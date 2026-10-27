import asyncio
import json
import logging
from typing import Optional
from groq import Groq
from app.config import settings

logger = logging.getLogger(__name__)

# ========== CONFIGURE GROQ ==========
# Initialize client once at module load — reused across all requests
_groq_client: Optional[Groq] = None

if settings.GROQ_API_KEY:
    _groq_client = Groq(api_key=settings.GROQ_API_KEY)
    logger.info("Groq AI configured successfully")
else:
    logger.warning("GROQ_API_KEY not set - AI features will be disabled")


async def _groq_create(**kwargs):
    """
    Wrapper around the Groq chat API that retries transient errors
    (rate limits / overload / timeouts) with exponential backoff. This keeps
    the demo resilient when calls arrive back-to-back on the free tier.
    """
    delay = 2.0
    last_exc = None
    for attempt in range(3):
        try:
            return _groq_client.chat.completions.create(**kwargs)
        except Exception as e:
            last_exc = e
            s = str(e).lower()
            transient = any(t in s for t in (
                "429", "rate limit", "rate_limit", "503", "overload",
                "timeout", "timed out", "temporarily",
            ))
            if transient and attempt < 2:
                logger.warning(
                    f"Groq transient error (attempt {attempt + 1}/3); retrying in {delay:.0f}s"
                )
                await asyncio.sleep(delay)
                delay *= 2
                continue
            raise
    raise last_exc


def _clean_json_response(raw: str) -> str:
    """
    Strips markdown fences if the model wraps JSON in ```json ... ```
    despite instructions not to.
    """
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1]).strip()
    return raw


async def parse_resume_with_ai(raw_text: str) -> Optional[dict]:
    """
    Sends raw resume text to Groq and gets back structured JSON data.

    MODEL: configurable via settings.GROQ_MODEL (Groq)

    RETURNS:
    - dict with structured data if successful
    - None if Groq fails or is not configured

    NOTE: Returns None instead of raising so resume upload still succeeds
    even if AI parsing fails. File and raw_text are always saved.
    """

    if not _groq_client:
        logger.warning("Groq not configured - skipping AI parsing")
        return None

    # Truncate very long resumes to stay within token limits
    truncated_text = raw_text[:8000] if len(raw_text) > 8000 else raw_text

    prompt = f"""You are a professional resume parser. Extract structured information from the resume text below.

IMPORTANT RULES:
- Return ONLY valid JSON, no markdown, no backticks, no explanation
- If a field is not found, use null for strings or [] for arrays
- For skills, extract ALL technical and soft skills mentioned
- For work_experience, list jobs from most recent to oldest
- Keep descriptions concise (max 2 sentences)

Return this exact JSON structure:
{{
    "full_name": "string or null",
    "email": "string or null",
    "phone": "string or null",
    "location": "string or null",
    "summary": "string or null",
    "skills": ["skill1", "skill2"],
    "work_experience": [
        {{
            "company": "string or null",
            "position": "string or null",
            "duration": "string or null",
            "description": "string or null"
        }}
    ],
    "education": [
        {{
            "institution": "string or null",
            "degree": "string or null",
            "field": "string or null",
            "year": "string or null"
        }}
    ],
    "certifications": ["cert1", "cert2"],
    "languages": ["language1", "language2"]
}}

RESUME TEXT:
{truncated_text}"""

    try:
        response = await _groq_create(
            model=settings.GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a resume parser that returns only valid JSON. No markdown, no explanation, just JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1,
            max_tokens=2048,
        )

        raw_response = response.choices[0].message.content
        cleaned = _clean_json_response(raw_response)
        parsed = json.loads(cleaned)

        logger.info("Resume parsed successfully by Groq AI")
        return parsed

    except json.JSONDecodeError as e:
        logger.error(f"Groq returned invalid JSON: {e}")
        return None
    except Exception as e:
        logger.error(f"Groq AI parsing failed: {type(e).__name__}: {e}")
        return None


async def generate_interview_questions(
    parsed_resume: dict,
    job_title: str,
    num_questions: int = 10,
    job_description: Optional[str] = None,
    focus_skills: Optional[list] = None,
) -> Optional[list]:
    """
    Generates personalized interview questions based on resume + target job.
    When a job_description and/or focus_skills (gaps) are provided, the questions
    deliberately probe those gaps — mirroring "re-check against the facts".

    RETURNS: list of question strings, or None on failure
    """

    if not _groq_client:
        logger.warning("Groq not configured - skipping question generation")
        return None

    resume_summary = json.dumps(parsed_resume, indent=2)[:3000]

    jd_block = ""
    if job_description:
        jd_block = f"\nTarget job description:\n{job_description[:2500]}\n"

    focus_block = ""
    if focus_skills:
        focus_block = (
            "\nThe candidate's resume shows GAPS in these areas vs the job — make "
            "sure at least a third of the questions probe them directly (fairly, "
            "to see how the candidate reasons about what they don't yet know):\n- "
            + "\n- ".join(str(s) for s in focus_skills[:8])
            + "\n"
        )

    prompt = f"""You are an expert technical interviewer. Generate {num_questions} interview questions for a candidate applying for the role of: {job_title}

Based on their resume:
{resume_summary}
{jd_block}{focus_block}
RULES:
- Return ONLY a JSON array of question strings, nothing else
- Mix technical, behavioral, and situational questions
- Make questions specific to their actual experience AND the target role
- No numbering, just the question text

Example format:
["Question 1?", "Question 2?", "Question 3?"]"""

    try:
        response = await _groq_create(
            model=settings.GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert interviewer that returns only a JSON array of questions. No markdown, no explanation."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=2048,
        )

        raw_response = response.choices[0].message.content
        cleaned = _clean_json_response(raw_response)
        questions = json.loads(cleaned)

        logger.info(f"Generated {len(questions)} interview questions")
        return questions

    except Exception as e:
        logger.error(f"Question generation failed: {type(e).__name__}: {e}")
        return None


