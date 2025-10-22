"""
Add conversation_history JSONB column to students table.
Migrates existing messages to JSON format.
"""

from app.core.database import engine
from sqlalchemy import text


async def migrate_add_conversation_history():
    """Add conversation_history column and migrate existing messages."""
    print("🔄 Adding conversation_history column to students table...")

    async with engine.begin() as conn:
        # Add conversation_history column
        await conn.execute(text("""
            ALTER TABLE students
            ADD COLUMN IF NOT EXISTS conversation_history JSON DEFAULT CAST('[]' AS json)
        """))

        print("✅ conversation_history column added")

        # Migrate existing messages to conversation_history
        print("🔄 Migrating existing messages to conversation_history...")

        # Get all students with messages
        result = await conn.execute(text("""
            SELECT DISTINCT student_id
            FROM messages
            ORDER BY student_id
        """))
        student_ids = [row[0] for row in result.fetchall()]

        print(f"📊 Found {len(student_ids)} students with messages")

        # For each student, aggregate messages into JSON
        for student_id in student_ids:
            # Get all messages for this student
            messages_result = await conn.execute(text("""
                SELECT message_type, content, timestamp
                FROM messages
                WHERE student_id = :student_id
                ORDER BY timestamp ASC
            """), {"student_id": student_id})

            messages = []
            for row in messages_result.fetchall():
                messages.append({
                    "role": row[0],  # message_type (user or assistant)
                    "content": row[1]
                })

            if messages:
                # Update student with conversation_history
                import json
                conversation_json = json.dumps(messages)

                await conn.execute(text("""
                    UPDATE students
                    SET conversation_history = CAST(:conversation_history AS json)
                    WHERE id = :student_id
                """), {
                    "student_id": student_id,
                    "conversation_history": conversation_json
                })

                print(f"  ✅ Migrated {len(messages)} messages for student {student_id[:8]}...")

        print(f"✅ Successfully migrated messages to conversation_history")
        print("💡 Note: messages table is kept for backward compatibility but will not be used")
