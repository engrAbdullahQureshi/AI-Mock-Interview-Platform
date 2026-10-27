from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime, timezone
import logging

from app.database import get_database
from app.routers.auth import get_current_user
from app.services.ai_service import generate_interview_questions, score_interview
from app.models.session import MessageRole
from app.models.interview import (
    InterviewCreateRequest,
    InterviewResponse,
    InterviewListResponse,
    InterviewListWrapper,
    InterviewStatus,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ========== HELPER ==========

def _interview_to_response(doc: dict) -> InterviewResponse:
    """Converts a raw MongoDB document → InterviewResponse."""
    return InterviewResponse(
        id=str(doc["_id"]),
        user_id=str(doc["user_id"]),
        resume_id=str(doc["resume_id"]),
        title=doc["title"],
        job_title=doc["job_title"],
        questions=doc.get("questions", []),
        status=doc["status"],
        created_at=doc["created_at"],
        completed_at=doc.get("completed_at"),
    )


def _interview_to_list_response(doc: dict) -> InterviewListResponse:
    """Lightweight version for list endpoint — no questions array."""
    return InterviewListResponse(
        id=str(doc["_id"]),
        title=doc["title"],
        job_title=doc["job_title"],
        status=doc["status"],
        created_at=doc["created_at"],
        completed_at=doc.get("completed_at"),
        question_count=doc.get("question_count", 0),
    )


# ========== CREATE INTERVIEW ==========

@router.post(
    "/",
    response_model=InterviewResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new mock interview",
    description=(
        "Fetches the resume, calls Groq AI to generate personalised questions, "
        "and saves the interview to MongoDB."
    ),
)
async def create_interview(
    payload: InterviewCreateRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    user_id = str(current_user["_id"])

    # ── 1. Validate resume_id ──────────────────────────────────────────────
    try:
        resume_oid = ObjectId(payload.resume_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid resume_id format.",
        )

    # ── 2. Fetch resume from DB (must belong to current user) ──────────────
    resume_doc = await db.resumes.find_one(
        {"_id": resume_oid, "user_id": user_id}
    )
    if not resume_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found or does not belong to you.",
        )

    parsed_data = resume_doc.get("parsed_data")
    if not parsed_data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Resume has no parsed data. Please re-upload and try again.",
        )

    # ── 3. Generate questions via Groq AI ──────────────────────────────────
    logger.info(
        f"Generating {payload.num_questions} questions for user={user_id} "
        f"job='{payload.job_title}'"
    )
    questions = await generate_interview_questions(
        parsed_resume=parsed_data,
        job_title=payload.job_title,
        num_questions=payload.num_questions,
        job_description=payload.job_description,
        focus_skills=payload.focus_skills,
    )

    if not questions:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service failed to generate questions. Please try again.",
        )

    # ── 4. Build & save interview document ────────────────────────────────
    title = f"{payload.job_title} Interview"
    now   = datetime.now(timezone.utc)

    interview_doc = {
        "user_id":        user_id,
        "resume_id":      payload.resume_id,
        "title":          title,
        "job_title":      payload.job_title,
        "job_description": payload.job_description,
        "questions":      questions,
        "question_count": len(questions),
        "status":         InterviewStatus.active,
        "created_at":     now,
        "completed_at":   None,
    }

    result = await db.interviews.insert_one(interview_doc)
    interview_doc["_id"] = result.inserted_id

    logger.info(f"Interview created: {result.inserted_id} for user={user_id}")
    return _interview_to_response(interview_doc)


# ========== LIST INTERVIEWS ==========

