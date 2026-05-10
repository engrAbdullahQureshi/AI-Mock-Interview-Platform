from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime, timezone
import logging

from app.database import get_database
from app.routers.auth import get_current_user
from app.services.ai_service import generate_interview_questions
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