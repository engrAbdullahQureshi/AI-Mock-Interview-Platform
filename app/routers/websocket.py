"""
Phase 5 — WebSocket Real-time Interview Chat
============================================

ENDPOINT:
    WS /api/v1/ws/chat/{interview_id}?token=<access_token>

FLOW:
    1. Client connects with JWT token as query param
    2. Server validates token + fetches interview from MongoDB
    3. Server creates a session document in MongoDB
    4. AI sends a greeting + Question 1
    5. Client sends answer (plain text)
    6. AI gives brief feedback + asks next question
    7. Repeats until all questions exhausted
    8. AI sends a closing summary
    9. Session saved, interview marked completed, connection closed

MESSAGE PROTOCOL (JSON both directions):
    Server → Client:
        { "type": "ai",       "content": "...", "question_index": 0 }
        { "type": "info",     "content": "..." }          ← system messages
        { "type": "complete", "content": "...", "session_id": "..." }

    Client → Server:
        plain text string  (the user's answer)
"""

import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from bson import ObjectId
from groq import Groq

from app.config import settings
from app.database import DatabaseManager
from app.services.auth import verify_access_token   # re-use existing JWT verifier
from app.models.session import MessageRole, SessionStatus

logger = logging.getLogger(__name__)
router = APIRouter()

# ── Groq client (reuse pattern from ai_service.py) ────────────────────────
_groq_client = None
if settings.GROQ_API_KEY:
    _groq_client = Groq(api_key=settings.GROQ_API_KEY)


# ==========================================================================
# HELPERS
# ==========================================================================

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _msg(role: MessageRole, content: str) -> dict:
    """Build a chat message dict ready for MongoDB."""
    return {
        "role":      role,
        "content":   content,
        "timestamp": _now(),
    }


async def _authenticate_ws(token: str | None) -> dict | None:
    """
    Validate JWT token passed as query param.
    Returns the user document from MongoDB, or None on failure.
    """
    if not token:
        return None
    try:
        payload = verify_access_token(token)
        if not payload:
            return None

        user_id = payload.get("sub")
        db = DatabaseManager.get_db()
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        return user
    except Exception as e:
        logger.warning(f"WebSocket auth failed: {e}")
        return None


def _build_system_prompt(interview: dict, candidate_name: str) -> str:
    """
    System prompt that gives the AI its interviewer persona and
    the full list of questions to work through.
    """
    questions_text = "\n".join(
        f"{i+1}. {q}" for i, q in enumerate(interview["questions"])
    )
    return f"""You are a professional, friendly technical interviewer conducting a mock interview.

Candidate name: {candidate_name}
Role they are practising for: {interview['job_title']}

Your question list (ask them IN ORDER, one at a time):
{questions_text}

RULES:
- After the candidate answers, give 2-3 sentences of constructive, encouraging feedback on their answer.
- Then immediately ask the next question.
- When all questions are done, give a warm 3-5 sentence overall summary of their performance and wish them luck.
- Keep a professional but encouraging tone throughout.
- Do NOT skip questions or ask questions out of order.
- Do NOT reveal the full question list to the candidate.
- Keep each response under 150 words.
"""


def _call_groq(system_prompt: str, messages: list) -> str:
    """
    Synchronous Groq call.
    `messages` is a list of {role, content} dicts (OpenAI-compatible format).
    """
    if not _groq_client:
        return "AI service is not configured. Please check GROQ_API_KEY."

    import time
    delay = 2.0
    for attempt in range(3):
        try:
            response = _groq_client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=[{"role": "system", "content": system_prompt}] + messages,
                temperature=0.7,
                max_tokens=300,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            s = str(e).lower()
            transient = any(t in s for t in (
                "429", "rate limit", "rate_limit", "503", "overload", "timeout", "timed out",
            ))
            if transient and attempt < 2:
                logger.warning(f"Groq WS transient error (attempt {attempt + 1}/3); retrying in {delay:.0f}s")
                time.sleep(delay)
                delay *= 2
                continue
            logger.error(f"Groq WebSocket call failed: {e}")
            return "I encountered an issue. Please repeat your answer."


# ==========================================================================
# WEBSOCKET ENDPOINT
# ==========================================================================

