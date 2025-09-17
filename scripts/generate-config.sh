#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STATIC_DIR="${ROOT_DIR}/frontend/static"
mkdir -p "${STATIC_DIR}"

API_BASE_URL="${API_BASE_URL:-/api/v1}"

cat > "${STATIC_DIR}/config.js" <<CONFIG
window.__API_BASE__ = "${API_BASE_URL}";
CONFIG

echo "Generated frontend/static/config.js with API_BASE_URL=${API_BASE_URL}"
