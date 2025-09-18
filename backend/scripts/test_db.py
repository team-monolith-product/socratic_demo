"""Simple database test script"""

import asyncio
import sys
from pathlib import Path

# Add the backend directory to the path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import create_tables, engine, AsyncSessionLocal
from app.models.database_models import Base
from sqlalchemy import text

async def test_database():
    print("🔍 Testing database setup...")

    try:
        print(f"🗄️ Database URL: {engine.url}")

        # Try to create tables
        print("🔨 Creating tables...")
        await create_tables()
        print("✅ create_tables() completed")

        # Check if tables exist
        async with engine.begin() as conn:
            result = await conn.run_sync(lambda conn: conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall())
            tables = [row[0] for row in result]
            print(f"📋 Tables found: {tables}")

        if not tables:
            print("⚠️ No tables found, trying manual creation...")
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
                print("✅ Manual table creation completed")

                # Check again
                result = await conn.run_sync(lambda conn: conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall())
                tables = [row[0] for row in result]
                print(f"📋 Tables after manual creation: {tables}")

        # Test session creation
        async with AsyncSessionLocal() as session:
            print("✅ Database session created successfully")

    except Exception as e:
        print(f"❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_database())