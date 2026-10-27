# AI Mock Interview Platform — Build Blueprint

> **Audience for this build:** Reece Makwana, Co-founder & CEO of **Mocean** ("agentic voice — always on"). Mocean answers every call/chat/email for specialist businesses in the business's own voice, **scores every conversation**, and **re-checks each agent against the business's own facts every night**.
>
> **Why this design wins him over:** our platform does the same *shape* of thing for interviews — it holds a conversation, **scores every answer against the candidate's own facts (their resume) and the job's own facts (the JD)**, and produces an auditable report. Same mental model, different domain. When Reece sees "score every conversation against ground truth," he sees his own product.
>
> **Direction chosen:** Polished **text + analytics** web app. Voice is deliberately kept out of the critical path (one-config swap later — see §8). Build quality and the analytics story carry the "wow."
>
> **Honesty guardrails (non-negotiable):** This is a strong **personal project built fast with AI tooling** — present it that way. Abdullah has ~2 years of experience. In narration: "I built", "I designed" are fine for *this* project; for prior jobs use "contributed to", never "led/shipped". Never claim tech he hasn't used (no Kubernetes, Django, Twilio, Azure, Snowflake, TensorFlow, production fine-tuning). Every number on screen must come from a real model call — no fake data.

---

## 1. Product Spec & Demo Flow

The app is a **personalized interview coach**. The reviewer experiences these screens in order. This order **is** the Loom script.

### Screen 0 — Landing / Auth (`/`, `/login`, `/register`)
- One-screen value prop: *"Practice the interview for the exact job you want — and get scored against the job, not vibes."*
- Register or log in → JWT stored in memory + refresh token. Redirect to Dashboard.
- **Seed a demo account** on first backend boot (`demo@demo.com` / `demo1234`) so the Loom never fumbles signup. Show a "Use demo account" button on login.

### Screen 1 — Dashboard (`/dashboard`)
- Empty state → big primary CTA: **"New Interview Prep"**.
- Once data exists: cards for recent resumes + recent interview reports (overall score badge on each).
- Left sidebar nav: Dashboard · Resumes · Interviews · (footer: signed-in user, logout).

### Screen 2 — Upload Resume (`/resumes/new`)
- Drag-and-drop zone (PDF/DOCX/TXT, ≤10MB). On drop → `POST /resumes/upload`.
- While parsing: skeleton + "Reading your resume…" shimmer.
- Result: **Parsed Profile card** — name, title, contact, a **skills chip cloud**, work-experience timeline, education. This proves the AI actually understood the document. Button: **"Next: target a job →"**.

### Screen 3 — Target Job + Gap Analysis (`/analyze`)
- Left: large textarea to paste a **Job Description** (pre-filled with the Mocean sample JD from §6 via a "Load sample JD" button so the demo is one click).
- Click **"Analyze fit"** → `POST /analysis/gap`.
- Right panel animates in:
  - **Match Score ring** (0–100) with a one-line verdict ("Strong fit — a few gaps to address").
  - **Matched skills** (green chips) vs **Missing / to-strengthen** (amber chips).
  - **Summary** paragraph: honest, specific, 3–4 sentences.
  - Primary CTA: **"Start tailored interview →"** (passes resume_id + JD + matched/missing into interview creation).

