# EcoMentor AI Architecture

## Project Structure

```
ecomentor-ai/
├── backend/                    Flask API (Cloud Run)
│   ├── main.py                 Entry point
│   ├── Dockerfile              Container config
│   ├── requirements.txt        Python dependencies
│   ├── .env.example            Environment template
│   ├── firestore.rules         Firestore security rules
│   ├── firestore.indexes.json  Composite indexes
│   ├── app/
│   │   ├── __init__.py         App factory (create_app)
│   │   ├── config.py           3 env classes (Dev/Test/Prod)
│   │   ├── extensions.py       Firestore client singleton
│   │   ├── blueprints/
│   │   │   ├── auth/           Registration, login, profile
│   │   │   ├── dashboard/      Summary, history, trends
│   │   │   ├── activities/     Log, list, get, delete activities
│   │   │   ├── ai/             Recommendations, reports, chat, what-if, feedback
│   │   │   └── leaderboard/    Global & friends leaderboard
│   │   ├── middleware/
│   │   │   ├── auth_middleware.py   Firebase JWT verification
│   │   │   └── csrf.py              Nonce-based CSRF with TTL
│   │   ├── services/
│   │   │   ├── auth_service.py      Firebase Auth integration
│   │   │   ├── dashboard_service.py Summary/history/trends logic
│   │   │   ├── activity_service.py  Activity + carbon + streak + points
│   │   │   ├── ai_service.py        Gemini client + conversation memory + caching
│   │   │   ├── carbon_service.py    Carbon calculator with regional factors
│   │   │   ├── cache_service.py     Dual cache (in-memory LRU + Firestore)
│   │   │   ├── prompt_service.py    Prompt templates + sanitization
│   │   │   ├── points_service.py    Gamification levels
│   │   │   ├── streak_service.py    Consecutive day tracking
│   │   │   └── leaderboard_service.py User ranking & friends
│   │   ├── repositories/       Firestore query layer
│   │   │   ├── base_repository.py       CRUD + query with cursor pagination
│   │   │   ├── user_repository.py
│   │   │   ├── activity_repository.py
│   │   │   ├── carbon_history_repository.py
│   │   │   ├── footprint_repository.py
│   │   │   ├── recommendation_repository.py
│   │   │   ├── challenge_repository.py
│   │   │   ├── report_repository.py
│   │   │   └── ai_report_repository.py
│   │   ├── models/             Data classes (layer contract)
│   │   └── utils/
│   │       ├── errors.py       AppError hierarchy
│   │       ├── responses.py    JSON response builders
│   │       ├── validators.py   Pydantic body validation
│   │       ├── rate_limiter.py Token bucket per scope
│   │       └── secrets.py      Env/Secret Manager resolution
│   └── tests/                  80+ tests (pytest)
├── frontend/                   Vanilla JS SPA (Firebase Hosting)
│   ├── index.html              Shell with nav, bottom nav, footer
│   ├── 404.html                Fallback page
│   ├── manifest.json           PWA manifest (SVG icons)
│   ├── sw.js                   Service worker
│   ├── public/                 Static assets (SVG icons)
│   ├── css/                    Variables, reset, base, layout, components, utilities
│   ├── js/
│   │   ├── main.js             Bootstrap + route registration
│   │   ├── router.js           Hash-based SPA router + auth nav
│   │   ├── api-client.js       Fetch wrapper + JWT + CSRF
│   │   ├── store.js            Simple pub/sub state
│   │   ├── theme.js            Dark/light toggle
│   │   ├── home.js             Landing page
│   │   ├── auth.js             Login/signup forms
│   │   ├── dashboard.js        Summary cards, chart, insights
│   │   ├── activities.js       Multi-step activity wizard
│   │   ├── coach.js            AI conversation + what-if analyzer
│   │   ├── leaderboard.js      Global ranking table
│   │   ├── achievements.js     Badges and levels
│   │   ├── report.js           Weekly/monthly reports
│   │   ├── profile.js          User profile
│   │   ├── settings.js         Preferences
│   │   ├── skeletons.js        Loading skeletons
│   │   └── utils.js            htmlEscape, toast
│   └── tests/                  Vitest + jsdom (3 test files)
├── firebase.json               Firebase Hosting + Rewrites config
├── .github/workflows/          CI/CD pipelines
├── docker-compose.yml          Local dev with Firestore emulator
├── docs/
│   ├── architecture.md         This file
│   ├── security.md             STRIDE threat model
│   └── accessibility.md        WCAG 2.1 AA checklist
└── README.md                   Project overview + setup
```

## Layer Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Blueprint (Routes)                      │
│  Parse request → Auth → Rate limit → Validate → Delegate   │
├─────────────────────────────────────────────────────────────┤
│                       Service Layer                         │
│  Business logic, orchestration, rules, AI conversation      │
├─────────────────────────────────────────────────────────────┤
│                     Repository Layer                        │
│  Firestore queries, cursor pagination, zero business logic  │
├─────────────────────────────────────────────────────────────┤
│                     Firestore (DB)                          │
└─────────────────────────────────────────────────────────────┘
```

## AI Architecture

```
┌──────────────┐     ┌──────────────┐     ┌─────────────┐
│  AI Routes   │────▶│  AIService   │────▶│PromptService│
│  /api/ai/*   │     │              │     │ (templates) │
└──────────────┘     │ • Chat       │     └─────────────┘
                     │ • Recommend  │            │
                     │ • Report     │            ▼
                     │ • Personality│     ┌─────────────┐
                     │ • Mission    │     │   Gemini    │
                     │ • What-If    │     │ 2.0 Flash   │
                     │ • Feedback   │     └─────────────┘
                     │ • Cache      │
                     │ • Memory     │
                     └──────────────┘
```

## Request Flow

1. User action → Frontend SPA route change
2. Route handler calls `api('/path')` → fetch with JWT + CSRF headers
3. Firebase Hosting rewrites `/api/*` to Cloud Run
4. Flask blueprint: auth middleware → rate limiter → CSRF (POST) → validation → service
5. Service orchestrates repositories, applies business logic
6. Response flows back as JSON

## Key Design Decisions

- **Vanilla JS frontend**: Zero build step for rapid iteration; Vite for dev bundling
- **Firestore**: Serverless NoSQL; composite indexes for query performance
- **Gemini-3.5 Flash**: Low latency, cost-effective for real-time coaching
- **Dual cache**: In-memory LRU (hot reads) + Firestore (persistence)
- **Nonce-based CSRF**: Rotation on each request, 1-hour TTL
- **Cursor pagination**: Firestore `start_after` for scalable list endpoints
- **Regional carbon factors**: Grid intensity varies by geography
- **Conversation memory**: Per-user in-memory chat history (max 50 turns)
