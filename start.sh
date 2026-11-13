#!/usr/bin/env bash
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

echo "Starting StoreLens AI..."

# Free ports if previously bound
fuser -k 8000/tcp 2>/dev/null || true
fuser -k 5173/tcp 2>/dev/null || true

# Activate Python virtual environment
if [ -f "backend/venv/bin/activate" ]; then
    source backend/venv/bin/activate
fi

# Start FastAPI backend
(cd backend && python3 -m uvicorn main:app --host 0.0.0.0 --port 8000) &
BACKEND_PID=$!

# Start Vite frontend
npm run dev --prefix frontend -- --host 0.0.0.0 --port 5173 &
FRONTEND_PID=$!

echo ""
echo "============================================="
echo " StoreLens AI is running:"
echo "   Frontend : http://localhost:5173"
echo "   Backend  : http://localhost:8000"
echo "   API Docs : http://localhost:8000/docs"
echo "============================================="
echo ""

cleanup() {
    echo "Stopping servers..."
    kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

wait
