from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.socratic_chat import router as chat_router
from app.api.teacher_session import router as teacher_router
from app.api.pdf_analysis import router as pdf_router
from app.core.config import get_settings
from app.core.database import create_tables
# Import models to ensure they are registered with Base
from app.models.database_models import Teacher, Session, Student, Message

load_dotenv()

settings = get_settings()

app = FastAPI(
    title="Socratic Tutor API",
    description="Socratic Method AI Learning System",
    version="1.0.0"
)

allow_origin_regex = settings.allow_origin_regex

# Debug CORS settings
print(f"🔧 CORS DEBUG - Allowed origins: {settings.allow_origins}")
print(f"🔧 CORS DEBUG - Origin regex: {allow_origin_regex}")
print(f"🔧 CORS DEBUG - ALLOWED_ORIGINS env: {settings._allowed_origins_raw}")
print(f"💾 Storage mode: Database (PostgreSQL)")
print(f"🗄️ Database URL: {settings.database_url}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Temporarily allow all origins
    allow_origin_regex=".*",  # Allow all origins with regex
    allow_credentials=False,  # Set to False when using allow_origins=["*"]
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)


def _resolve_frontend_dir() -> Path:
    """Return frontend directory path if it exists."""

    if settings.static_root:
        candidate = Path(settings.static_root).resolve()
    else:
        candidate = Path(__file__).resolve().parents[1] / "frontend"
    return candidate


FRONTEND_DIR = _resolve_frontend_dir()

static_dir = FRONTEND_DIR / "static"
pages_dir = FRONTEND_DIR / "pages"

if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

if pages_dir.exists():
    app.mount("/pages", StaticFiles(directory=str(pages_dir)), name="pages")

app.include_router(chat_router, prefix="/api/v1")
app.include_router(teacher_router, prefix="/api/v1")
app.include_router(pdf_router, prefix="/api/v1")


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    try:
        print("🗄️ Initializing database...")

        # First create/verify tables
        await create_tables()
        print("✅ Database tables created/verified successfully")

        # Then run migrations to add any missing columns
        from app.core.migrations import run_migrations
        await run_migrations()

    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        raise  # Crash the app if DB fails - no fallback


@app.get("/")
async def root():
    """Serve index page when bundled with frontend, otherwise return service info."""

    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"service": "socratic", "status": "ok"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/favicon.ico")
async def favicon():
    """Handle favicon requests"""
    favicon_file = FRONTEND_DIR / "static" / "favicon.ico"
    if favicon_file.exists():
        return FileResponse(favicon_file)
    return {"status": "no favicon"}

@app.get("/s/{session_id}")
async def student_session(session_id: str):
    """Redirect to Vercel frontend for student session access"""
    from fastapi.responses import RedirectResponse

    # Redirect to Vercel frontend with session ID
    vercel_url = f"https://socratic-nine.vercel.app/s/{session_id}"
    return RedirectResponse(url=vercel_url, status_code=302)

# OPTIONS 요청 전역 처리 (CORS preflight 대응)
@app.options("/{full_path:path}")
async def options_handler(full_path: str):
    return {}

if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
