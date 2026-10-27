import os
import uuid
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from app.database import get_database
from app.routers.auth import get_current_user
from app.models.resume import (
    ResumeResponse,
    ResumeListResponse,
    MessageResponse,
    ParsedResumeData,
    WorkExperience,
    Education,
)
from app.services.resume_parser import extract_text
from app.services.ai_service import parse_resume_with_ai
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# ========== HELPERS ==========

def build_resume_response(doc: dict) -> ResumeResponse:
    """
    Converts a raw MongoDB document into a ResumeResponse.
    Handles ObjectId → str conversion and optional parsed_data.
    """
    parsed_data = None
    if doc.get("parsed_data"):
        try:
            raw = doc["parsed_data"]

            # Convert nested dicts to Pydantic models
            work_exp = [
                WorkExperience(**w) for w in raw.get("work_experience", [])
            ]
            education = [
                Education(**e) for e in raw.get("education", [])
            ]

            parsed_data = ParsedResumeData(
                full_name=raw.get("full_name"),
                email=raw.get("email"),
                phone=raw.get("phone"),
                location=raw.get("location"),
                summary=raw.get("summary"),
                skills=raw.get("skills", []),
                work_experience=work_exp,
                education=education,
                certifications=raw.get("certifications", []),
                languages=raw.get("languages", []),
            )
        except Exception as e:
            logger.warning(f"Could not parse parsed_data for resume {doc['_id']}: {e}")

    return ResumeResponse(
        id=str(doc["_id"]),
        user_id=str(doc["user_id"]),
        file_name=doc["file_name"],
        file_size=doc["file_size"],
        uploaded_at=doc["uploaded_at"],
        raw_text=doc.get("raw_text"),
        parsed_data=parsed_data,
    )


# ========== ENDPOINTS ==========

@router.post(
    "/upload",
    response_model=ResumeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and parse a resume",
)
async def upload_resume(
    file: UploadFile = File(..., description="Resume file (PDF, DOCX, or TXT)"),
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Upload a resume file, extract text, and parse with Groq AI.

    FLOW:
    1. Validate file type and size
    2. Save file to ./uploads/ directory
    3. Extract raw text (PDF/DOCX/TXT)
    4. Send text to Groq for structured parsing
    5. Save everything to MongoDB
    6. Return structured resume data

    PROTECTED: Requires valid JWT access token.
    """

    # Step 1: Validate file extension
    filename = file.filename or "unknown"
    ext = os.path.splitext(filename)[1].lower()

    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type '{ext}' not allowed. Supported: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )

    # Step 2: Read file bytes and check size
    file_bytes = await file.read()
    file_size = len(file_bytes)

    if file_size > settings.MAX_UPLOAD_SIZE:
        max_mb = settings.MAX_UPLOAD_SIZE / (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size is {max_mb:.0f}MB."
        )

    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty."
        )

    # Step 3: Save file to disk with a unique name
    # Use UUID to avoid collisions if two users upload same filename
    unique_filename = f"{uuid.uuid4().hex}_{filename}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    with open(file_path, "wb") as f:
        f.write(file_bytes)

    logger.info(f"File saved: {file_path} ({file_size} bytes)")

    # Step 4: Extract raw text
    content_type = file.content_type or ""
    raw_text = await extract_text(file_bytes, content_type, filename)

    if not raw_text:
        logger.warning(f"Text extraction failed for {filename} — saving file without text")

    # Step 5: Parse with Groq AI (only if we have text)
    parsed_data = None
    if raw_text:
        logger.info("Sending resume to Groq for parsing...")
        parsed_data = await parse_resume_with_ai(raw_text)

    # Step 6: Save to MongoDB
    user_id = str(current_user["_id"])
    now = datetime.utcnow()

    resume_doc = {
        "user_id": user_id,
        "file_name": filename,
        "file_path": file_path,
        "file_size": file_size,
        "content_type": content_type,
        "raw_text": raw_text,
        "parsed_data": parsed_data,
        "uploaded_at": now,
    }

    result = await db.resumes.insert_one(resume_doc)
    resume_doc["_id"] = result.inserted_id

    logger.info(f"Resume saved to DB: {result.inserted_id} for user {user_id}")

    return build_resume_response(resume_doc)


@router.get(
    "",
    response_model=ResumeListResponse,
    summary="List all resumes for current user",
)
async def list_resumes(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Returns all resumes uploaded by the currently logged-in user.
    Most recent first.

    PROTECTED: Requires valid JWT access token.
    """
    user_id = str(current_user["_id"])

    # Find all resumes for this user, sorted by upload date descending
    cursor = db.resumes.find(
        {"user_id": user_id}
    ).sort("uploaded_at", -1)

    docs = await cursor.to_list(length=100)   # Max 100 resumes per user

    resumes = [build_resume_response(doc) for doc in docs]

    return ResumeListResponse(resumes=resumes, total=len(resumes))


@router.get(
    "/{resume_id}",
    response_model=ResumeResponse,
    summary="Get a single resume by ID",
)
async def get_resume(
    resume_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Returns full details for a single resume, including raw_text and parsed_data.

    PROTECTED: Users can only access their own resumes.
    """
    user_id = str(current_user["_id"])

    # Validate resume_id is a valid ObjectId
    try:
        oid = ObjectId(resume_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid resume ID format."
        )

    doc = await db.resumes.find_one({"_id": oid})

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found."
        )

    # Ensure this resume belongs to the requesting user
    if str(doc["user_id"]) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resume."
        )

    return build_resume_response(doc)


@router.delete(
    "/{resume_id}",
    response_model=MessageResponse,
    summary="Delete a resume",
)
async def delete_resume(
    resume_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Deletes a resume from MongoDB and removes the file from disk.

    PROTECTED: Users can only delete their own resumes.
    """
    user_id = str(current_user["_id"])

    try:
        oid = ObjectId(resume_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid resume ID format."
        )

    # Find resume first (need file_path to delete from disk)
    doc = await db.resumes.find_one({"_id": oid})

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found."
        )

    if str(doc["user_id"]) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this resume."
        )

    # Delete from MongoDB
    await db.resumes.delete_one({"_id": oid})

    # Delete file from disk (don't fail if file already missing)
    file_path = doc.get("file_path")
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
            logger.info(f"Deleted file from disk: {file_path}")
        except Exception as e:
            logger.warning(f"Could not delete file {file_path}: {e}")

    logger.info(f"Resume {resume_id} deleted by user {user_id}")

    return MessageResponse(message="Resume deleted successfully.", success=True)