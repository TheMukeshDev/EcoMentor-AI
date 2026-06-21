# EcoMentor AI

AI-powered platform that helps users track, understand, and reduce their carbon footprint through personalized insights, challenges, and community engagement.

---

## Table of Contents

- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [AI Features](#ai-features)
- [Deployment](#deployment)
- [Testing](#testing)
- [Tech Stack](#tech-stack)

---

## Quick Start

### Prerequisites

| Tool | Version | Purpose |
|---|---|---|
| Python | 3.12+ | Backend runtime |
| Node.js | 20+ | Frontend build tooling |
| Docker | Latest | Firestore emulator |
| [gcloud CLI](https://cloud.google.com/sdk/docs/install) | Latest | Firestore emulator, deployment |

### Option 1: Docker Compose (easiest)

```bash
docker-compose up
# Backend:  http://localhost:5000
# Frontend: http://localhost:5173
```

### Option 2: Manual Setup

**1. Backend**

```bash
cd backend
python -m venv .venv

# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

Edit `backend/.env` — set at minimum:
```
GEMINI_API_KEY=your-gemini-api-key
SECRET_KEY=some-random-secret
```

**2. Start Firestore Emulator**

Via gcloud CLI (requires Docker or Java):
```bash
gcloud beta emulators firestore start --host-port=localhost:8080
```

Via Docker (no gcloud needed):
```bash
docker run -p 8080:8080 \
  gcr.io/google.com/cloudsdktool/google-cloud-cli:emulators \
  gcloud beta emulators firestore start --host-port=0.0.0.0:8080 --project=ecomentor-dev
```

**3. Run Backend**

```bash
flask run
# → http://localhost:5000
```

**4. Frontend**

```bash
cd frontend
cp .env.example .env    # Fill in your Firebase project config
npm install
npm run dev
# → http://localhost:5173
```

Frontend dev server proxies `/api/*` to the backend (configured in `frontend/vite.config.js`).

**5. Verify**

```bash
curl http://localhost:5000/health
# → {"status": "healthy"}
```

---

## Architecture

**Backend**: Flask API with Blueprints → Services → Repositories pattern. Hosted on Cloud Run.

**Frontend**: Vanilla JS SPA served via Firebase Hosting. Firebase rewrites `/api/*` to Cloud Run.

See [docs/architecture.md](docs/architecture.md) for detailed layer rules, request flow, and endpoint reference.

---

## AI Features

EcoMentor uses **Google Gemini 2.0 Flash** for personalized recommendations, weekly reports, daily missions, conversational chat, and what-if analysis. Every prompt is enriched with user data (level, streak, carbon scores) for context-aware responses.

See [docs/ai.md](docs/ai.md) for prompt templates, caching strategy, and security details.

---

## Deployment

Firebase Hosting serves the frontend. `/api/*` requests auto-forward to Cloud Run — no CORS needed in production.

### Prerequisites

1. Google Cloud project with billing enabled
2. Firestore (Native mode) in your project
3. Firebase project linked to your Google Cloud project
4. [gcloud CLI](https://cloud.google.com/sdk/docs/install) + [Firebase CLI](https://firebase.google.com/docs/cli) installed

### Backend (Cloud Run)

```bash
gcloud config set project YOUR_PROJECT_ID
gcloud builds submit backend/ --tag gcr.io/YOUR_PROJECT_ID/ecomentor-api
gcloud run deploy ecomentor-api --image gcr.io/YOUR_PROJECT_ID/ecomentor-api \
  --region us-central1 --platform managed --allow-unauthenticated \
  --set-env-vars "APP_ENV=production,GCP_PROJECT_ID=YOUR_PROJECT_ID"
```

Secrets (`SECRET_KEY`, `GEMINI_API_KEY`) go in Secret Manager, not env vars.

### Frontend (Firebase Hosting)

```bash
cd frontend
npm ci
npm run build
npm run deploy:gen-config        # Generates firebase.json from .env
cd .. && npx firebase-tools deploy --only hosting
```

Or: `cd frontend && npm run deploy`

**`.env.production`** (create before building):

```
VITE_FIREBASE_API_KEY=your-api-key
VITE_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your-project-id
VITE_FIREBASE_STORAGE_BUCKET=your-project.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=your-sender-id
VITE_FIREBASE_APP_ID=your-app-id
HOSTING_SERVICE_ID=ecomentor-api
HOSTING_REGION=us-central1
```

> `firebase.json` is auto-generated from `HOSTING_*` vars — no manual editing needed.

### CI/CD

Push to `main` triggers `.github/workflows/deploy.yml`: builds Cloud Run + Firebase Hosting. Enable by adding `GCP_SA_KEY` secret in GitHub.

### Troubleshooting

| Symptom | Fix |
|---|---|
| Backend 503 | Check `GEMINI_API_KEY` in Secret Manager |
| Can't log in | Verify `frontend/.env` Firebase values |
| API calls fail | Check `HOSTING_SERVICE_ID` / `HOSTING_REGION` |
| Firestore denied | Review `backend/firestore.rules` |

---

## Testing

```bash
# Backend
pytest                          # All tests
pytest --cov=app                # With coverage

# Frontend
cd frontend && npx vitest run   # All tests
```

---

## Tech Stack

| Component | Technology |
|---|---|
| Backend | Python 3.12 · Flask 3.1 · Gunicorn |
| Database | Firestore (Native mode) |
| Auth | JWT (PyJWT) |
| Infra | Cloud Run · Firebase Hosting · Secret Manager |
| CI | GitHub Actions · Ruff · pytest |
| Frontend | Vanilla JS · CSS custom properties · Vite |
