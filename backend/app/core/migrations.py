"""Database migration utilities."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import AsyncSessionLocal


async def _detect_database_type(session: AsyncSession) -> str:
    """Detect the database type (sqlite or postgresql)."""
    try:
        # Try PostgreSQL specific query
        await session.execute(text("SELECT version();"))
        return "postgresql"
    except:
        # If PostgreSQL query fails, assume SQLite
        return "sqlite"


async def drop_session_activities_table():
    """Drop the session_activities table if it exists."""
    async with AsyncSessionLocal() as session:
        try:
            db_type = await _detect_database_type(session)

            if db_type == "postgresql":
                # PostgreSQL: use information_schema
                check_query = text("""
                    SELECT table_name FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_name = 'session_activities';
                """)
            else:
                # SQLite: use sqlite_master
                check_query = text("""
                    SELECT name FROM sqlite_master
                    WHERE type='table' AND name='session_activities';
                """)

            result = await session.execute(check_query)
            table_exists = result.fetchone() is not None

            if table_exists:
                if db_type == "postgresql":
                    drop_query = text("DROP TABLE IF EXISTS session_activities CASCADE;")
                else:
                    drop_query = text("DROP TABLE IF EXISTS session_activities;")

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
            db_type = await _detect_database_type(session)

            # First check if sessions table exists
            if db_type == "postgresql":
                table_check_query = text("""
                    SELECT table_name FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_name = 'sessions';
                """)
            else:
                table_check_query = text("""
                    SELECT name FROM sqlite_master
                    WHERE type='table' AND name='sessions';
                """)

            table_result = await session.execute(table_check_query)
            table_exists = table_result.fetchone() is not None

            if not table_exists:
                print("ℹ️ sessions table does not exist yet, skipping column addition")
                return

            # Check if column exists
            if db_type == "postgresql":
                check_query = text("""
                    SELECT column_name FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = 'sessions' AND column_name = 'deleted_at';
                """)
                result = await session.execute(check_query)
                column_exists = result.fetchone() is not None
            else:
                check_query = text("PRAGMA table_info(sessions);")
                result = await session.execute(check_query)
                columns = result.fetchall()
                column_exists = any(col[1] == 'deleted_at' for col in columns)

            if not column_exists:
                if db_type == "postgresql":
                    add_column_query = text("ALTER TABLE sessions ADD COLUMN deleted_at TIMESTAMP WITH TIME ZONE;")
                else:
                    add_column_query = text("ALTER TABLE sessions ADD COLUMN deleted_at DATETIME;")

                await session.execute(add_column_query)
                await session.commit()
                print("✅ deleted_at column added to sessions table")
            else:
                print("ℹ️ deleted_at column already exists in sessions table")

        except Exception as e:
            await session.rollback()
            print(f"❌ Error adding deleted_at column: {e}")
            raise


async def drop_score_records_table():
    """Drop the score_records table if it exists."""
    async with AsyncSessionLocal() as session:
        try:
            db_type = await _detect_database_type(session)

            if db_type == "postgresql":
                # PostgreSQL: use information_schema
                check_query = text("""
                    SELECT table_name FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_name = 'score_records';
                """)
            else:
                # SQLite: use sqlite_master
                check_query = text("""
                    SELECT name FROM sqlite_master
                    WHERE type='table' AND name='score_records';
                """)

            result = await session.execute(check_query)
            table_exists = result.fetchone() is not None

            if table_exists:
                if db_type == "postgresql":
                    drop_query = text("DROP TABLE IF EXISTS score_records CASCADE;")
                else:
                    drop_query = text("DROP TABLE IF EXISTS score_records;")

                await session.execute(drop_query)
                await session.commit()
                print("✅ score_records table dropped successfully")
            else:
                print("ℹ️ score_records table does not exist")

        except Exception as e:
            await session.rollback()
            print(f"❌ Error dropping score_records table: {e}")
            raise


async def create_scores_table():
    """Create the scores table for tracking student response evaluations."""
    async with AsyncSessionLocal() as session:
        try:
            db_type = await _detect_database_type(session)

            # Check if scores table already exists
            if db_type == "postgresql":
                check_query = text("""
                    SELECT table_name FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_name = 'scores';
                """)
            else:
                check_query = text("""
                    SELECT name FROM sqlite_master
                    WHERE type='table' AND name='scores';
                """)

            result = await session.execute(check_query)
            table_exists = result.fetchone() is not None

            if not table_exists:
                if db_type == "postgresql":
                    create_query = text("""
                        CREATE TABLE scores (
                            id VARCHAR(36) PRIMARY KEY,
                            message_id VARCHAR(36) NOT NULL,
                            student_id VARCHAR(36) NOT NULL,
                            session_id VARCHAR(20) NOT NULL,
                            overall_score INTEGER NOT NULL,
                            depth_score INTEGER NOT NULL,
                            breadth_score INTEGER NOT NULL,
                            application_score INTEGER NOT NULL,
                            metacognition_score INTEGER NOT NULL,
                            engagement_score INTEGER NOT NULL,
                            evaluation_data JSON,
                            is_completed BOOLEAN DEFAULT FALSE,
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                            FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE,
                            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
                            FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
                        );

                        CREATE INDEX idx_scores_message_id ON scores(message_id);
                        CREATE INDEX idx_scores_student_id ON scores(student_id);
                        CREATE INDEX idx_scores_session_id ON scores(session_id);
                        CREATE INDEX idx_scores_created_at ON scores(created_at);
                    """)
                else:
                    # Create table first
                    create_table_query = text("""
                        CREATE TABLE scores (
                            id TEXT PRIMARY KEY,
                            message_id TEXT NOT NULL,
                            student_id TEXT NOT NULL,
                            session_id TEXT NOT NULL,
                            overall_score INTEGER NOT NULL,
                            depth_score INTEGER NOT NULL,
                            breadth_score INTEGER NOT NULL,
                            application_score INTEGER NOT NULL,
                            metacognition_score INTEGER NOT NULL,
                            engagement_score INTEGER NOT NULL,
                            evaluation_data TEXT,
                            is_completed INTEGER DEFAULT 0,
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE,
                            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
                            FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
                        )
                    """)

                    await session.execute(create_table_query)

                    # Create indexes separately for SQLite
                    index_queries = [
                        "CREATE INDEX idx_scores_message_id ON scores(message_id)",
                        "CREATE INDEX idx_scores_student_id ON scores(student_id)",
                        "CREATE INDEX idx_scores_session_id ON scores(session_id)",
                        "CREATE INDEX idx_scores_created_at ON scores(created_at)"
                    ]

                    for index_query in index_queries:
                        await session.execute(text(index_query))
                await session.commit()
                print("✅ scores table created successfully with indexes")
            else:
                print("ℹ️ scores table already exists")

        except Exception as e:
            await session.rollback()
            print(f"❌ Error creating scores table: {e}")
            raise


async def add_student_token_column():
    """Add token column to students table."""
    async with AsyncSessionLocal() as session:
        try:
            db_type = await _detect_database_type(session)

            # Check if token column already exists
            if db_type == "postgresql":
                check_query = text("""
                    SELECT column_name FROM information_schema.columns
                    WHERE table_name = 'students' AND column_name = 'token';
                """)
            else:
                # SQLite
                check_query = text("PRAGMA table_info(students);")

            result = await session.execute(check_query)

            if db_type == "postgresql":
                existing_columns = [row[0] for row in result.fetchall()]
                token_exists = 'token' in existing_columns
            else:
                # SQLite PRAGMA returns (cid, name, type, notnull, dflt_value, pk)
                existing_columns = [row[1] for row in result.fetchall()]
                token_exists = 'token' in existing_columns

            if not token_exists:
                print("➕ Adding token column to students table...")

                # Add token column
                alter_query = text("ALTER TABLE students ADD COLUMN token VARCHAR(50);")
                await session.execute(alter_query)

                # Add index on token column
                if db_type == "postgresql":
                    index_query = text("CREATE INDEX ix_students_token ON students (token);")
                else:
                    index_query = text("CREATE INDEX ix_students_token ON students (token);")

                await session.execute(index_query)
                await session.commit()
                print("✅ Token column added to students table")
            else:
                print("ℹ️ Token column already exists in students table")

        except Exception as e:
            await session.rollback()
            print(f"❌ Failed to add token column: {e}")
            raise


async def run_migrations():
    """Run all pending migrations."""
    print("🔄 Running database migrations...")
    await drop_session_activities_table()
    await drop_score_records_table()
    await add_deleted_at_column()
    await create_scores_table()
    await add_student_token_column()
    print("✅ Migrations completed")