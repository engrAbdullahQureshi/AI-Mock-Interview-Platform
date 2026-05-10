from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ========== ENUMS ==========

class InterviewStatus(str, Enum):
    active    = "active"
    completed = "completed"
    paused    = "paused"


# ========== REQUEST MODELS ==========

class InterviewCreateRequest(BaseModel):
    """
    Body sent by client to create a new interview.
    resume_id  → MongoDB _id of an already-uploaded resume
    job_title  → role the user is practising for
    num_questions → how many questions to generate (default 10, max 20)
    """
    resume_id:     str = Field(..., example="6a007ad779c224ad10bae78d")
    job_title:     str = Field(..., min_length=2, max_length=100,
                               example="Full Stack Engineer")
    num_questions: int = Field(default=10, ge=1, le=20)


# ========== RESPONSE MODELS ==========

class InterviewResponse(BaseModel):
    """
    Returned to client after creating or fetching an interview.
    Mirrors the MongoDB document shape (with _id → id).
    """
    id:           str
    user_id:      str
    resume_id:    str
    title:        str                   # e.g. "Full Stack Engineer Interview"
    job_title:    str
    questions:    List[str]
    status:       InterviewStatus
    created_at:   datetime
    completed_at: Optional[datetime] = None

    class Config:
        # Allow population from MongoDB dicts that use _id
        populate_by_name = True


class InterviewListResponse(BaseModel):
    """
    Lightweight version used in the list endpoint (no questions array).
    Keeps the list response small and fast.
    """
    id:           str
    title:        str
    job_title:    str
    status:       InterviewStatus
    created_at:   datetime
    completed_at: Optional[datetime] = None
    question_count: int               # len(questions) stored at save time


class InterviewListWrapper(BaseModel):
    """Envelope for GET /interviews list."""
    interviews: List[InterviewListResponse]
    total:      int