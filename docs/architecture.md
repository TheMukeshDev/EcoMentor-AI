# EcoMentor AI — Architecture Guide

## 1. Folder Structure

```
ecomentor-ai/
│
├── backend/
│   ├── app/
│   │   ├── __init__.py              # Flask app factory (create_app)
│   │   ├── config.py                # Environment-based config classes
│   │   ├── extensions.py            # Firestore client singleton
│   │   │
│   │   ├── blueprints/              # Route layer — API endpoints
│   │   │   ├── __init__.py
│   │   │   ├── auth/                #  /api/auth/*
│   │   │   │   ├── __init__.py
│   │   │   │   ├── routes.py
│   │   │   │   └── schemas.py       # Request/response shapes
│   │   │   ├── footprint/           #  /api/footprint/*
│   │   │   │   ├── __init__.py
│   │   │   │   ├── routes.py
│   │   │   │   └── schemas.py
│   │   │   ├── recommendations/     #  /api/recommendations/*
│   │   │   │   ├── __init__.py
│   │   │   │   ├── routes.py
│   │   │   │   └── schemas.py
│   │   │   └── challenges/          #  /api/challenges/*
│   │   │       ├── __init__.py
│   │   │       ├── routes.py
│   │   │       └── schemas.py
│   │   │
│   │   ├── services/                # Business logic layer
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py
│   │   │   ├── footprint_service.py
│   │   │   ├── recommendation_service.py
│   │   │   └── challenge_service.py
│   │   │
│   │   ├── repositories/            # Data access layer (Firestore)
│   │   │   ├── __init__.py
│   │   │   ├── base_repository.py   # CRUD mixin
│   │   │   ├── user_repository.py
│   │   │   ├── footprint_repository.py
│   │   │   ├── recommendation_repository.py
│   │   │   └── challenge_repository.py
│   │   │
│   │   ├── models/                  # Pydantic / dataclass schemas
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── footprint.py
│   │   │   ├── recommendation.py
│   │   │   └── challenge.py
│   │   │
│   │   ├── middleware/              # Request interceptors
│   │   │   ├── __init__.py
│   │   │   └── auth_middleware.py   # JWT verification decorator
│   │   │
│   │   └── utils/                   # Shared helpers
│   │       ├── __init__.py
│   │       ├── errors.py            # Custom exception classes
│   │       ├── responses.py         # Standardised JSON responses
│   │       └── validators.py        # Input validation helpers
│   │
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py              # Fixtures (test client, Firestore emulator)
│   │   ├── unit/
│   │   │   ├── test_services/
│   │   │   └── test_repositories/
│   │   └── integration/
│   │       ├── test_blueprints/
│   │       └── test_api/
│   │
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── .env.example
│   └── main.py                      # Entry point
│
├── frontend/
│   ├── public/
│   │   ├── index.html               # SPA shell
│   │   ├── 404.html                 # Firebase Hosting fallback
│   │   └── favicon.ico
│   │
│   ├── src/
│   │   ├── css/
│   │   │   ├── base/
│   │   │   │   ├── reset.css
│   │   │   │   └── variables.css    # Design tokens
│   │   │   ├── components/          # Reusable UI pieces
│   │   │   │   ├── navbar.css
│   │   │   │   ├── cards.css
│   │   │   │   ├── forms.css
│   │   │   │   ├── buttons.css
│   │   │   │   └── modal.css
│   │   │   ├── layouts/             # Page-level structure
│   │   │   │   ├── dashboard.css
│   │   │   │   └── auth.css
│   │   │   └── pages/               # Page-specific overrides
│   │   │       ├── home.css
│   │   │       ├── calculator.css
│   │   │       └── challenges.css
│   │   │
│   │   ├── js/
│   │   │   ├── app.js               # Router initialisation
│   │   │   ├── api/                 # HTTP client layer (fetch wrappers)
│   │   │   │   ├── client.js        # Base fetch with auth header injection
│   │   │   │   ├── auth.js
│   │   │   │   ├── footprint.js
│   │   │   │   └── challenges.js
│   │   │   ├── services/            # Frontend business / state logic
│   │   │   │   ├── auth_service.js
│   │   │   │   ├── footprint_service.js
│   │   │   │   └── storage_service.js  # localStorage / session wrapper
│   │   │   ├── utils/               # Pure helpers
│   │   │   │   ├── helpers.js
│   │   │   │   └── validators.js
│   │   │   └── components/          # DOM-manipulation modules
│   │   │       ├── navbar.js
│   │   │       ├── charts.js        # Chart.js or similar
│   │   │       └── forms.js
│   │   │
│   │   └── assets/
│   │       ├── images/
│   │       └── icons/
│   │
│   ├── firebase.json
│   ├── .firebaserc
│   └── storage.rules
│
├── docs/
│   ├── architecture.md
│   ├── api-reference.md
│   └── setup-guide.md
│
├── .github/
│   └── workflows/
│       ├── backend-ci.yml           # Lint → test → build image
│       ├── frontend-ci.yml          # Lint → build → deploy Hosting
│       └── deploy.yml               # CI/CD to Cloud Run + Hosting
│
├── .gitignore
└── README.md
```

