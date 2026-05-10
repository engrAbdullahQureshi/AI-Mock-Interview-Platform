from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import time
import os

from app.config import settings
from app.database import DatabaseManager
from app.redis_client import RedisManager

# ========== LOGGING CONFIGURATION ==========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)


# ========== APPLICATION LIFESPAN ==========
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ========== STARTUP ==========
    logger.info("Starting AI Interview Platform...")
    logger.info(f"Environment: {'Development' if settings.DEBUG else 'Production'}")

    try:
        await DatabaseManager.connect_db()
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise

    await RedisManager.connect_redis()

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    logger.info(f"Upload directory: {settings.UPLOAD_DIR}")

    logger.info("Application started successfully!")
    logger.info("API Documentation: http://localhost:8000/docs")

    yield  # App serves requests here

    # ========== SHUTDOWN ==========
    logger.info("Shutting down application...")
    await DatabaseManager.close_db()
    await RedisManager.close_redis()
    logger.info("Application stopped cleanly")


# ========== CREATE FASTAPI APP ==========
app = FastAPI(
    title=settings.APP_NAME,
    description="""
    AI-Powered Mock Interview & Resume Analyzer Platform

    Features:
    - JWT Authentication with refresh tokens
    - Resume upload and parsing
    - AI-generated interview questions
    - Real-time interview chat (WebSocket)
    - Interview analytics and scoring

    Built with: FastAPI, MongoDB Atlas, Groq AI
    """,
    version=settings.API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    debug=settings.DEBUG
)


# ========== CORS MIDDLEWARE ==========
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========== REQUEST LOGGING MIDDLEWARE ==========
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    logger.info(f">> {request.method} {request.url.path}")
    response = await call_next(request)
    duration = time.time() - start_time
    logger.info(
        f"<< {request.method} {request.url.path} "
        f"[{response.status_code}] {duration:.3f}s"
    )
    response.headers["X-Process-Time"] = f"{duration:.3f}"
    return response


# ========== EXCEPTION HANDLERS ==========
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.DEBUG else "An unexpected error occurred",
            "type": type(exc).__name__ if settings.DEBUG else None
        }
    )


# ========== ROOT ENDPOINTS ==========
@app.get("/")
async def root():
    return {
        "message": "Welcome to AI Interview Platform API",
        "app": settings.APP_NAME,
        "version": settings.API_VERSION,
        "status": "running",
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc"
        }
    }


@app.get("/health")
async def health_check():
    health_status = {
        "api": "healthy",
        "timestamp": time.time(),
        "database": "unknown",
        "cache": "unknown"
    }

    try:
        db = DatabaseManager.get_db()
        await db.command("ping")
        health_status["database"] = "healthy"
    except Exception as e:
        health_status["database"] = f"unhealthy: {str(e)}"
        logger.error(f"Database health check failed: {e}")

    try:
        redis_client = await RedisManager.get_client()
        if redis_client:
            await redis_client.ping()
            health_status["cache"] = "healthy"
        else:
            health_status["cache"] = "not connected (optional)"
    except Exception as e:
        health_status["cache"] = f"unhealthy: {str(e)}"
        logger.warning(f"Redis health check failed: {e}")

    is_healthy = health_status["database"] == "healthy"

    return {
        "status": "healthy" if is_healthy else "degraded",
        "services": health_status
    }


@app.get("/api/v1/info")
async def api_info():
    return {
        "api_version": settings.API_VERSION,
        "app_name": settings.APP_NAME,
        "features": {
            "authentication": "JWT with refresh tokens",
            "resume_upload": "PDF, DOCX support",
            "ai_provider": "Groq (llama-3.3-70b-versatile)",
            "websocket": "Real-time interview chat at /api/v1/ws/chat/{interview_id}",
            "caching": "Redis" if await RedisManager.get_client() else "Disabled",
            "rate_limiting": "Enabled" if await RedisManager.get_client() else "Disabled"
        },
        "limits": {
            "max_upload_size": f"{settings.MAX_UPLOAD_SIZE / (1024*1024):.0f}MB",
            "allowed_extensions": settings.ALLOWED_EXTENSIONS,
            "rate_limit": f"{settings.RATE_LIMIT_REQUESTS} requests per {settings.RATE_LIMIT_PERIOD//3600} hour(s)"
        }
    }


# ========== INCLUDE ROUTERS ==========
from app.routers import auth
from app.routers import resumes
from app.routers import interviews     # Phase 4
from app.routers import websocket      # Phase 5

app.include_router(
    auth.router,
    prefix="/api/v1/auth",
    tags=["Authentication"]
)

app.include_router(
    resumes.router,
    prefix="/api/v1/resumes",
    tags=["Resumes"]
)

app.include_router(                    # Phase 4
    interviews.router,
    prefix="/api/v1/interviews",
    tags=["Interviews"]
)

app.include_router(                    # Phase 5
    websocket.router,
    prefix="/api/v1/ws",
    tags=["WebSocket"]
)


# ========== RUN APPLICATION ==========
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )