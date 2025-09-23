#!/usr/bin/env python3
"""Run database migrations."""

import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.core.migrations import run_migrations

async def main():
    """Run all migrations."""
    try:
        await run_migrations()
        print("🎉 All migrations completed successfully!")
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())