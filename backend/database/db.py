import os
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

# Get Database URL from environment, default to local SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./pr_dashboard.db")

# Parse and construct corresponding sync and async URLs
if DATABASE_URL.startswith("postgresql+asyncpg://"):
    ASYNC_DATABASE_URL = DATABASE_URL
    SYNC_DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
elif DATABASE_URL.startswith("postgresql://"):
    SYNC_DATABASE_URL = DATABASE_URL
    ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
elif DATABASE_URL.startswith("sqlite+aiosqlite://"):
    ASYNC_DATABASE_URL = DATABASE_URL
    SYNC_DATABASE_URL = DATABASE_URL.replace("sqlite+aiosqlite://", "sqlite://")
else:
    # Standard SQLite fallback
    SYNC_DATABASE_URL = DATABASE_URL
    # Ensure URL is in format sqlite:///...
    if DATABASE_URL.startswith("sqlite:///"):
        ASYNC_DATABASE_URL = DATABASE_URL.replace("sqlite:///", "sqlite+aiosqlite:///")
    else:
        ASYNC_DATABASE_URL = "sqlite+aiosqlite:///./pr_dashboard.db"

# Connection Pooling Configuration
is_postgresql = "postgresql" in SYNC_DATABASE_URL

# Sync Engine and Sessionmaker
if is_postgresql:
    engine = create_engine(
        SYNC_DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_timeout=30,
        pool_recycle=1800,
        pool_pre_ping=True
    )
else:
    engine = create_engine(
        SYNC_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Async Engine and Sessionmaker (preserve async SQLAlchemy architecture)
if is_postgresql:
    async_engine = create_async_engine(
        ASYNC_DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_timeout=30,
        pool_recycle=1800,
        pool_pre_ping=True
    )
else:
    async_engine = create_async_engine(
        ASYNC_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )

AsyncSessionLocal = sessionmaker(
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    bind=async_engine
)

Base = declarative_base()

def init_db():
    """Synchronous database initialization"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Sync database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_async_db():
    """Async database session dependency"""
    async with AsyncSessionLocal() as db:
        try:
            yield db
        finally:
            await db.close()

async def check_db_health() -> dict:
    """Check both sync and async database connection health"""
    health = {"status": "healthy", "details": {}}
    
    # 1. Check sync connection
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        health["details"]["sync_connection"] = "Connected"
    except Exception as e:
        health["status"] = "unhealthy"
        health["details"]["sync_connection"] = f"Error: {str(e)}"
        
    # 2. Check async connection
    try:
        async with async_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        health["details"]["async_connection"] = "Connected"
    except Exception as e:
        health["status"] = "unhealthy"
        health["details"]["async_connection"] = f"Error: {str(e)}"
        
    return health