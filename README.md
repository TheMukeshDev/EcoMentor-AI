# EcoMentor AI

AI-powered platform that helps users track, understand, and reduce their carbon footprint through personalized insights, challenges, and community engagement.

## Architecture

```
ecomentor-ai/
├── backend/          Flask API (Cloud Run)
├── frontend/         HTML/CSS/JS SPA (Firebase Hosting)
└── docs/             Architecture & standards
```

### Backend (Flask)

| Layer | Responsibility |
|---|---|
| **Blueprints** | Thin route handlers — parse request, delegate to service, return JSON |
| **Services** | All business logic — orchestrates repositories, enforces rules |
| **Repositories** | Firestore queries — one class per entity, zero business logic |
| **Models** | Data shapes (dataclasses) — contract between layers |
| **Middleware** | JWT verification, CSRF protection |
| **Utils** | Error classes, response builders, validators, rate limiter, secrets |

#### API Endpoints

| Blueprint | Prefix | Routes |
|---|---|---|
| Auth | `/api/auth` | register, login, get_profile, update_profile |
| Dashboard | `/api/dashboard` | get_summary, get_history, get_stats |
| Activities | `/api/activities` | list, log, get, delete |
| AI | `/api/ai` | get_recommendations, get_insights, chat |
| Leaderboard | `/api/leaderboard` | global, friends |

### Frontend

Vanilla JS SPA served via Firebase Hosting. Firebase rewrites `/api/*` to Cloud Run — no CORS needed in production.

### Deployment

```
GitHub Actions → Build → Cloud Run (Flask) + Firebase Hosting (SPA)
                                       ↕
                                  Firestore
```

## Quick Start

### Prerequisites

- Python 3.12+
- [Firestore emulator](https://cloud.google.com/firestore/docs/emulator)

### Setup

```bash
# Clone and enter backend
cd backend

# Create environment
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env

# Start Firestore emulator (separate terminal)
gcloud beta emulators firestore start --host-port=localhost:8080

# Run
flask run
```

### Verify

```bash
curl http://localhost:5000/health
# → {"status": "healthy"}
```

## Testing

```bash
pytest                    # All tests
pytest -m unit            # Unit tests only
pytest -m integration     # Integration tests only
pytest --cov=app          # With coverage
```

Tests use mocked repositories and services — no Firestore emulator required.

### Test structure

```
tests/
├── conftest.py               # Session-scoped app, mock repo fixtures, pre-wired services
├── unit/
│   ├── test_services/        # Service logic tests (carbon calc, auth, activity flows)
│   └── test_repositories/    # Query builders & collection names
└── integration/
    ├── test_health.py
    ├── test_auth_routes.py
    └── test_blueprint_registration.py
```

## Configuration

Three environment classes in `app/config.py`:

| Class | Env | Firestore | CORS |
|---|---|---|---|
| `DevelopmentConfig` | `development` | Emulator | `localhost:*` |
| `TestingConfig` | `testing` | Emulator (mocked) | `*` |
| `ProductionConfig` | `production` | Production | Configurable |

Set via `APP_ENV` env var. Secrets managed through Google Secret Manager in production.

## Environment Variables

See `.env.example` for all options:

| Variable | Default | Description |
|---|---|---|
| `APP_ENV` | `development` | Runtime environment |
| `SECRET_KEY` | — | Flask signing key |
| `GCP_PROJECT_ID` | `ecomentor-dev` | GCP project |
| `FIRESTORE_EMULATOR_HOST` | — | Emulator host:port |
| `CORS_ORIGINS` | — | Allowed origins (comma-separated) |
| `RATE_LIMIT_ENABLED` | `true` | Enable rate limiting |
| `RATE_LIMIT_DEFAULT` | `100;3600` | Default capacity;refill/sec |
| `RATE_LIMIT_STRICT` | `10;60` | Strict capacity;refill/sec |

## Project Standards

- **Architecture**: [docs/architecture.md](docs/architecture.md) — folder structure, layer dependency rules, request flow
- **Accessibility**: [docs/accessibility.md](docs/accessibility.md) — WCAG 2.1 AA checklist, ARIA, keyboard nav, mobile responsiveness

### Layer dependency rule

```
Blueprint → Service → Repository
    ↓           ↓           ↓
    └───── Model ◄─┴── Model ◄┘
```

Blueprints never import repositories. Services never import Flask globals. Repositories contain zero business logic.

### Security

- Secrets via Google Secret Manager (`.env` fallback in dev)
- CSRF protection on state-changing methods
- Token bucket rate limiting (per-IP / per-user / global)
- Pydantic request validation with field-level 422 errors
- Security headers: `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`
- Full threat model: [docs/security.md](docs/security.md)

### Carbon Calculator

The `CarbonService` calculates a daily carbon footprint score from four categories:

| Category | Input | Factor |
|---|---|---|
| **Transport** | transport type + distance (km) | Walking/bicycle: 0, Metro: 2, Bus: 4, Bike: 8, Car: 10, Plane: 20 gCO₂/km |
| **Electricity** | AC usage hours | None: 0, 1-2h: 1.5, 3-5h: 4, 6+h: 8 hours × 0.5 kgCO₂/h |
| **Food** | diet type | Vegan: 1, Vegetarian: 2, Non-veg: 6 kgCO₂ × 0.5 |
| **Waste** | plastic waste (kg) | 2.0 kgCO₂/kg |

`score = transportFactor × distance × 0.1 + acHours × 0.5 + foodFactor × 0.5 + plasticKg × 2.0`

A breakdown per category is available via `CarbonService.get_breakdown()`.

### Accessibility

All features meet **WCAG 2.1 AA**. CI blocks PRs with Lighthouse accessibility scores below 90 or axe-core violations. Full checklist in [docs/accessibility.md](docs/accessibility.md).

## CI/CD

GitHub Actions workflows (`.github/workflows/`):

| Workflow | Trigger | Actions |
|---|---|---|
| `backend-ci.yml` | PR (backend/) | Ruff lint → pytest → coverage |
| `deploy.yml` | Push to `main` | Build & deploy Cloud Run + Firebase Hosting |

CI/CD configs reference [docs/security.md](docs/security.md) for incident response procedures.

## Tech Stack

| Component | Technology |
|---|---|
| Backend | Python 3.14 · Flask 3.1 · Gunicorn |
| Database | Firestore (Native mode) |
| Auth | JWT (PyJWT) |
| Infra | Cloud Run · Firebase Hosting · Secret Manager |
| CI | GitHub Actions · Ruff · pytest |
| Frontend | Vanilla JS · CSS custom properties |
