# Demo Guide — AI Mock Interview Platform

Everything you need to run the app and record the Loom for Reece.

---

## 1. Run it (two terminals)

**Backend** (from the repo root `AI-Mock-Interview-Platform/`):
```bash
# one-time: create venv + install
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt

# run
.venv\Scripts\python -m uvicorn app.main:app --port 8000
```

**Frontend** (from `AI-Mock-Interview-Platform/frontend/`):
```bash
npm install
npm run dev
```

- App: **http://localhost:3000**
- API docs: http://localhost:8000/docs
- Demo login: **demo@demo.com / demo1234** (seeded on first boot, with a sample resume already parsed)

> The app runs with **no database** — it falls back to an in-memory store (`.localdb.json`). The only thing you must set is your Groq key.

### The one required secret
Copy `.env.example` to `.env` and set:
```
GROQ_API_KEY=your_free_key_from_console.groq.com
SECRET_KEY=any-random-32+-character-string
```
Without the Groq key the UI loads and auth works, but resume parsing, gap analysis, questions, and scoring will show an "AI unavailable" error. **Set the key before recording.**

---

## 2. The Loom script (~2.5 min)

Keep it calm and let the product talk. Narration beats, screen by screen:

1. **(0:00) Hook.** "This is a mock-interview platform I built. The idea mirrors something you'll recognise, Reece — it scores every conversation against ground truth. Let me show you." → click **Use demo account**.
2. **(0:15) It understood me.** On the dashboard, open the resume. "An LLM extracted a structured profile from my PDF — skills, experience, education. These are the candidate's *facts*."
3. **(0:40) It scored me against the real job.** Go to **Analyze**, click **Load sample JD** (a realistic Mocean-style role), click **Analyze fit**. "It scores me against the *job's* facts — here's the match score, what lines up, what I'd need to strengthen. Honest, not inflated."
4. **(1:05) It adapted to my gaps.** Click **Start tailored interview**. "The questions are generated from my resume *and* the JD gaps — so it deliberately probes my weak spots, the same way you re-check an agent against the business's facts." Answer two questions on camera.
5. **(1:45) The part I care about — the report.** End the interview. "Every answer is scored across five dimensions by the model, and the aggregate is computed by **deterministic code, not the model grading itself** — so the number is reproducible. Strengths, gaps, per-question breakdown. Auditable."
6. **(2:15) Close.** "Stack is FastAPI + Groq on the back, Next.js/React/TypeScript on the front, built to run with one API key. Happy to walk through any layer. I build fast because I lean hard on AI tooling day to day."

---

## 3. Honest answers to what Reece will likely ask

- **"How does the scoring actually work?"** — "The LLM returns per-dimension scores for each answer against a rubric in the system prompt, at low temperature. I aggregate in Python — mean per dimension, then mean of the dimensions — so the overall score is deterministic and reproducible. The model judges; code tallies."
- **"Why Groq / this model?"** — "Fast, cheap inference and solid JSON adherence for `llama-3.3-70b`. The AI layer is isolated in one service module, so swapping providers is a small change. At Aiden Risk I benchmarked five LLMs on cost/performance, so I'm comfortable making that call empirically."
- **"What about voice?"** — "Deliberately out of v1 to keep it reliable. The conversation layer already streams over WebSockets, so adding speech-to-text in and text-to-speech out is the natural next step — I'd start with a browser speech stack to prove it, then a hosted neural voice. I've worked with real-time *audio* before on a medical-transcription project, though not telephony yet."
- **"How would you make it production-grade?"** — "Persist to Postgres, harden auth and add rate limits, put the LLM calls behind a queue with retries, add eval regression tests on the scoring prompt, and observability on latency/cost per call. Right now it's a focused personal project, not production — I kept the scope honest."
- **"Did you use AI to build it?"** — "Yes, heavily — Claude Code and Cursor are my daily drivers. I designed the architecture and the scoring approach; AI accelerated the implementation. That's how I work, and it's why I ship fast ~2 years in."

**Framing guardrails:** ~2 years of experience. Say "I built / I designed" for *this* project; "contributed to" for prior jobs (Aiden Risk, Codeninja). Don't claim telephony, Kubernetes, Twilio, or production fine-tuning. Lead with: real LLM-agent production exposure, breadth across AI/backend/full-stack, and honest judgement about model limits.

---

## 4. What's real vs. not (so nothing bites you)
- **Real:** every on-screen number comes from a live Groq call. Auth (JWT + bcrypt), resume parsing, gap analysis, personalized questions, 5-dimension scoring with Python aggregation — all real.
- **Simplified for the demo:** storage is an in-memory JSON file by default (MongoDB is wired but optional); no queue/observability yet; voice is deferred. These are deliberate scope choices — say so if asked.
