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


async def add_deleted_at_column():
    """Add deleted_at column to sessions table if it doesn't exist."""
    async with AsyncSessionLocal() as session:
        try:
            # Check if column exists first
            check_query = text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns
                    WHERE table_schema = 'public'
                    AND table_name = 'sessions'
                    AND column_name = 'deleted_at'
                );
            """)
            result = await session.execute(check_query)
            column_exists = result.scalar()

            if not column_exists:
                # Add the column
                add_column_query = text("ALTER TABLE sessions ADD COLUMN deleted_at TIMESTAMP WITH TIME ZONE;")
                await session.execute(add_column_query)
                await session.commit()
                print("✅ deleted_at column added to sessions table")
            else:
                print("ℹ️ deleted_at column already exists in sessions table")

        except Exception as e:
            await session.rollback()
            print(f"❌ Error adding deleted_at column: {e}")
            raise


async def run_migrations():
    """Run all pending migrations."""
    print("🔄 Running database migrations...")
    await drop_session_activities_table()
    await add_deleted_at_column()
    print("✅ Migrations completed")