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
        self.database_url: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./socratic.db")
        self.frontend_url: str = os.getenv("FRONTEND_URL", "https://socratic-nine.vercel.app")

        # PDF 처리 설정 (파일 크기는 10MB로 완화)
        self.max_pdf_size_mb: int = int(os.getenv("MAX_PDF_SIZE_MB", "10"))  # 10MB로 복원
        self.max_pdf_pages: int = int(os.getenv("MAX_PDF_PAGES", "30"))  # 30 페이지 유지
        self.max_text_length: int = int(os.getenv("MAX_TEXT_LENGTH", "5000"))  # 5000자 유지
        self.allowed_pdf_types: List[str] = [".pdf"]

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