### Screen 4 — Live Interview (`/interview/[id]`)
- Chat UI. AI interviewer greets the candidate by name and references the role.
- Progress bar: "Question 3 / 8". Each AI turn = short feedback on the previous answer + the next question. Questions are **personalized** to the resume AND the JD gaps (missing skills get probed — mirrors Mocean's "re-check against the business's own facts").
- Candidate types answers. Clean chat bubbles, typing indicator, auto-scroll.
- "End interview" button always visible. On finish → `POST /interviews/{id}/complete` then route to the report.

### Screen 5 — Analytics Report (`/interview/[id]/report`) — **the wow screen**
- Header: **Overall score ring** + verdict + role + date.
- **Dimension breakdown** (radar OR horizontal bars): *Relevance · Technical Depth · Communication · Specificity · JD Alignment* (0–100 each).
- **Per-question accordion**: each question → candidate's answer → dimension sub-scores → one-line AI feedback. This is the "every conversation gets read and scored" moment — call it out in narration.
- **Strengths** (3 bullets) and **Areas to improve** (3 bullets), each tied to evidence from an answer.
- **JD-gap recap**: which missing skills came up and how they were handled.
- Buttons: "Retake" · "Export report" (print-to-PDF via `window.print()` with a print stylesheet — no new dependency).

**Narrative spine for the Loom:** upload → *it understood me* → analyze → *it scored me against the real job* → interview → *it adapted its questions to my gaps* → report → *every answer scored against ground truth, auditable*. That last line is the Mocean echo.

---

## 2. Visual Design System

**Aesthetic:** confident dark SaaS — think Linear/Vercel restraint with one electric accent. Calm surfaces, high contrast text, a single vivid action color, generous spacing. No gradients-as-decoration; one subtle accent glow on the score ring only.

### Color tokens (CSS variables; Tailwind `theme.extend.colors`)
```
--bg:            #0B0E14   /* app background */
--surface:       #141922   /* cards */
--surface-2:     #1C2230   /* raised / hover */
--border:        #262E3D
--text:          #E6EAF2   /* primary text */
--text-muted:    #9AA6B9   /* secondary text */
--text-faint:    #5E6B82   /* labels, captions */
--accent:        #6366F1   /* indigo — primary actions, score ring */
--accent-hover:  #7C7FF2
--accent-soft:   #6366F11A /* 10% indigo, chip/glow backgrounds */
--success:       #22C55E   /* matched skills, high scores */
--success-soft:  #22C55E1A
--warning:       #F59E0B   /* missing skills, mid scores */
--warning-soft:  #F59E0B1A
--danger:        #EF4444   /* low scores */
--info:          #38BDF8   /* accents in charts */
```
**Score → color mapping:** ≥80 success · 60–79 accent · 40–59 warning · <40 danger. Use everywhere a score appears for instant legibility.

### Typography (Google Fonts)
- **Display / headings:** `Space Grotesk` (600/700) — modern, a little product-y.
- **Body / UI:** `Inter` (400/500/600).
- **Mono (scores, chips counts, code):** `JetBrains Mono` (500).
- Scale (rem): 0.75 / 0.875 / 1 / 1.125 / 1.25 / 1.5 / 2 / 2.5 / 3.

### Spacing, radius, elevation
- Spacing scale (px): 4 · 8 · 12 · 16 · 24 · 32 · 48 · 64. Page gutter 24 (16 on mobile).
- Radius: `sm 8` · `md 12` · `lg 16` · `xl 24` · `full 9999`. Cards = `lg`. Buttons = `md`. Chips/rings = `full`.
- Shadow: cards `0 1px 2px #00000040`; raised/hover `0 8px 24px #00000059`. Accent glow on score ring only: `0 0 40px var(--accent-soft)`.
- Motion: 150ms ease for hover, 300ms ease-out for panel/score reveals. Animate the score ring sweeping 0→value and numbers counting up.

### Component inventory (build these as reusable React components)
- **Button**: `primary` (accent fill), `secondary` (surface-2 + border), `ghost`, `danger`. States: hover, active, disabled, loading (spinner).
- **Card**: surface, `lg` radius, 1px border, 24px padding, optional header row.
- **Input / Textarea**: surface-2, border, focus ring in accent; labels in `text-faint` uppercase 0.75rem.
- **ChatBubble**: `ai` (surface-2, left, avatar "AI") vs `user` (accent-soft, right). Timestamp `text-faint`. Typing indicator (3 bouncing dots).
- **ScoreRing**: SVG circular gauge, animated sweep, big mono number center, color by score band, optional glow. Sizes `sm 64` / `lg 180`.
- **SkillChip**: `matched` (success-soft bg, success text, check icon) / `missing` (warning-soft bg, warning text, plus icon). Rounded-full, 0.875rem.
- **DimensionChart**: Recharts **RadarChart** (preferred for the 5 dimensions) with a horizontal **BarChart** fallback. Grid/stroke in `--border`, fill `--accent` at 30% opacity.
- **ProgressBar**: thin, accent fill, used for "Question x/y".
- **StatBadge**: small pill showing a score with band color (used on dashboard cards).
- **Accordion**: for per-question report rows.
- **Skeleton / Shimmer**: for parsing + analysis loading states.
- **Toast**: top-right, for errors ("Couldn't reach AI service") and success.
- **EmptyState**: icon + headline + CTA.

### Key screen layouts
- **App shell:** fixed left sidebar (240px, surface, nav items with icon+label, active = accent-soft bg + accent left-border), main content max-width 1080px centered, 24px gutters. Collapses to top bar on mobile.
- **Gap analysis:** two columns on desktop (JD input left ~45%, results right ~55%); stacks on mobile with results below.
- **Interview:** centered 760px chat column; sticky header with role + progress; sticky input bar at bottom.
- **Report:** full-width grid — top row: score ring (left) + verdict/meta (right); second row: dimension chart (left) + strengths/improvements (right); then full-width per-question accordion. Print stylesheet flattens to single column, white bg, black text.

---

## 3. Tech Stack & Folder Layout

**Frontend:** Next.js (App Router) + React + TypeScript + Tailwind CSS + Recharts. State: React context for auth + lightweight fetch wrapper (no Redux). Charts only via Recharts. Icons: `lucide-react`.

**Backend:** existing FastAPI + Groq (`llama-3.3-70b-versatile`). Add two capabilities: gap-analysis + scoring (both are Groq JSON calls).

### Folder layout
```
AI-Mock-Interview-Platform/
├── app/                 # existing FastAPI backend (hardened, not rewritten)
│   ├── routers/         # + analysis.py (new); interviews.py gains scoring + report
│   ├── services/        # ai_service.py gains gap_analysis + answer scoring
│   └── store/           # NEW: storage abstraction (Mongo OR in-memory)
├── frontend/            # NEW — Next.js app
│   ├── app/             # routes: /, login, register, dashboard, resumes, analyze, interview/[id], interview/[id]/report
│   ├── components/      # component inventory from §2
│   ├── lib/             # api client, auth context, types, scoreColor()
│   └── styles/          # globals.css with CSS vars + Tailwind
├── requirements.txt     # FIX: must list groq, python-docx, pymongo — remove google-generativeai
├── .env.example         # no real secrets
└── BLUEPRINT.md
```

### Zero-setup rule (critical for the demo)
A reviewer must run the whole thing with **only a Groq key** — no MongoDB account.

Implement a **storage abstraction** `app/store/`:
- Define an async `Store` interface: `users`, `resumes`, `interviews`, `sessions` with `insert_one / find_one / find / update_one / delete_one` returning plain dicts with a string `id`.
- `MongoStore` = current Motor code behind that interface.
- `MemoryStore` = pure-Python dicts, generates ids with `uuid4().hex`, persisted to a local JSON file (`./.localdb.json`) so data survives a reload during the demo.
- **Selection logic at startup:** if `MONGODB_URL` is set *and* a ping succeeds within 3s → `MongoStore`; otherwise log a clear warning and fall back to `MemoryStore`. The app must **boot and fully function** with no Mongo. Routers depend on `get_store()`, never on Motor directly.
- `config.py`: **remove the hardcoded live MongoDB URL** (default to `None`). `GROQ_API_KEY` stays env-only. If Groq key missing, AI endpoints return a friendly 503 and the UI shows a toast — app still navigable.
- CORS: allow `http://localhost:3000`.
- **Seed** demo user + one sample resume on boot when the store is empty (so Screens 1–2 have content instantly).

> Builders: do **not** break existing Mongo behavior — `MongoStore` must preserve current field names (`password_hash`, `user_id`, `questions`, etc.). The abstraction wraps; it does not rename.

---

## 4. API Contract

Base prefix `/api/v1`. Auth via `Authorization: Bearer <access_token>`. All responses JSON.

### Existing (keep, build on)
| Method | Path | Body | Response (shape) |
|---|---|---|---|
| POST | `/auth/register` | `{username,email,password}` | `{access_token,refresh_token,token_type,expires_in,user:{id,username,email,created_at}}` |
| POST | `/auth/login` | `{email,password}` | same as register |
| POST | `/auth/refresh` | `{refresh_token}` | same |
| GET | `/auth/me` | — | `{id,username,email,created_at}` |
| POST | `/resumes/upload` | multipart `file` | `ResumeResponse` (below) |
| GET | `/resumes/` | — | `{resumes:[ResumeResponse],total}` |
| GET | `/resumes/{id}` | — | `ResumeResponse` |
| DELETE | `/resumes/{id}` | — | `{message,success}` |
| POST | `/interviews/` | `{resume_id,job_title,num_questions}` | `InterviewResponse` |
| GET | `/interviews/` | — | `{interviews:[InterviewListResponse],total}` |
| GET | `/interviews/{id}` | — | `InterviewResponse` |
| PUT | `/interviews/{id}/complete` | — | `InterviewResponse` |
| DELETE | `/interviews/{id}` | — | `{message,success}` |
| WS | `/ws/chat/{interview_id}?token=` | text in / JSON out | see §existing websocket |

`ResumeResponse`:
```json
{
  "id": "abc123", "user_id": "u1",
  "file_name": "Abdullah_Resume_2026.pdf", "file_size": 58000,
  "uploaded_at": "2026-10-28T10:00:00Z",
  "raw_text": "…",
  "parsed_data": {
    "full_name": "Abdullah Qureshi", "email": "…", "phone": "…", "location": "Lahore, Pakistan",
    "summary": "…", "skills": ["Python","FastAPI","Next.js","LLM agents","Groq"],
    "work_experience": [{"company":"Aiden Risk","position":"Founding AI Engineer (Contract)","duration":"Mar 2026–Sep 2026","description":"…"}],
    "education": [{"institution":"LUMS","degree":"MS","field":"Artificial Intelligence","year":"2025–"}],
    "certifications": [], "languages": ["English","Urdu"]
  }
}
```

### NEW endpoints

**1) JD Gap Analysis** — `POST /api/v1/analysis/gap`
Request:
```json
{ "resume_id": "abc123", "job_description": "<pasted JD text>" }
```
Response:
```json
{
  "match_score": 81,
  "verdict": "Strong fit — a few gaps to strengthen",
  "matched_skills":  ["Python","FastAPI","LLM agents","WebSockets","Next.js","Groq/Claude Agent SDK","MongoDB"],
  "missing_skills":  ["Production voice/telephony stack","Kubernetes","Observability at scale"],
  "summary": "Abdullah's AI-agent and full-stack background maps closely to this founding AI engineer role… Gaps are mostly voice-infra specific and learnable.",
  "resume_id": "abc123"
}
```
The frontend passes `matched_skills` + `missing_skills` + `job_description` into interview creation so questions target gaps. Extend `POST /interviews/` to optionally accept `job_description` and `focus_skills` (both optional, back-compatible).