---

## 2. Responsibility of Each Folder

| Folder / File | Responsibility |
|---|---|
| **backend/app** | Flask application core — factory, config, extensions |
| **blueprints/** | Thin route handlers. Parse request → delegate to service → return response. One blueprint per domain. |
| **services/** | All business logic. Orchestrates repositories, calls external APIs, enforces rules. Never imports Flask `request` or `g`. |
| **repositories/** | Every Firestore query lives here. One class per entity. `base_repository.py` provides generic `get`, `set`, `query`, `delete`. |
| **models/** | Data shapes (dataclasses/Pydantic). Defines the contract between layers. |
| **middleware/** | Pre-request hooks — JWT verification, rate-limiting, request ID injection. |
| **utils/** | Pure, stateless helpers — error classes, response builders, validation functions. |
| **tests/** | Mirrors `app/` structure. Unit tests mock repositories; integration tests use Firestore emulator. |
| **frontend/src/css/** | Design tokens in `variables.css`, then component → layout → page cascade. Strict BEM-like naming. |
| **frontend/src/js/api/** | Thin fetch wrappers. One file per backend domain. `client.js` adds `Authorization: Bearer` and base URL. |
| **frontend/src/js/services/** | Frontend state management — caches, transforms, and exposes data to UI components. |
| **frontend/src/js/components/** | DOM builders. Each module exports functions that accept state and return DOM strings or nodes. |
| **.github/workflows/** | CI/CD pipelines. Backend tests on PR, auto-deploy to Cloud Run on merge to `main`. |

---

## 3. Request Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│  Browser (Firebase Hosting)                                 │
│  ┌──────────┐   ┌───────────┐   ┌───────────────────────┐  │
│  │ HTML/CSS │   │ JS SPA   │   │ JS API Client         │  │
│  │ (static) │   │ (router)  │   │ (fetch + auth header) │  │
│  └──────────┘   └───────────┘   └──────────┬────────────┘  │
│                                            │               │
└────────────────────────────────────────────┼───────────────┘
                                             │ HTTPS
                                             ▼
┌─────────────────────────────────────────────────────────────┐
│  Cloud Run (Flask)                                          │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  main.py (WSGI entry point)                         │    │
│  └─────────────────────┬───────────────────────────────┘    │
│                        │                                     │
│  ┌─────────────────────▼───────────────────────────────┐    │
│  │  Middleware Pipeline                                 │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │    │
│  │  │ CORS     │  │ Auth JWT │  │ Request ID       │  │    │
│  │  │ (Flask-  │  │ (before  │  │ (logging/tracing) │  │    │
│  │  │  CORS)   │  │  request)│  │                  │  │    │
│  │  └──────────┘  └──────────┘  └──────────────────┘  │    │
│  └─────────────────────┬───────────────────────────────┘    │
│                        │                                     │
│  ┌─────────────────────▼───────────────────────────────┐    │
│  │  Blueprint Router                                   │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐ │    │
│  │  │ Auth     │ │Footprint │ │Recommend │ │Chall.  │ │    │
│  │  │/api/auth │ │/api/foot │ │/api/rec  │ │/api/ch │ │    │
│  │  └────┬─────┘ └────┬─────┘ └────┬─────┘ └───┬────┘ │    │
│  └───────┼────────────┼────────────┼────────────┼──────┘    │
│          │            │            │            │           │
│  ┌───────▼────────────▼────────────▼────────────▼──────┐    │
│  │  Service Layer                                      │    │
│  │  - auth_service.py                                  │    │
│  │  - footprint_service.py                             │    │
│  │  - recommendation_service.py                        │    │
│  │  - challenge_service.py                             │    │
│  │  (business rules, cross-cutting logic, caching)     │    │
│  └──────────┬──────────────────────────────────────────┘    │
│             │                                               │
│  ┌──────────▼──────────────────────────────────────────┐    │
│  │  Repository Layer                                   │    │
│  │  - base_repository.py (generic CRUD)                │    │
│  │  - user_repository.py                               │    │
│  │  - footprint_repository.py                          │    │
│  │  - recommendation_repository.py                     │    │
│  │  - challenge_repository.py                          │    │
│  │  (only Firestore queries; no business rules)        │    │
│  └──────────┬──────────────────────────────────────────┘    │
│             │                                               │
└─────────────┼───────────────────────────────────────────────┘
              │
              ▼
   ┌──────────────────────┐
   │    Firestore         │
   │  ┌────────────────┐  │
   │  │ users          │  │
   │  │ footprints     │  │
   │  │ recommendations│  │
   │  │ challenges     │  │
   │  │ progress       │  │
   │  └────────────────┘  │
   └──────────────────────┘
```

### Step-by-step walkthrough

1. **Browser** serves static files from **Firebase Hosting** (CDN edge).
2. JS `api/client.js` constructs an HTTP request with `Authorization: Bearer <token>` and sends it to **Cloud Run**.
3. **Flask middleware** runs first — CORS headers, JWT verification, request-ID injection.
4. The request reaches the appropriate **Blueprint route** (e.g. `footprint/routes.py`).
5. The route extracts parameters, calls the **Service** layer (e.g. `FootprintService.calculate()`).
6. The service applies business rules, then delegates data access to a **Repository** (e.g. `FootprintRepository`).
7. The repository executes the **Firestore** query (read/write) and returns raw data.
8. The service transforms data, returns a result to the blueprint.
9. The blueprint wraps the result in a **standardised JSON response** (`utils/responses.py`).
10. The browser receives the response and the JS component updates the DOM.

---

## 4. Deployment Architecture

```
                              ┌─────────────────────────┐
                              │     GitHub Actions       │
                              │  (CI/CD)                 │
                              └────┬──────────┬──────────┘
                                   │          │
                            push to main    PR to main
                                   │          │
                    ┌──────────────┤          ├──────────────┐
                    │              │          │              │
                    ▼              ▼          ▼              ▼
           ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐
           │ Lint &     │  │ Build &    │  │ Lint &     │  │ Build &    │
           │ Test (BE)  │  │ Push Image │  │ Test (FE)  │  │ Deploy     │
           │            │  │ to Artifact│  │            │  │ Hosting    │
           └────────────┘  │ Registry   │  └────────────┘  │ (staging)  │
                           └─────┬──────┘                  └────────────┘
                                 │
                                 ▼
                     ┌─────────────────────┐
                     │  Cloud Run (Flask)  │
                     │                     │
                     │  - autoscaling      │
                     │  - min 1, max 10    │
                     │  - 256 MB RAM       │
                     │  - 60s timeout      │
                     │  - env vars from    │
                     │    Secret Manager   │
                     └──────────┬──────────┘
                                │
                     ┌──────────▼──────────┐
                     │   Firestore         │
                     │   (Native mode)     │
                     │                     │
                     │  - Indexes via      │
                     │    firestore.indexes │
                     │    .json            │
                     │  - Security rules   │
                     │    in firestore     │
                     │    .rules           │
                     └─────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│  Firebase Hosting                                               │
│                                                                  │
│  ┌────────────────┐   ┌────────────────┐   ┌────────────────┐   │
│  │ /              │   │ /api/*         │   │ /__/*          │   │
│  │ static assets  │   │ rewrite to     │   │ Firebase       │   │
│  │ (HTML/CSS/JS)  │   │ Cloud Run      │   │ internals      │   │
│  └────────────────┘   └────────────────┘   └────────────────┘   │
│                                                                  │
│  Rewrite rule in firebase.json:                                  │
│    "rewrites": [                                                 │
│      {"source": "/api/**", "run": {"serviceId": "ecomentor-api"}}│
│    ]                                                             │
└──────────────────────────────────────────────────────────────────┘
```

### Key decisions

| Decision | Rationale |
|---|---|
| **Firebase Hosting + Cloud Run** | Single Google Cloud surface; Hosting rewrites `/api/*` to Cloud Run so no CORS needed in production. |
| **Blueprint per domain** | Each domain can be worked on independently. Easy to extract into a microservice later. |
| **Service layer isolation** | Business logic is testable without Flask or Firestore. Swap Firestore for PostgreSQL by swapping only the repository layer. |
| **Repository pattern** | Every Firestore query is in exactly one place. No raw Firestore calls in blueprints or services. |
| **Pydantic/dataclass models** | Validates data at layer boundaries. Catches type errors early. |
| **No ORM** | Firestore is schema-less by nature. Repositories use the native `google-cloud-firestore` library directly. |
| **JS API client layer** | All fetch calls go through `api/client.js` so auth headers, error handling, and base URLs are centralised. |

---

## 5. Layer Dependency Rule

```
  Blueprint (depends on →) Service (depends on →) Repository
       │                        │                        │
       │                        ▼                        │
       └───────────── Model ◄───┴───► Model ◄────────────┘
```

- **Blueprint** imports Service + Model. Never imports Repository.
- **Service** imports Repository + Model. Never imports Flask globals (`request`, `g`, `session`).
- **Repository** imports Model + Firestore client. Contains zero business logic.
- **Model** imports nothing from the app. Pure data definition.

This enforces a strict **unidirectional dependency** — inner layers know nothing about outer layers.

---

## 6. Environment Strategy

| Environment | Firestore | Cloud Run Service Name | Firebase Hosting Project |
|---|---|---|---|
| `local` | Emulator | N/A | `ecomentor-dev` |
| `dev` | Dev project | `ecomentor-api-dev` | `ecomentor-dev` |
| `staging` | Staging project | `ecomentor-api-staging` | `ecomentor-staging` |
| `prod` | Production project | `ecomentor-api` | `ecomentor` |

Config is loaded via `app/config.py` using `APP_ENV` env var. Secrets stored in **Google Secret Manager**, not in `.env` (except for local development).
