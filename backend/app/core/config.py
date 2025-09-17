"""Application configuration helpers."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import List


class Settings:
    """Runtime configuration sourced from environment variables."""

    def __init__(self) -> None:
        self.openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
        self.openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self._allowed_origins_raw = os.getenv("ALLOWED_ORIGINS", "*")
        self.static_root: str | None = os.getenv("STATIC_ROOT")

    @property
    def allow_origins(self) -> List[str]:
        """Return CORS origins as a list (comma separated env)."""
        raw = self._allowed_origins_raw.strip()
        if not raw or raw == "*":
            # Return specific origins for better CORS handling
            return [
                "http://localhost:3000",
                "http://localhost:8000",
                "http://localhost:8001",
                "https://socratic-nine.vercel.app"
            ]
        return [origin.strip() for origin in raw.split(",") if origin.strip()]

    @property
    def allow_origin_regex(self) -> str | None:
        """Optionally enable regex wildcard for permissive CORS."""
        raw = self._allowed_origins_raw.strip()
        if not raw or raw == "*":
            # Allow all Vercel app domains and localhost
            return r"^https://.*\.vercel\.app$|^http://localhost:\d+$|^https://socratic-nine\.vercel\.app$"
        return None


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings instance."""

    return Settings()
