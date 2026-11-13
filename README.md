# StoreLens

Multimodal inventory onboarding and synchronization platform for retail stores, built with FastAPI, React, Vite, Tailwind CSS, and the Google GenAI SDK (`gemini-3.8-flash`).

---

## Architecture

- **Backend (`/backend`)**: FastAPI server using `from google import genai`. Persists inventory to a local Firestore-modeled JSON file (`store_catalog.json`).
- **Frontend (`/frontend`)**: React + Vite application styled with Anomaly Rune UI semantic tokens (`--v2-*`) in a monochrome black and white palette.

---

## Endpoints

1. `POST /api/onboard-video`: Accepts an uploaded `.mp4` or `.webm` shelf walkthrough video. Extracts visible retail packaging and aligns spoken prices by timestamp. Extracts full packaging frames via FFmpeg and OpenCV with letterboxed studio padding.
2. `POST /api/voice-update`: Accepts merchant voice audio or text transcripts. Uses inline audio bytes to match SKU, action (`DECREMENT`, `INCREMENT`, `MARK_SOLD`), and quantity against the current catalog.
3. `GET /api/catalog`: Returns live inventory with optional `?q=` search and `?category=` filters.
4. `POST /api/reset`: Resets catalog to empty (`seed=false`) or loads 6 pre-recorded sample items (`seed=true`).

---

## Setup & Running

### Prerequisites
- Python 3.10+ (Python 3.11 recommended)
- Node.js 18+ and npm
- FFmpeg

### Quick Start
```bash
chmod +x ./start.sh
./start.sh
```

### Backend (Manual)
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
Runs on `http://localhost:8000`.

### Frontend (Manual)
```bash
cd frontend
npm install
npm run dev
```
Runs on `http://localhost:5173`.

---

## Design System

The UI uses a strict monochrome design system modeled after Anomaly Rune UI (`github.com/anomalyco/rune` / `@opencode/ui`):
- `--v2-bg-base`: `#09090b`
- `--v2-bg-surface`: `#121214`
- `--v2-bg-control`: `#1c1c1f`
- `--v2-border-subtle`: `#27272a`
- `--v2-border-focus`: `#fafafa`
- Typography: `Inter` for controls, `JetBrains Mono` with `tabular-nums` for prices, timestamps, SKU IDs, and quantities.
