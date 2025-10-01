#!/usr/bin/env python3
"""Check database health and fix common issues."""

import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.core.migrations import check_database_health
from app.core.database import create_tables, AsyncSessionLocal
from app.models.database_models import Base
from sqlalchemy import text

async def main():
    """Check database health and fix issues."""
    try:
        print("🏥 Running database health check...")

        # Check basic health
        health_ok = await check_database_health()

        if not health_ok:
            print("❌ Basic health check failed")
            return False

        # Try to create tables if they don't exist
        print("🔨 Ensuring all tables exist...")
        await create_tables()
        print("✅ Tables created/verified")

        # Test message operations
        print("💬 Testing message table operations...")
        async with AsyncSessionLocal() as session:
            # Test if we can query messages table
            result = await session.execute(text("SELECT COUNT(*) FROM messages;"))
            count = result.scalar()
            print(f"✅ Messages table has {count} records")

            # Test if we can query students table
            result = await session.execute(text("SELECT COUNT(*) FROM students;"))
            count = result.scalar()
            print(f"✅ Students table has {count} records")

            # Test if we can query sessions table
            result = await session.execute(text("SELECT COUNT(*) FROM sessions;"))
            count = result.scalar()
            print(f"✅ Sessions table has {count} records")

        print("🎉 Database health check completed successfully!")
        return True

    except Exception as e:
        print(f"❌ Database health check failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)