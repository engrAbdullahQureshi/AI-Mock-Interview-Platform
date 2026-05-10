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

    MODEL: llama-3.3-70b-versatile — fast, free, excellent at JSON extraction

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
        response = _groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
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
    num_questions: int = 10
) -> Optional[list]:
    """
    Generates personalized interview questions based on resume + target job.
    Used in Phase 4 (Interview Management).

    RETURNS: list of question strings, or None on failure
    """

    if not _groq_client:
        logger.warning("Groq not configured - skipping question generation")
        return None

    resume_summary = json.dumps(parsed_resume, indent=2)[:3000]

    prompt = f"""You are an expert technical interviewer. Generate {num_questions} interview questions for a candidate applying for the role of: {job_title}

Based on their resume:
{resume_summary}

RULES:
- Return ONLY a JSON array of question strings, nothing else
- Mix technical, behavioral, and situational questions
- Make questions specific to their actual experience
- Include questions about skills relevant to the target role
- No numbering, just the question text

Example format:
["Question 1?", "Question 2?", "Question 3?"]"""

    try:
        response = _groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
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