"""Database migration utilities."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import AsyncSessionLocal


async def drop_session_activities_table():
    """Drop the session_activities table if it exists."""
    async with AsyncSessionLocal() as session:
        try:
            # Check if table exists first
            check_query = text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = 'session_activities'
                );
            """)
            result = await session.execute(check_query)
            table_exists = result.scalar()

            if table_exists:
                # Drop the table
                drop_query = text("DROP TABLE IF EXISTS session_activities CASCADE;")
                await session.execute(drop_query)
                await session.commit()
                print("✅ session_activities table dropped successfully")
            else:
                print("ℹ️ session_activities table does not exist")

        except Exception as e:
            await session.rollback()
            print(f"❌ Error dropping session_activities table: {e}")
            raise


async def run_migrations():
    """Run all pending migrations."""
    print("🔄 Running database migrations...")
    await drop_session_activities_table()
    print("✅ Migrations completed")