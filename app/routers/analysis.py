"""
Resume ↔ Job Description gap analysis.

POST /api/v1/analysis/gap
    body: { "resume_id": str, "job_description": str }
    returns: { match_score, verdict, matched_skills[], missing_skills[],
               summary, resume_id }

The frontend passes matched_skills + missing_skills + job_description into
interview creation so questions target the real gaps.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from bson import ObjectId

from app.database import get_database
from app.routers.auth import get_current_user
from app.services.ai_service import analyze_gap

logger = logging.getLogger(__name__)
router = APIRouter()


class GapAnalysisRequest(BaseModel):
    resume_id: str = Field(..., example="6a007ad779c224ad10bae78d")
    job_description: str = Field(..., min_length=20, max_length=8000)


class GapAnalysisResponse(BaseModel):
    match_score: int
    verdict: str
    matched_skills: List[str]
    missing_skills: List[str]
    summary: str
    resume_id: str


@router.post(
    "/gap",
    response_model=GapAnalysisResponse,
    summary="Analyze how well a resume fits a job description",
)
async def gap_analysis(
    payload: GapAnalysisRequest,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_database),
):
    user_id = str(current_user["_id"])

    # Validate + fetch the resume (must belong to the current user)
    try:
        resume_oid = ObjectId(payload.resume_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid resume_id format.",
        )

    resume_doc = await db.resumes.find_one({"_id": resume_oid, "user_id": user_id})
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

    result = await analyze_gap(parsed_data, payload.job_description)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service is unavailable. Check the GROQ_API_KEY and try again.",
        )

    result["resume_id"] = payload.resume_id
    return GapAnalysisResponse(**result)
