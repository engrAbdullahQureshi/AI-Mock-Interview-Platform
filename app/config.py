from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    HOW THIS WORKS:
    1. Reads values from .env file automatically
    2. Validates data types (if you put "hello" for a number, it will error)
    3. Provides default values if env variable is missing
    """
    
    # ========== Application Settings ==========
    APP_NAME: str = "AI Interview Platform"
    DEBUG: bool = True  # Changed to True for development
    API_VERSION: str = "v1"
    
    # ========== Security - JWT Configuration ==========
    SECRET_KEY: str = "default-secret-key-change-this-in-production-min-32-characters"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # ========== Database - MongoDB (OPTIONAL) ==========
    # Leave MONGODB_URL empty to run with the built-in in-memory store
    # (perfect for local demos / reviewers with no MongoDB). Set it in .env
    # to use a real MongoDB Atlas cluster. Never commit real credentials here.
    MONGODB_URL: str = ""
    MONGODB_DB_NAME: str = "ai_interview_db"
    
    # ========== Redis (Optional) ==========
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    # ========== AI Service ==========
    GROQ_API_KEY: str | None = None
    # Centralized so a Groq model change is a one-line/env fix, not a hunt.
    GROQ_MODEL: str = "openai/gpt-oss-120b"
  
    
    
    # ========== File Upload ==========
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".docx", ".txt"]
    
    # ========== Rate Limiting ==========
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 3600
    
    # ========== CORS ==========
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()