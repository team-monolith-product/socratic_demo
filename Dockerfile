FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend /app/backend
COPY start.sh /app/start.sh

RUN chmod +x /app/start.sh

EXPOSE 8000

CMD ["/app/start.sh"]