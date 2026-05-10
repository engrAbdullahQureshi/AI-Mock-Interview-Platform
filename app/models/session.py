from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ========== ENUMS ==========

class MessageRole(str, Enum):
    ai   = "ai"
    user = "user"


class SessionStatus(str, Enum):
    active    = "active"
    completed = "completed"


# ========== MESSAGE ==========

class ChatMessage(BaseModel):
    """A single message in the interview conversation."""
    role:      MessageRole
    content:   str
    timestamp: datetime


# ========== SESSION RESPONSE ==========

class SessionResponse(BaseModel):
    """Full session document returned to client."""
    id:              str
    interview_id:    str
    user_id:         str
    messages:        List[ChatMessage]
    status:          SessionStatus
    current_question_index: int
    started_at:      datetime
    ended_at:        Optional[datetime] = None


class SessionListResponse(BaseModel):
    """Lightweight session summary for list views."""
    id:           str
    interview_id: str
    status:       SessionStatus
    message_count: int
    started_at:   datetime
    ended_at:     Optional[datetime] = None