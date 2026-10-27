"""
Seed a demo account + one sample resume on first boot (when the users
collection is empty), so the reviewer can log in with demo@demo.com / demo1234
and immediately see a parsed resume — no signup fumbling in the Loom.

Everything here is honest and matches Abdullah's real background. All on-screen
scores still come from live model calls; only this starting profile is seeded.
"""

import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

DEMO_EMAIL = "demo@demo.com"
DEMO_PASSWORD = "demo1234"
DEMO_USERNAME = "abdullah_demo"

# Honest structured profile (mirrors Abdullah_Resume_2026.pdf — no inflation).
SAMPLE_PARSED = {
    "full_name": "Abdullah Qureshi",
    "email": "abdullah.qureshi@example.com",
    "phone": "+92-3xx-xxxxxxx",
    "location": "Lahore, Pakistan",
    "summary": (
        "AI engineer and full-stack developer with ~2 years of experience across "
        "LLM agents, backend, and full-stack work. Comfortable building with FastAPI, "
        "Node/Express and Next.js, and evaluating model output rather than just calling "
        "an API. Fast, AI-first workflow with honest judgement about model limits."
    ),
    "skills": [
        "Python", "FastAPI", "JavaScript", "TypeScript", "React", "Next.js",
        "Node.js", "Express", "LLM agents", "Prompt engineering",
        "LLM evaluation / benchmarking", "RAG", "Claude Agent SDK", "MCP",
        "Groq", "WebSockets", "MongoDB", "PostgreSQL (pgvector)", "AWS (EC2/S3/RDS)",
        "Docker", "Git", "scikit-learn", "OpenCV",
    ],
    "work_experience": [
        {
            "company": "Aiden Risk",
            "position": "Founding AI Engineer (Contract)",
            "duration": "Mar 2026 – Sep 2026",
            "description": (
                "Contributed to an AI commercial-insurance placement platform "
                "(Node/Express, Next.js, Postgres+pgvector, Claude Agent SDK). "
                "Migrated carrier-portal login testing to deterministic Playwright "
                "recipes; benchmarked 5 LLMs on cost/performance; wrote root-cause "
                "reports on production bugs (fixes adopted)."
            ),
        },
        {
            "company": "Codeninja Inc.",
            "position": "Associate Software Engineer",
            "duration": "Mar 2025 – Apr 2026",
            "description": (
                "Backend fixes via Jira/agile and SQL; DevSecOps on AWS (EC2/RDS) for "
                "a client; worked on a Middle-East e-commerce application."
            ),
        },
        {
            "company": "Deline Media",
            "position": "Trainee Software Engineer",
            "duration": "Aug 2024 – Jan 2025",
            "description": (
                "Built REST APIs with auth and RBAC using Angular, Node/Express and "
                "Laravel for education and healthcare patient-management apps."
            ),
        },
        {
            "company": "NetSol Technologies",
            "position": "AI / Data Science Intern",
            "duration": "Jun 2024 – Aug 2024",
            "description": "Data analysis and preprocessing for ML model training.",
        },
    ],
    "education": [
        {
            "institution": "LUMS",
            "degree": "MS",
            "field": "Artificial Intelligence (in progress)",
            "year": "2025 –",
        },
        {
            "institution": "FAST NUCES, Lahore",
            "degree": "BS",
            "field": "Computer Engineering",
            "year": "2024",
        },
    ],
    "certifications": [],
    "languages": ["English", "Urdu"],
}

SAMPLE_RAW_TEXT = (
    "Abdullah Qureshi — AI Engineer & Full-Stack Developer — Lahore, Pakistan. "
    "~2 years experience. Founding AI Engineer (Contract) at Aiden Risk; Associate "
    "Software Engineer at Codeninja; Trainee SWE at Deline Media; AI/DS Intern at "
    "NetSol. MS AI (LUMS, in progress), BS Computer Engineering (FAST NUCES). "
    "Skills: Python, FastAPI, Next.js, Node, LLM agents, RAG, Groq, Claude Agent SDK, "
    "WebSockets, MongoDB, Postgres/pgvector, AWS."
)


async def seed_if_empty(db) -> None:
    """Insert the demo user + sample resume if no demo user exists yet."""
    try:
        existing = await db.users.find_one({"email": DEMO_EMAIL})
        if existing:
            return

        from app.services.auth import hash_password

        now = datetime.now(timezone.utc)
        user_doc = {
            "username": DEMO_USERNAME,
            "email": DEMO_EMAIL,
            "password_hash": hash_password(DEMO_PASSWORD),
            "full_name": "Abdullah Qureshi",
            "created_at": now,
            "updated_at": now,
            "is_active": True,
        }
        result = await db.users.insert_one(user_doc)
        user_id = str(result.inserted_id)

        resume_doc = {
            "user_id": user_id,
            "file_name": "Abdullah_Resume_2026.pdf",
            "file_size": 58000,
            "uploaded_at": now,
            "raw_text": SAMPLE_RAW_TEXT,
            "parsed_data": SAMPLE_PARSED,
        }
        await db.resumes.insert_one(resume_doc)

        logger.info("Seeded demo account (demo@demo.com) + sample resume.")
    except Exception as e:
        logger.warning(f"Seeding skipped due to error: {e}")