**2) Interview Report / Scoring** — `GET /api/v1/interviews/{id}/report`
Computed after completion by scoring the saved transcript (`sessions` messages) with one Groq call; cache the result on the interview/session doc so re-opening the report is instant.
Response:
```json
{
  "interview_id": "iv1",
  "job_title": "Founding AI Engineer",
  "completed_at": "2026-10-28T10:20:00Z",
  "overall_score": 78,
  "verdict": "Solid performance with clear technical depth; tighten specificity.",
  "dimensions": { "relevance": 82, "technical_depth": 80, "communication": 76, "specificity": 70, "jd_alignment": 79 },
  "strengths":   ["Explained agent/LLM tradeoffs concretely", "…", "…"],
  "improvements":["Quantify impact with metrics", "…", "…"],
  "jd_gap_recap":"Handled the voice-infra gap honestly by mapping it to prior real-time audio work (MedScribe).",
  "per_question": [
    {
      "index": 1, "question": "…", "answer": "…",
      "scores": { "relevance": 85, "technical_depth": 80, "communication": 78, "specificity": 72, "jd_alignment": 80 },
      "feedback": "Strong framing; add a concrete metric to make it land."
    }
  ]
}
```
If a report is requested before completion, return `409` with `{detail:"Interview not completed"}`.

