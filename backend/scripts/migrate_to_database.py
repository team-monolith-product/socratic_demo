"""Migration script to move data from JSON files to database."""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add the backend directory to the path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import create_tables, AsyncSessionLocal
from app.models.database_models import Teacher, Session, Student, Message, SessionActivity
from app.services.database_service import DatabaseService


async def migrate_json_to_database():
    """Migrate data from JSON files to database."""
    print("🚀 Starting migration from JSON files to database...")

    # Create tables if they don't exist
    await create_tables()
    print("✅ Database tables created/verified")

    # Initialize services
    db_service = DatabaseService()

    # Paths to JSON files
    data_dir = Path(__file__).parent.parent / "data"
    sessions_file = data_dir / "sessions.json"
    students_file = data_dir / "students.json"

    if not sessions_file.exists():
        print("❌ sessions.json file not found")
        return

    if not students_file.exists():
        print("❌ students.json file not found")
        return

    try:
        # Load JSON data
        with open(sessions_file, 'r', encoding='utf-8') as f:
            sessions_data = json.load(f)

        with open(students_file, 'r', encoding='utf-8') as f:
            students_data = json.load(f)

        print(f"📚 Found {len(sessions_data)} sessions and {sum(len(s) for s in students_data.values())} students")

        # Migrate sessions
        migrated_sessions = 0
        for session_id, session_info in sessions_data.items():
            print(f"🔄 Migrating session: {session_id}")
            success = await db_service.save_session(session_id, session_info)
            if success:
                migrated_sessions += 1
                print(f"✅ Session {session_id} migrated successfully")
            else:
                print(f"❌ Failed to migrate session {session_id}")

        # Migrate students
        migrated_students = 0
        for session_id, session_students in students_data.items():
            if session_students:  # Only if there are students
                print(f"🔄 Migrating {len(session_students)} students for session: {session_id}")
                success = await db_service.save_session_students(session_id, session_students)
                if success:
                    migrated_students += len(session_students)
                    print(f"✅ Students for session {session_id} migrated successfully")
                else:
                    print(f"❌ Failed to migrate students for session {session_id}")

        print(f"🎉 Migration completed!")
        print(f"📊 Summary:")
        print(f"   - Sessions migrated: {migrated_sessions}/{len(sessions_data)}")
        print(f"   - Students migrated: {migrated_students}/{sum(len(s) for s in students_data.values())}")

        # Verify migration
        print("🔍 Verifying migration...")
        stats = await db_service.get_storage_stats()
        print(f"📈 Database contains: {stats['total_sessions']} sessions, {stats['total_students']} students")

        # Create backup of original files
        backup_dir = data_dir / "backup"
        backup_dir.mkdir(exist_ok=True)

        import shutil
        shutil.copy2(sessions_file, backup_dir / f"sessions_backup_{int(asyncio.get_event_loop().time())}.json")
        shutil.copy2(students_file, backup_dir / f"students_backup_{int(asyncio.get_event_loop().time())}.json")
        print(f"💾 Original files backed up to: {backup_dir}")

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise


async def test_database_connection():
    """Test database connection and display current data."""
    print("🔗 Testing database connection...")

    try:
        db_service = DatabaseService()
        stats = await db_service.get_storage_stats()
        print(f"✅ Database connection successful")
        print(f"📊 Current database stats: {stats}")

        # Load and display current sessions
        sessions = await db_service.load_sessions()
        print(f"📚 Found {len(sessions)} sessions in database:")
        for session_id, session_data in sessions.items():
            print(f"   - {session_id}: {session_data['config']['topic']} ({session_data['status']})")

    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        raise


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Database migration tools")
    parser.add_argument("--test", action="store_true", help="Test database connection")
    parser.add_argument("--migrate", action="store_true", help="Migrate JSON data to database")

    args = parser.parse_args()

    if args.test:
        asyncio.run(test_database_connection())
    elif args.migrate:
        asyncio.run(migrate_json_to_database())
    else:
        print("Usage:")
        print("  python migrate_to_database.py --test     # Test database connection")
        print("  python migrate_to_database.py --migrate  # Migrate JSON data to database")