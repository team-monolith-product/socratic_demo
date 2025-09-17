# Socratic Tutor

A standalone version of the Proto4 Socratic learning experience. The backend is a FastAPI service that orchestrates Socratic dialogue and multi-dimensional assessment using OpenAI models. The frontend is a lightweight static application that consumes the API.

## Project Structure

```
backend/            # FastAPI application (Railway)
frontend/           # Static assets served via Vercel
scripts/            # Utility scripts (e.g. config generation)
docs/               # Technical, prompt, and deployment documentation
Procfile            # Railway process declaration
vercel.json         # Vercel build configuration
```

## Local Development

1. Create and activate a Python virtual environment.
2. Copy `.env.example` to `.env` and set `OPENAI_API_KEY`.
3. Install backend dependencies and run the API:
   ```bash
   cd socratic
   make install-backend
   make build-frontend   # generates frontend/static/config.js
   make run-backend
   ```
4. Open `frontend/index.html` in a static server (e.g. `python -m http.server 3000`) and interact with the UI. Adjust `frontend/static/config.js` to point at the backend if needed.

## Deployment Overview

- **Backend**: Deployed to Railway using the Dockerfile in `backend/`. Configure environment variables `OPENAI_API_KEY`, `OPENAI_MODEL`, and `ALLOWED_ORIGINS`.
- **Frontend**: Deployed to Vercel as a static site. Set `API_BASE_URL` to the Railway endpoint (`https://<app>.up.railway.app/api/v1`).

Detailed instructions live in `docs/DEPLOYMENT.md`.

## Documentation

Additional materials copied from the original Proto4 project:

- `docs/TECHNICAL_DOCUMENTATION.md`
- `docs/PROMPT_DOCUMENTATION.md`
- `docs/USER_GUIDE.md`

## Next Steps

- Add automated tests for service logic using mocked OpenAI responses.
- Wire logging/monitoring (e.g. structured logging, Sentry).
- Introduce CI workflows (lint/test) under `.github/workflows/`.
