from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ========== STRUCTURED RESUME DATA ==========
# This is what Gemini extracts from the raw resume text

class WorkExperience(BaseModel):
    company: Optional[str] = None
    position: Optional[str] = None
    duration: Optional[str] = None
    description: Optional[str] = None


class Education(BaseModel):
    institution: Optional[str] = None
    degree: Optional[str] = None
    field: Optional[str] = None
    year: Optional[str] = None


class ParsedResumeData(BaseModel):
    """
    Structured data extracted by Gemini AI from raw resume text.
    All fields are optional since resume formats vary widely.
    """
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    summary: Optional[str] = None
    skills: List[str] = []
    work_experience: List[WorkExperience] = []
    education: List[Education] = []
    certifications: List[str] = []
    languages: List[str] = []


# ========== RESPONSE MODELS ==========

class ResumeResponse(BaseModel):
    """Returned to client after upload or fetch."""
    id: str
    user_id: str
    file_name: str
    file_size: int
    uploaded_at: datetime
    raw_text: Optional[str] = None     # Full extracted text
    parsed_data: Optional[ParsedResumeData] = None  # Gemini structured output

    class Config:
        json_schema_extra = {
            "example": {
                "id": "64f1a2b3c4d5e6f7a8b9c0d1",
                "user_id": "64f1a2b3c4d5e6f7a8b9c0d0",
                "file_name": "john_doe_resume.pdf",
                "file_size": 102400,
                "uploaded_at": "2024-01-15T10:30:00",
                "parsed_data": {
                    "full_name": "John Doe",
                    "skills": ["Python", "FastAPI", "MongoDB"]
                }
            }
        }


class ResumeListResponse(BaseModel):
    """Returned when listing all resumes for a user."""
    resumes: List[ResumeResponse]
    total: int


class MessageResponse(BaseModel):
    message: str
    success: bool = True


# ========== DATABASE MODEL ==========

class ResumeInDB(BaseModel):
    """Full resume document as stored in MongoDB."""
    user_id: str
    file_name: str
    file_path: str
    file_size: int
    content_type: str
    raw_text: Optional[str] = None
    parsed_data: Optional[dict] = None
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)