> **WebSocket note for builders:** the existing WS passes `?token=`. Keep it. The frontend opens the socket after interview creation; server greeting arrives as `{type:"ai",...}`, client sends plain-text answers, server replies `{type:"ai"|"complete"|"error"}`. On `complete`, frontend calls the report endpoint.

---

## 5. Scoring Rubric & LLM Prompt Design

Both calls use Groq `llama-3.3-70b-versatile`, `temperature` 0.2 (deterministic-ish), `response_format` JSON instruction, and a hardened JSON extractor (reuse `_clean_json_response`). Always `try/except` → on failure return a graceful error, never crash.

### (a) Gap analysis
**System:** "You are a precise technical recruiter. Compare a candidate's structured resume to a job description. Be fair and honest — do not inflate. Return ONLY valid JSON."
**User (templated):** include `parsed_data` (JSON) + `job_description` + the required output schema. Rules:
- `match_score` 0–100 = weighted blend: **core skill overlap 45% · domain/role relevance 25% · seniority fit 20% · breadth 10%**. Tell the model this weighting explicitly.
- `matched_skills`: skills/experience in the resume that the JD asks for (max 10).
- `missing_skills`: JD requirements not evidenced in the resume (max 6). These feed interview questions.
- `verdict`: ≤8 words. `summary`: 3–4 sentences, specific, honest about gaps.
Output schema = the §4 response exactly.

