"""
Migrate messages table to store conversation as JSON array.
- Remove: content, message_type, extra_data columns
- Add: conversation_data JSON column
- Add: unique constraint on student_id
"""

from app.core.database import engine
from sqlalchemy import text


async def migrate_messages_to_json():
    """Alter messages table schema to store conversation as JSON."""
    print("🔄 Migrating messages table to JSON storage format...")

    async with engine.begin() as conn:
        # Remove old columns
        print("  📝 Removing old columns (content, message_type, extra_data)...")
        await conn.execute(text("""
            ALTER TABLE messages
            DROP COLUMN IF EXISTS content,
            DROP COLUMN IF EXISTS message_type,
            DROP COLUMN IF EXISTS extra_data
        """))

        # Add conversation_data column
        print("  📝 Adding conversation_data JSON column...")
        await conn.execute(text("""
            ALTER TABLE messages
            ADD COLUMN IF NOT EXISTS conversation_data JSON DEFAULT CAST('[]' AS json)
        """))

        # Add unique constraint on student_id
        print("  📝 Adding unique constraint on student_id...")
        await conn.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_messages_student_id_unique
            ON messages (student_id)
        """))

        print("✅ Messages table migration completed")
        print("   - Old columns removed: content, message_type, extra_data")
        print("   - New column added: conversation_data (JSON)")
        print("   - Constraint added: student_id UNIQUE")
