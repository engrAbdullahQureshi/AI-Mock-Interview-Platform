# AI Mock Interview Platform

A fully functional AI-powered mock interview platform built as a backend REST API. Users upload their resumes, receive AI-generated interview questions tailored to their experience and target role, and conduct live real-time interview sessions with an AI interviewer over WebSocket.

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Framework | FastAPI (Python) | Async REST API + WebSocket |
| Database | MongoDB Atlas + Motor | Cloud NoSQL, async driver |
| AI Provider | Groq — llama-3.3-70b-versatile | Resume parsing, question generation, live interviewer |
| Authentication | JWT (python-jose) | Access + refresh token strategy |
| Password Security | bcrypt (passlib) | Password hashing |
| File Parsing | PyPDF2, python-docx | PDF and DOCX text extraction |
| Validation | Pydantic v2 | Request/response models, auto-validation |
| Server | Uvicorn (ASGI) | Async server with hot reload |
| Caching | Redis (optional) | Graceful fallback if unavailable |

---

## Project Structure

```
AI-MOCK-INTERVIEW/
├── app/
│   ├── main.py              # FastAPI app, middleware, router registration
│   ├── config.py            # All settings loaded from .env via pydantic-settings
│   ├── database.py          # MongoDB connection (DatabaseManager singleton)
│   ├── redis_client.py      # Redis connection (optional, graceful fallback)
│   ├── models/
│   │   ├── __init__.py      # Exports all models
│   │   ├── user.py          # UserRegisterRequest, UserLoginRequest, TokenResponse...
│   │   ├── resume.py        # ResumeResponse, ParsedResumeData, WorkExperience...
│   │   ├── interview.py     # InterviewCreateRequest, InterviewResponse...
│   │   └── session.py       # ChatMessage, SessionResponse, MessageRole...
│   ├── routers/
│   │   ├── auth.py          # Auth endpoints + get_current_user dependency
│   │   ├── resumes.py       # Resume upload/list/get/delete
│   │   ├── interviews.py    # Interview CRUD endpoints
│   │   └── websocket.py     # WebSocket real-time interview chat
│   └── services/
│       ├── auth.py          # JWT creation/verification, bcrypt hashing
│       ├── resume_parser.py # Text extraction from PDF/DOCX/TXT
│       └── ai_service.py    # All Groq API calls
├── uploads/                 # Uploaded resume files (auto-created)
├── requirements.txt
├── .env
└── app.log
```

---

## Setup & Installation

### Prerequisites
- Python 3.10+
- MongoDB Atlas account
- Groq API key (free at console.groq.com)
- Redis (optional)

### 1. Clone & create virtual environment
```bash
git clone <repository-url>
cd AI-MOCK-INTERVIEW
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Create `.env` file
```env
APP_NAME="AI Interview Platform"
DEBUG=True
API_VERSION="v1"

SECRET_KEY="your-32-character-secret-key-here"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

MONGODB_URL="mongodb+srv://username:password@cluster.mongodb.net/?appName=Cluster"
MONGODB_DB_NAME="ai_interview_db"

GROQ_API_KEY="your-groq-api-key-here"

UPLOAD_DIR="./uploads"
MAX_UPLOAD_SIZE=10485760

RATE_LIMIT_REQUESTS=100
RATE_LIMIT_PERIOD=3600

ALLOWED_ORIGINS=["http://localhost:3000", "http://localhost:5173"]

REDIS_HOST="localhost"
REDIS_PORT=6379
REDIS_DB=0
```

### 4. Run the server
```bash
uvicorn app.main:app --reload
```

API runs at `http://localhost:8000`
Swagger docs at `http://localhost:8000/docs`

---

## API Endpoints

### Authentication — `/api/v1/auth`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/register` | No | Register new user, returns JWT tokens |
| POST | `/login` | No | Login with email/password, returns JWT tokens |
| POST | `/refresh` | No | Exchange refresh token for new access token |
| POST | `/logout` | Yes | Stateless logout |
| GET | `/me` | Yes | Get current user profile |

### Resumes — `/api/v1/resumes`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/upload` | Yes | Upload PDF/DOCX/TXT, extract text, parse with Groq AI |
| GET | `/` | Yes | List all resumes for current user |
| GET | `/{resume_id}` | Yes | Get single resume with full parsed data |
| DELETE | `/{resume_id}` | Yes | Delete resume and file from disk |

