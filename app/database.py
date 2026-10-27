from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
from app.config import settings
import logging

# Setup logging to see connection status
logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Manages MongoDB connection using Motor (async MongoDB driver).
    
    WHY MOTOR INSTEAD OF PYMONGO?
    - Motor is async-compatible (non-blocking)
    - Works perfectly with FastAPI's async nature
    - Allows handling multiple requests simultaneously
    
    PATTERN: Singleton
    - Only ONE database connection for entire app
    - Shared across all requests
    - More efficient than creating connection per request
    """
    
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None
    using_memory: bool = False

    @classmethod
    async def connect_db(cls):
        """
        Establish the database connection.

        If MONGODB_URL is set AND reachable within 3s, use MongoDB (Motor).
        Otherwise transparently fall back to the in-memory store so the whole
        app runs locally with only a Groq API key (perfect for demos/reviewers).
        """
        url = (settings.MONGODB_URL or "").strip()

        if url:
            try:
                cls.client = AsyncIOMotorClient(url, serverSelectionTimeoutMS=3000)
                cls.db = cls.client[settings.MONGODB_DB_NAME]
                await cls.client.admin.command("ping")
                cls.using_memory = False
                logger.info(f"Connected to MongoDB: {settings.MONGODB_DB_NAME}")
                await cls.create_indexes()
                return
            except Exception as e:
                logger.warning(
                    f"MongoDB unavailable ({e}); falling back to in-memory store."
                )
                try:
                    if cls.client:
                        cls.client.close()
                except Exception:
                    pass
                cls.client = None

        # ----- In-memory fallback -----
        import os
        from app.store.memory_db import MemoryDatabase

        local_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), ".localdb.json"
        )
        cls.db = MemoryDatabase(local_path)
        cls.using_memory = True
        logger.warning(
            "Using in-memory store (no MongoDB configured/reachable). "
            "Data persists to .localdb.json on this machine only."
        )
    
    @classmethod
    async def create_indexes(cls):
        """
        Create database indexes for frequently queried fields.
        
        WHAT ARE INDEXES?
        - Like a book's index page
        - Makes searching MUCH faster
        - Without index: MongoDB scans ALL documents
        - With index: MongoDB jumps directly to matching documents
        
        EXAMPLE:
        Finding user by email without index: Check 10,000 users
        Finding user by email with index: Check 1 user (instant!)
        """
        if cls.db is None:
            return
        
        try:
            # USERS COLLECTION
            # Unique index on email (no two users can have same email)
            await cls.db.users.create_index("email", unique=True)
            await cls.db.users.create_index("created_at")
            
            # RESUMES COLLECTION
            await cls.db.resumes.create_index("user_id")
            await cls.db.resumes.create_index("uploaded_at")
            
            # INTERVIEWS COLLECTION
            await cls.db.interviews.create_index("user_id")
            # Compound index: user_id ascending, created_at descending
            await cls.db.interviews.create_index([("user_id", 1), ("created_at", -1)])
            
            # SESSIONS COLLECTION
            await cls.db.sessions.create_index("interview_id")
            await cls.db.sessions.create_index("user_id")
            
            logger.info(" Database indexes created successfully")
            
        except Exception as e:
            logger.warning(f" Index creation warning: {e}")
            # Don't fail startup if indexes fail (they might already exist)
    
    @classmethod
    async def close_db(cls):
        """
        Closes MongoDB connection.
        Called when application shuts down.
        """
        if cls.client:
            cls.client.close()
            logger.info("MongoDB connection closed")
    
    @classmethod
    def get_db(cls) -> AsyncIOMotorDatabase:
        """
        Returns database instance.
        
        Used in API endpoints through dependency injection.
        Raises error if database not initialized.
        """
        if cls.db is None:
            raise RuntimeError("Database not initialized. Call connect_db() first.")
        return cls.db


# ========== FastAPI Dependency ==========
async def get_database() -> AsyncIOMotorDatabase:
    """
    FastAPI dependency that provides database access to routes.
    
    HOW TO USE IN ROUTES:
    
    @router.get("/users")
    async def get_users(db: AsyncIOMotorDatabase = Depends(get_database)):
        users = await db.users.find().to_list(100)
        return users
    
    FastAPI automatically calls this function and passes 'db' to your route!
    """
    return DatabaseManager.get_db()