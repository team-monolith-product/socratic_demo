FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend /app/backend

EXPOSE 8000

# Use a Python script to handle port properly
CMD python -c "import os; import subprocess; port = os.environ.get('PORT', '8000'); subprocess.run(['uvicorn', 'backend.main:app', '--host', '0.0.0.0', '--port', port])"