@router.get(
    "/",
    response_model=InterviewListWrapper,
    summary="List all interviews for current user",
)
async def list_interviews(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    user_id = str(current_user["_id"])

    cursor = (
        db.interviews.find({"user_id": user_id})
        .sort("created_at", -1)   # newest first
    )
    docs = await cursor.to_list(length=100)

    interviews = [_interview_to_list_response(doc) for doc in docs]
    return InterviewListWrapper(interviews=interviews, total=len(interviews))


# ========== GET SINGLE INTERVIEW ==========

@router.get(
    "/{interview_id}",
    response_model=InterviewResponse,
    summary="Get a single interview with all questions",
)
async def get_interview(
    interview_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    user_id = str(current_user["_id"])

    try:
        oid = ObjectId(interview_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid interview_id format.",
        )

    doc = await db.interviews.find_one({"_id": oid, "user_id": user_id})
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview not found or does not belong to you.",
        )

    return _interview_to_response(doc)


# ========== COMPLETE INTERVIEW ==========

@router.put(
    "/{interview_id}/complete",
    response_model=InterviewResponse,
    summary="Mark an interview as completed",
)
async def complete_interview(
    interview_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    user_id = str(current_user["_id"])

    try:
        oid = ObjectId(interview_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid interview_id format.",
        )

    now = datetime.now(timezone.utc)

    result = await db.interviews.find_one_and_update(
        {"_id": oid, "user_id": user_id},
        {"$set": {"status": InterviewStatus.completed, "completed_at": now}},
        return_document=True,   # return updated doc
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview not found or does not belong to you.",
        )

    logger.info(f"Interview {interview_id} marked as completed by user={user_id}")
    return _interview_to_response(result)


# ========== DELETE INTERVIEW ==========

@router.delete(
    "/{interview_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an interview",
)
async def delete_interview(
    interview_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    user_id = str(current_user["_id"])

    try:
        oid = ObjectId(interview_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid interview_id format.",
        )

    result = await db.interviews.delete_one({"_id": oid, "user_id": user_id})

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview not found or does not belong to you.",
        )

    logger.info(f"Interview {interview_id} deleted by user={user_id}")
    # 204 returns no body


# ========== INTERVIEW REPORT (scoring) ==========

_DIMS = ["relevance", "technical_depth", "communication", "specificity", "jd_alignment"]


def _clamp_score(v) -> int:
    try:
        return max(0, min(100, int(round(float(v)))))
    except Exception:
        return 0


@router.get(
    "/{interview_id}/report",
    summary="Scored analytics report for a completed interview",
    description=(
        "Scores the saved transcript across 5 dimensions with one Groq call. "
        "The model judges each answer; Python aggregates the overall numbers so "
        "they are deterministic and reproducible. Cached on first computation."
    ),
)
async def interview_report(
    interview_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    user_id = str(current_user["_id"])

    try:
        oid = ObjectId(interview_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid interview_id format.",
        )

    interview = await db.interviews.find_one({"_id": oid, "user_id": user_id})
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview not found or does not belong to you.",
        )

    if interview.get("status") != InterviewStatus.completed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Interview not completed.",
        )

    # Return cached report if we already scored this interview.
    if interview.get("report"):
        return interview["report"]

    questions = interview.get("questions", [])

    # Grab the most recent session's transcript for this interview.
    sessions = (
        await db.sessions.find({"interview_id": interview_id})
        .sort("started_at", -1)
        .to_list(length=1)
    )
    messages = sessions[0].get("messages", []) if sessions else []
    answers = [m.get("content", "") for m in messages if m.get("role") == MessageRole.user]

    # Pair each question with the candidate's answer in order.
    qa_pairs = []
    for i, q in enumerate(questions):
        qa_pairs.append({
            "index": i + 1,
            "question": q,
            "answer": answers[i] if i < len(answers) else "(no answer given)",
        })

    scored = await score_interview(
        job_title=interview.get("job_title", "the role"),
        job_description=interview.get("job_description"),
        parsed_resume=await _fetch_parsed_resume(db, interview, user_id),
        qa_pairs=qa_pairs,
    )
    if scored is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service is unavailable. Check the GROQ_API_KEY and try again.",
        )

    # ----- Aggregate in Python (deterministic, reproducible) -----
    model_pq = {int(p.get("index", idx + 1)): p
                for idx, p in enumerate(scored.get("per_question", []))}

    per_question = []
    dim_totals = {d: [] for d in _DIMS}
    for pair in qa_pairs:
        idx = pair["index"]
        raw = model_pq.get(idx, {})
        raw_scores = raw.get("scores", {}) or {}
        scores = {d: _clamp_score(raw_scores.get(d, 0)) for d in _DIMS}
        for d in _DIMS:
            dim_totals[d].append(scores[d])
        per_question.append({
            "index": idx,
            "question": pair["question"],
            "answer": pair["answer"],
            "scores": scores,
            "feedback": str(raw.get("feedback", "")).strip(),
        })

    def _mean(nums):
        return int(round(sum(nums) / len(nums))) if nums else 0

    dimensions = {d: _mean(dim_totals[d]) for d in _DIMS}
    overall_score = _mean(list(dimensions.values()))

    completed_at = interview.get("completed_at")
    report = {
        "interview_id": interview_id,
        "job_title": interview.get("job_title"),
        "completed_at": completed_at.isoformat() if hasattr(completed_at, "isoformat") else completed_at,
        "overall_score": overall_score,
        "verdict": str(scored.get("verdict", "")).strip(),
        "dimensions": dimensions,
        "strengths": list(scored.get("strengths", []))[:5],
        "improvements": list(scored.get("improvements", []))[:5],
        "jd_gap_recap": str(scored.get("jd_gap_recap", "")).strip(),
        "per_question": per_question,
    }

    # Cache so re-opening the report is instant.
    await db.interviews.update_one({"_id": oid}, {"$set": {"report": report}})
    logger.info(f"Report computed for interview {interview_id} — overall={overall_score}")
    return report


async def _fetch_parsed_resume(db, interview: dict, user_id: str) -> dict:
    """Best-effort fetch of the resume's parsed data for scoring context."""
    try:
        resume = await db.resumes.find_one(
            {"_id": ObjectId(interview["resume_id"]), "user_id": user_id}
        )
        return (resume or {}).get("parsed_data") or {}
    except Exception:
        return {}