@router.websocket("/chat/{interview_id}")
async def interview_chat(
    websocket: WebSocket,
    interview_id: str,
    token: str | None = None,          # passed as ?token=<jwt>
):
    """
    Real-time interview chat over WebSocket.
    Connect with: ws://localhost:8000/api/v1/ws/chat/{interview_id}?token=<jwt>
    """

    # ── 1. Authenticate ────────────────────────────────────────────────────
    user = await _authenticate_ws(token)
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        logger.warning(f"WebSocket rejected — invalid token for interview {interview_id}")
        return

    await websocket.accept()
    user_id   = str(user["_id"])
    candidate = user.get("full_name") or user.get("name") or "Candidate"

    db = DatabaseManager.get_db()

    # ── 2. Fetch interview ─────────────────────────────────────────────────
    try:
        interview_oid = ObjectId(interview_id)
    except Exception:
        await websocket.send_json({"type": "error", "content": "Invalid interview ID."})
        await websocket.close()
        return

    interview = await db.interviews.find_one(
        {"_id": interview_oid, "user_id": user_id}
    )
    if not interview:
        await websocket.send_json({"type": "error", "content": "Interview not found."})
        await websocket.close()
        return

    questions = interview.get("questions", [])
    if not questions:
        await websocket.send_json({"type": "error", "content": "This interview has no questions."})
        await websocket.close()
        return

    # ── 3. Create session in MongoDB ───────────────────────────────────────
    session_doc = {
        "interview_id":           interview_id,
        "user_id":                user_id,
        "messages":               [],
        "status":                 SessionStatus.active,
        "current_question_index": 0,
        "started_at":             _now(),
        "ended_at":               None,
    }
    session_result = await db.sessions.insert_one(session_doc)
    session_id     = str(session_result.inserted_id)

    logger.info(f"Session {session_id} started — user={user_id} interview={interview_id}")

    # ── 4. Build AI system prompt + conversation history ──────────────────
    system_prompt    = _build_system_prompt(interview, candidate)
    groq_history: list[dict] = []   # OpenAI-format messages sent to Groq
    saved_messages:  list[dict] = []  # Raw dicts saved to MongoDB

    # ── 5. Send greeting + Question 1 ─────────────────────────────────────
    greeting_prompt = (
        f"Greet {candidate} warmly, introduce yourself as their interviewer for the "
        f"{interview['job_title']} role, and ask the FIRST question from your list."
    )
    groq_history.append({"role": "user", "content": greeting_prompt})
    opening = _call_groq(system_prompt, groq_history)
    groq_history.append({"role": "assistant", "content": opening})

    saved_messages.append(_msg(MessageRole.ai, opening))
    await websocket.send_json({
        "type":             "ai",
        "content":          opening,
        "question_index":   0,
        "total_questions":  len(questions),
    })

    current_q_index = 0   # tracks which question we're on

    # ── 6. Main chat loop ──────────────────────────────────────────────────
    try:
        while True:
            # Receive user's answer
            try:
                raw = await websocket.receive_text()
            except WebSocketDisconnect:
                logger.info(f"Session {session_id} — client disconnected mid-interview")
                break

            user_answer = raw.strip()
            if not user_answer:
                continue   # ignore empty messages

            # Save user message
            saved_messages.append(_msg(MessageRole.user, user_answer))
            groq_history.append({"role": "user", "content": user_answer})

            current_q_index += 1   # we just answered question at current_q_index

            # Determine if more questions remain
            questions_done = current_q_index >= len(questions)

            if questions_done:
                # Ask Groq for closing summary
                groq_history.append({
                    "role": "user",
                    "content": (
                        "That was the last answer. Please give a warm overall performance "
                        "summary and wish the candidate luck."
                    )
                })
                closing = _call_groq(system_prompt, groq_history)
                groq_history.append({"role": "assistant", "content": closing})
                saved_messages.append(_msg(MessageRole.ai, closing))

                # Send final message
                await websocket.send_json({
                    "type":       "complete",
                    "content":    closing,
                    "session_id": session_id,
                })

                # Save session + mark interview completed
                now = _now()
                await db.sessions.update_one(
                    {"_id": session_result.inserted_id},
                    {"$set": {
                        "messages":               saved_messages,
                        "status":                 SessionStatus.completed,
                        "current_question_index": current_q_index,
                        "ended_at":               now,
                    }}
                )
                await db.interviews.update_one(
                    {"_id": interview_oid},
                    {"$set": {"status": "completed", "completed_at": now}}
                )

                logger.info(f"Session {session_id} completed — {current_q_index} questions answered")
                await websocket.close()
                break

            else:
                # Ask Groq for feedback + next question
                next_q_number = current_q_index + 1   # human-readable
                groq_history.append({
                    "role": "user",
                    "content": (
                        f"Give feedback on that answer, then ask question {next_q_number} "
                        f"from your list."
                    )
                })
                ai_reply = _call_groq(system_prompt, groq_history)
                groq_history.append({"role": "assistant", "content": ai_reply})
                saved_messages.append(_msg(MessageRole.ai, ai_reply))

                # Persist progress after every exchange
                await db.sessions.update_one(
                    {"_id": session_result.inserted_id},
                    {"$set": {
                        "messages":               saved_messages,
                        "current_question_index": current_q_index,
                    }}
                )

                await websocket.send_json({
                    "type":            "ai",
                    "content":         ai_reply,
                    "question_index":  current_q_index,
                    "total_questions": len(questions),
                })

    except WebSocketDisconnect:
        logger.info(f"Session {session_id} — WebSocket disconnected")

    except Exception as e:
        logger.error(f"Session {session_id} — unexpected error: {e}", exc_info=True)
        try:
            await websocket.send_json({"type": "error", "content": "An unexpected error occurred."})
            await websocket.close()
        except Exception:
            pass

    finally:
        # Always save whatever messages we have if session not already completed
        try:
            existing = await db.sessions.find_one({"_id": session_result.inserted_id})
            if existing and existing.get("status") != SessionStatus.completed:
                await db.sessions.update_one(
                    {"_id": session_result.inserted_id},
                    {"$set": {
                        "messages":               saved_messages,
                        "current_question_index": current_q_index,
                        "ended_at":               _now(),
                    }}
                )
        except Exception as e:
            logger.error(f"Could not save session on cleanup: {e}")