### (b) Interview scoring
**System:** "You are a fair, rigorous interview assessor. Score each answer only on what was actually said. Ground every judgement in the candidate's resume facts and the job's requirements. Return ONLY valid JSON."
**User:** include `job_title`, `job_description` (if present), `parsed_data` summary (the ground-truth facts), and the full Q/A transcript. For **each** question return the 5 dimension scores (0–100) + one-line feedback.
**Dimensions (0–100):**
- **Relevance** — did the answer address the question?
- **Technical Depth** — correctness + depth of technical reasoning.
- **Communication** — clarity, structure, conciseness.
- **Specificity** — concrete examples/metrics vs vague claims.
- **JD Alignment** — does it evidence what *this* job needs?

**Aggregation (compute in Python, not by the model, for trust):**
- Per-question overall = mean of its 5 dimensions.
- Report dimension score = mean of that dimension across all questions.
- `overall_score` = mean of the 5 report dimensions, rounded.
- `strengths`/`improvements`: ask the model for 3 each, each referencing a real answer.
This split (model scores dimensions, Python aggregates) is a deliberate, defensible design choice — call it out in the demo: *"the model judges, deterministic code aggregates, so the number is reproducible."* That line lands hard with a founder who re-checks agents nightly.

---

## 6. Sample Job Description (one-click "Load sample JD")

Store as a constant the frontend can insert. Tuned to yield ~78–82% honest match against Abdullah's real background.

> **Founding Full-Stack AI Engineer — Mocean (Remote, contract)**
>
> Mocean builds agentic voice for specialist businesses — AI that answers every call, chat and email, books work, and scores every conversation against the business's own facts. We're a small founding team and move fast.
>
> **What you'll do**
> - Build and ship features across the stack: TypeScript/React front end, Python/Node services, real-time pipelines.
> - Design and iterate LLM agents: prompt design, tool use, retrieval/grounding against each business's facts, and automated evaluation of agent quality.
> - Own real-time conversation flows (streaming, WebSockets) and the scoring/QA layer that reads and grades every conversation.
> - Instrument everything: logging, metrics, regression checks so agents don't drift.
>
> **You should have**
> - ~2+ years building production-ish software; strong Python and JavaScript/TypeScript.
> - Hands-on LLM/agent experience — prompt engineering, tool calling, RAG/grounding, and evaluating model output (not just calling an API).
> - Comfort with FastAPI or Node/Express, React/Next.js, and a real database (Postgres or Mongo).
> - A bias for shipping, honest judgement about model limits, and strong written communication.
>
> **Nice to have**
> - Real-time audio / voice / telephony experience (STT/TTS, streaming).
> - Vector search (pgvector), queues, cloud deploy (AWS), observability.
> - Experience in regulated/specialist domains (insurance, healthcare, trades).

