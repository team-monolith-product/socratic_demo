#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STATIC_DIR="${ROOT_DIR}/frontend/static"
mkdir -p "${STATIC_DIR}"

# Debug environment variables
echo "=== Environment Variables Debug ==="
echo "API_BASE_URL from env: ${API_BASE_URL:-NOT_SET}"
echo "VERCEL: ${VERCEL:-NOT_SET}"
echo "VERCEL_ENV: ${VERCEL_ENV:-NOT_SET}"
echo "==================================="

# Use environment variable or fallback to Railway URL for production
if [ "$VERCEL_ENV" = "production" ]; then
    API_BASE_URL="${API_BASE_URL:-https://web-production-7b060.up.railway.app/api/v1}"
else
    API_BASE_URL="${API_BASE_URL:-/api/v1}"
fi

cat > "${STATIC_DIR}/config.js" <<CONFIG
// Generated at build time: $(date)
// Environment: ${VERCEL_ENV:-local}
// API_BASE_URL: ${API_BASE_URL}
window.__API_BASE__ = "${API_BASE_URL}";
CONFIG

echo "Generated frontend/static/config.js with API_BASE_URL=${API_BASE_URL}"
echo "Config file contents:"
cat "${STATIC_DIR}/config.js"