### Interviews — `/api/v1/interviews`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/` | Yes | Create interview — fetches resume, AI generates questions |
| GET | `/` | Yes | List all interviews for current user |
| GET | `/{interview_id}` | Yes | Get interview with all questions |
| PUT | `/{interview_id}/complete` | Yes | Mark interview as completed |
| DELETE | `/{interview_id}` | Yes | Delete interview |

### WebSocket — Real-time Interview Chat

```
WS /api/v1/ws/chat/{interview_id}?token={access_token}
```

WebSocket cannot send headers, so the JWT is passed as a query parameter. The server validates the token before accepting the connection.

**Message protocol:**

Server sends JSON:
```json
{ "type": "ai",       "content": "...", "question_index": 0, "total_questions": 10 }
{ "type": "complete", "content": "...", "session_id": "..." }
```

Client sends plain text (the answer):
```
"Your answer to the question"
```

---

## How It Works

### Resume Upload Flow
1. Validate file type (PDF/DOCX/TXT) and size (max 10MB)
2. Save file to `./uploads/` with UUID prefix to avoid collisions
3. Extract raw text using PyPDF2 (PDF) or python-docx (DOCX)
4. Send text to Groq AI for structured parsing
5. Save raw text + parsed data to MongoDB
6. Return structured resume data

Groq extracts: `full_name`, `email`, `phone`, `location`, `summary`, `skills[]`, `work_experience[]`, `education[]`, `certifications[]`, `languages[]`

### Interview Creation Flow
1. Client sends `resume_id` + `job_title`
2. Server fetches resume parsed data from MongoDB
3. Groq generates 10 personalised questions based on actual resume content and target role
4. Interview document saved to MongoDB with questions array
5. Return interview with all questions

### WebSocket Interview Flow
1. Client connects with JWT token as query param
2. Server validates token, fetches interview + questions
3. Session document created in MongoDB
4. AI sends greeting + Question 1
5. Client answers → AI gives feedback + asks next question
6. Repeats until all questions are answered
7. AI sends closing performance summary
8. Full conversation saved to sessions collection, interview marked completed

---

## Database Collections

| Collection | Purpose | Key Indexes |
|---|---|---|
| `users` | User accounts | `email` (unique), `created_at` |
| `resumes` | Uploaded resumes with parsed data | `user_id`, `uploaded_at` |
| `interviews` | Interview sessions with questions | `user_id`, compound `(user_id, created_at)` |
| `sessions` | WebSocket chat history | `interview_id`, `user_id` |

---

## Security

- **Passwords** hashed with bcrypt — never stored as plain text
- **JWT access tokens** expire in 30 minutes — limits damage if stolen
- **JWT refresh tokens** expire in 7 days — used only to get new access tokens
- **Route protection** via `get_current_user` dependency — all protected routes validate JWT automatically
- **Resource ownership** — every query filters by both document ID and `user_id` — users cannot access each other's data
- **Input validation** — Pydantic rejects invalid requests before any route logic runs with HTTP 422
- **File validation** — type and size checked before saving to disk

---

## Testing the WebSocket (Browser Console)

Swagger UI does not support WebSocket. Use the browser console instead:

```javascript
const TOKEN = "your_access_token_here";
const INTERVIEW_ID = "your_interview_id_here";

const ws = new WebSocket(
  `ws://127.0.0.1:8000/api/v1/ws/chat/${INTERVIEW_ID}?token=${TOKEN}`
);

ws.onopen    = ()      => console.log("Connected!");
ws.onmessage = (event) => console.log("AI:", JSON.parse(event.data).content);
ws.onerror   = (err)   => console.error("Error:", err);

// Send an answer
ws.send("Your answer here");
```

---

## Implementation Status

| Phase | Feature | Status |
|---|---|---|
| 1 | Foundation — FastAPI setup, MongoDB, middleware, health check | ✅ Complete |
| 2 | Authentication — register, login, JWT, refresh tokens | ✅ Complete |
| 3 | Resume upload, text extraction, Groq AI parsing | ✅ Complete |
| 4 | Interview management — create, list, complete, delete | ✅ Complete |
| 5 | WebSocket real-time AI interview chat | ✅ Complete |
| 6 | Frontend (React/Next.js) | ⏳ Planned |

---

## Key Dependencies

```
fastapi==0.110.0
uvicorn[standard]==0.27.1
motor==3.3.2
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
groq
PyPDF2==3.0.1
python-docx
pydantic==2.6.1
pydantic-settings==2.1.0
email-validator==2.1.0
python-multipart==0.0.9
```