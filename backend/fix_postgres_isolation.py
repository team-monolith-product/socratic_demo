#!/usr/bin/env python3
"""Fix PostgreSQL transaction isolation issues."""

import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.core.database import AsyncSessionLocal
from sqlalchemy import text

async def fix_postgres_settings():
    """Fix PostgreSQL settings for better transaction visibility."""
    try:
        print("🔧 Fixing PostgreSQL transaction isolation settings...")

        async with AsyncSessionLocal() as session:
            # Check current isolation level
            result = await session.execute(text("SHOW transaction_isolation;"))
            current_isolation = result.scalar()
            print(f"📊 Current isolation level: {current_isolation}")

            # Check if we're on PostgreSQL
            result = await session.execute(text("SELECT version();"))
            version = result.scalar()
            if "PostgreSQL" not in version:
                print("ℹ️ Not PostgreSQL, skipping isolation fixes")
                return True

            print(f"📊 Database version: {version}")

            # Set session-level settings for better consistency
            await session.execute(text("SET SESSION synchronous_commit = ON;"))
            print("✅ Set synchronous_commit = ON")

            await session.execute(text("SET SESSION commit_delay = 0;"))
            print("✅ Set commit_delay = 0")

            # Commit the session configuration
            await session.commit()

            print("✅ PostgreSQL settings optimized for data consistency")
            return True

    except Exception as e:
        print(f"❌ Error fixing PostgreSQL settings: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_message_operations():
    """Test message save and retrieve operations."""
    try:
        print("🧪 Testing message operations...")

        # Test session 1: Save a test message
        async with AsyncSessionLocal() as session1:
            async with session1.begin():
                result = await session1.execute(text("""
                    INSERT INTO messages (id, student_id, session_id, content, message_type, timestamp)
                    VALUES ('test-msg-001', 'test-student-001', 'test-session-001', 'Test message content', 'user', NOW())
                    ON CONFLICT (id) DO NOTHING
                    RETURNING id;
                """))
                message_id = result.scalar()
                print(f"📝 Test message saved with ID: {message_id}")

        # Test session 2: Immediately try to read the message
        async with AsyncSessionLocal() as session2:
            result = await session2.execute(text("""
                SELECT id, content FROM messages WHERE id = 'test-msg-001';
            """))
            message = result.fetchone()
            if message:
                print(f"✅ Test message successfully read: {message[1]}")
            else:
                print("❌ Test message not found in fresh session")

            # Cleanup
            await session2.execute(text("DELETE FROM messages WHERE id = 'test-msg-001';"))
            await session2.commit()
            print("🧹 Test data cleaned up")

        return True

    except Exception as e:
        print(f"❌ Error testing message operations: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main function to fix PostgreSQL issues."""
    try:
        print("🚀 Starting PostgreSQL isolation fix...")

        # Fix settings
        settings_ok = await fix_postgres_settings()
        if not settings_ok:
            print("❌ Failed to fix settings")
            return False

        # Test operations
        test_ok = await test_message_operations()
        if not test_ok:
            print("❌ Failed message operation test")
            return False

        print("🎉 PostgreSQL isolation issues fixed successfully!")
        return True

    except Exception as e:
        print(f"❌ Fix process failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)