**Expected honest result vs Abdullah:** match ~**80%**. Matched: Python, TS/React/Next, FastAPI, Node/Express, LLM agents (Claude Agent SDK/MCP), prompt eng, LLM eval/benchmarking, RAG/pgvector, WebSockets, Mongo/Postgres, AWS basics, insurance+healthcare domain. Honest gaps: production **voice/telephony** (has adjacent real-time *audio* via MedScribe — map it, don't claim telephony), large-scale **observability**, Kubernetes. Those gaps are real and learnable — perfect, because the interview then probes them and Abdullah answers honestly.

---

## 7. Demo (Loom) Script + Talking Points

### 2.5-minute narration (screen-by-screen)
1. **(0:00) Hook** — "This is a mock-interview platform I built. The idea mirrors something you'll recognize, Reece: it scores every conversation against ground truth. Let me show you." Log in with demo account.
2. **(0:15) Upload** — drop my resume. "It extracts a structured profile from the PDF with an LLM — skills, experience, education. That's the candidate's *facts*."
3. **(0:40) Gap analysis** — load the Mocean JD, click Analyze. "Now it scores me against the *job's* facts — 80% match, here's what lines up, here's what I'd need to strengthen. Honest, not inflated."
4. **(1:05) Interview** — start it. "The questions are generated from my resume *and* the JD gaps — so it deliberately probes my weak spots, the same way you re-check an agent against the business's facts." Answer two questions on camera.
5. **(1:45) Report** — "Here's the part I care about: every answer is scored across five dimensions by the model, and the aggregate is computed by deterministic code so the number is reproducible — not the model grading itself. Strengths, gaps, per-question breakdown. Auditable."
6. **(2:15) Close** — "Stack's FastAPI + Groq on the back, Next.js/React/TS on the front, built to run with one API key. Happy to walk through any layer. I built this fast because I lean hard on AI tooling day-to-day."

### Honest answers to questions Reece will likely ask
- **"How does the scoring actually work?"** — "The LLM returns per-dimension scores for each answer with a rubric in the system prompt at low temperature. I aggregate in Python — mean per dimension, then mean of dimensions — so the overall score is deterministic and reproducible. The model judges; code tallies."
- **"Why Groq / this model?"** — "Fast, cheap inference and solid JSON adherence for `llama-3.3-70b`. The AI layer is isolated in one service module, so swapping providers is a small change. At Aiden Risk I benchmarked five LLMs on cost/perf, so I'm comfortable making that call empirically." (True — from career profile.)
- **"What about voice?"** — "Deliberately out of v1 to keep it reliable. The conversation layer is already streaming over WebSockets, so adding STT in / TTS out is the natural next step — I'd start with a browser speech stack to prove it, then a hosted neural voice. I've worked with real-time *audio* before on a medical-transcription project, though not telephony yet." (True — MedScribe; don't claim Twilio/telephony.)
- **"How would you make this production-grade?"** — "Persist to Postgres, add auth hardening and rate limits, put the LLM calls behind a queue with retries, add eval regression tests on the scoring prompt, and observability on latency/cost per call. Right now it's a focused personal project, not production — I kept the scope honest."
- **"How long did this take / did you use AI?"** — "Yes, heavily — Claude Code and Cursor are my daily drivers. I designed the architecture and scoring approach; AI accelerated the implementation. That's how I work, and it's why I ship fast for ~2 years in."
- **Experience level** — always ~2 years, "contributed to" for Aiden Risk/Codeninja work, never "led a team" or "shipped to millions". Lead with: real LLM-agent production exposure, breadth across AI/backend/full-stack, honest judgement.

---

## 8. Voice (later, one-config swap — DO NOT build now)
Keep the conversation layer provider-agnostic. Later: add `POST /voice/stt` (Groq Whisper) and a TTS adapter interface with a `BROWSER | ELEVENLABS | DEEPGRAM` switch in config; the chat screen gains a mic button and plays TTS of AI turns. Nothing in v1 should block this. Not in scope for the demo build.

---

## 9. Build order for the crew (dependency-aware)
1. **Backend hardening** (first, others depend on it): storage abstraction + Mongo/memory fallback, fix `requirements.txt`, remove hardcoded secret, seed demo data, CORS. Keep existing endpoints green.
2. **Backend AI features**: `/analysis/gap` + `/interviews/{id}/report` + extend interview creation with JD/focus. (After step 1's store exists.)
3. **Frontend**: scaffold Next.js + Tailwind + design system/components, then screens 0–5 against the API contract. (Can start the design-system/components in parallel with steps 1–2; wire data after endpoints exist.)
4. **Integration + local run + demo polish**: seed flow, "Load sample JD", print stylesheet, error toasts, final pass on the wow screen.
