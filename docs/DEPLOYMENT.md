# Deployment Guide

This service is designed for a split deployment: the FastAPI backend runs on Railway and the static frontend runs on Vercel.

## Railway (Backend)

1. Create a new Railway service and select the "Deploy from GitHub" option targeting this repository.
2. In the deployment settings choose the branch (e.g. `main`) and keep the Dockerfile buildpack (Railway will detect `backend/Dockerfile`).
3. Set environment variables under **Variables**:
   - `OPENAI_API_KEY` – required OpenAI API token.
   - `OPENAI_MODEL` – optional, defaults to `gpt-4o-mini`.
   - `ALLOWED_ORIGINS` – comma separated list of domains allowed by CORS (e.g. `https://socratic.vercel.app`).
4. Deploy the service and verify logs. Railway exposes a default domain like `https://<app>.up.railway.app` – note this URL for the frontend configuration.
5. Optional: add a custom domain in Railway and update DNS records accordingly.
6. Validate the deployment by requesting `GET /health` and `GET /api/v1/topic/validate` with a sample payload.

## Vercel (Frontend)

1. Import the repository into Vercel and keep the project root at the repository root.
2. Under **Build & Output Settings** set:
   - Framework Preset: `Other` (or `Static Site`).
   - Build Command: `bash scripts/generate-config.sh`.
   - Output Directory: `frontend`.
3. Define the environment variable `API_BASE_URL` in Vercel, pointing to the deployed Railway endpoint (`https://<app>.up.railway.app/api/v1`).
4. Deploy the project. The build command generates `frontend/static/config.js` so the application knows which API base URL to call.
5. After deployment, verify the UI loads and that chats reach the backend (watch the Railway logs for confirmation).
6. Configure a custom domain on Vercel if desired, and update `ALLOWED_ORIGINS` on Railway when additional domains are added.

## Post-deployment Smoke Test

- Visit the Vercel URL, enter a topic, and confirm:
  1. Topic validation succeeds.
  2. Initial message loads from the backend.
  3. Socratic chat exchanges AI + assessment responses.
- Monitor both Railway and Vercel logs for errors.
- Update documentation with any environment-specific instructions discovered during deployment.