async def analyze_gap(parsed_resume: dict, job_description: str) -> Optional[dict]:
    """
    Compare a structured resume against a job description and return an honest
    fit assessment. See BLUEPRINT.md §5a.

    RETURNS a dict:
      { match_score:int, verdict:str, matched_skills:[str],
        missing_skills:[str], summary:str }
    or None on failure.
    """
    if not _groq_client:
        logger.warning("Groq not configured - skipping gap analysis")
        return None

    resume_summary = json.dumps(parsed_resume, indent=2)[:3500]

    prompt = f"""Compare this candidate's resume to the job description and assess fit HONESTLY. Do not inflate.

CANDIDATE RESUME (structured):
{resume_summary}

JOB DESCRIPTION:
{job_description[:3500]}

Compute match_score (0-100) as a weighted blend:
- core skill overlap: 45%
- domain / role relevance: 25%
- seniority fit: 20%
- breadth: 10%

Return ONLY valid JSON, no markdown, with EXACTLY this shape:
{{
  "match_score": 0-100 integer,
  "verdict": "at most 8 words",
  "matched_skills": ["skills/experience the JD asks for that ARE evidenced (max 10)"],
  "missing_skills": ["JD requirements NOT evidenced in the resume (max 6)"],
  "summary": "3-4 sentences, specific and honest about gaps"
}}"""

    try:
        response = await _groq_create(
            model=settings.GROQ_MODEL,
            messages=[
                {"role": "system", "content": "You are a precise, fair technical recruiter. Return ONLY valid JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=1200,
        )
        data = json.loads(_clean_json_response(response.choices[0].message.content))

        # Clamp / sanitise
        data["match_score"] = max(0, min(100, int(round(float(data.get("match_score", 0))))))
        data["matched_skills"] = list(data.get("matched_skills", []))[:10]
        data["missing_skills"] = list(data.get("missing_skills", []))[:6]
        data["verdict"] = str(data.get("verdict", "")).strip()
        data["summary"] = str(data.get("summary", "")).strip()
        logger.info(f"Gap analysis done — match_score={data['match_score']}")
        return data
    except Exception as e:
        logger.error(f"Gap analysis failed: {type(e).__name__}: {e}")
        return None


async def score_interview(
    job_title: str,
    job_description: Optional[str],
    parsed_resume: dict,
    qa_pairs: list,
) -> Optional[dict]:
    """
    Score an interview transcript. The MODEL returns per-question dimension
    scores + qualitative notes; the CALLER aggregates the overall numbers in
    Python (deterministic, reproducible). See BLUEPRINT.md §5b.

    qa_pairs: [{"index":1, "question":"...", "answer":"..."}]
    RETURNS a dict:
      { per_question:[{index,question,answer,scores{relevance,technical_depth,
        communication,specificity,jd_alignment}, feedback}],
        strengths:[str], improvements:[str], verdict:str, jd_gap_recap:str }
    or None on failure.
    """
    if not _groq_client:
        logger.warning("Groq not configured - skipping interview scoring")
        return None

    resume_summary = json.dumps(parsed_resume, indent=2)[:2500]
    transcript = json.dumps(qa_pairs, indent=2)[:6000]
    jd_line = f"\nJOB DESCRIPTION:\n{job_description[:2000]}\n" if job_description else ""

    prompt = f"""Score this mock interview fairly and rigorously. Judge each answer ONLY on what was actually said. Ground every judgement in the candidate's resume facts and the job's requirements.

ROLE: {job_title}
{jd_line}
CANDIDATE FACTS (resume):
{resume_summary}

TRANSCRIPT (questions and the candidate's answers):
{transcript}

For EACH question, score these 5 dimensions 0-100:
- relevance: did the answer address the question?
- technical_depth: correctness + depth of technical reasoning
- communication: clarity, structure, conciseness
- specificity: concrete examples/metrics vs vague claims
- jd_alignment: does it evidence what THIS job needs?

Return ONLY valid JSON, no markdown, with EXACTLY this shape:
{{
  "per_question": [
    {{"index": 1, "scores": {{"relevance":0,"technical_depth":0,"communication":0,"specificity":0,"jd_alignment":0}}, "feedback": "one specific sentence"}}
  ],
  "strengths": ["3 bullets, each referencing a real answer"],
  "improvements": ["3 bullets, each actionable and specific"],
  "verdict": "one sentence overall",
  "jd_gap_recap": "one sentence on how the candidate handled the JD gap areas"
}}"""

    try:
        response = await _groq_create(
            model=settings.GROQ_MODEL,
            messages=[
                {"role": "system", "content": "You are a fair, rigorous interview assessor. Return ONLY valid JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=2500,
        )
        data = json.loads(_clean_json_response(response.choices[0].message.content))
        logger.info("Interview scored by Groq AI")
        return data
    except Exception as e:
        logger.error(f"Interview scoring failed: {type(e).__name__}: {e}")
        return None