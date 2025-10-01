"""Database connection and session management."""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import get_settings

settings = get_settings()

# Create async engine with database-specific settings
if settings.database_url.startswith("sqlite"):
    # SQLite configuration
    engine = create_async_engine(
        settings.database_url,
        echo=False,  # Set to True for SQL debugging
        future=True,
    )
else:
    # PostgreSQL configuration
    engine = create_async_engine(
        settings.database_url,
        echo=False,  # Set to True for SQL debugging
        future=True,
        pool_pre_ping=True,
        pool_recycle=300,  # Recycle connections every 5 minutes
        pool_size=10,
        max_overflow=20,
        # PostgreSQL specific settings for transaction isolation
        connect_args={
            "server_settings": {
                "jit": "off",  # Disable JIT for better performance on small queries
            }
        }
    )

# Create async session factory with proper transaction settings
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=True,  # Automatically flush before queries
    autocommit=False,  # Use transactions explicitly
)

# Create declarative base
Base = declarative_base()


async def get_db() -> AsyncSession:
    """Get database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def create_tables():
    """Create all tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables():
    """Drop all tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)