# Security Threat Model

## Scope

EcoMentor AI — Flask API (Cloud Run) + Firebase Hosting SPA + Firestore.

## Assets

| Asset | Sensitivity | Description |
|---|---|---|
| User PII (email, name) | PII | Stored in Firestore `users` collection |
| Auth tokens (JWT) | Secret | Firebase ID tokens, transmitted via Authorization header |
| Carbon footprint data | User-private | Per-user activity logs, scores, reports |
| Firestore service account | Critical | Production database access |
| SECRET_KEY | Critical | Flask signing, CSRF token signing |

## Trust Boundaries

```
[Browser SPA] ──HTTPS──► [Cloud Run API] ──► [Firestore]
                    │                          │
                    └── Firebase Auth ──────────┘
```

## Threats (STRIDE per asset)

### T1: Token theft / replay

- **Risk**: Attacker steals JWT via XSS or network intercept
- **Impact**: Full account impersonation
- **Mitigations**:
  - Short token expiry (Firebase ID tokens: 1 hour)
  - HTTPS enforced (Cloud Run default)
  - `require_auth` middleware verifies Firebase Auth SDK (not raw decode)
  - No token storage in URL query strings

### T2: CSRF on state-changing endpoints

- **Risk**: Attacker tricks authenticated user into submitting a request
- **Impact**: Activity logged, profile changed without consent
- **Mitigations**:
  - Nonce-based CSRF protection with 1-hour TTL (replaced static HMAC approach)
  - Token format: `nonce:timestamp:hmac_sha256_signature` (three parts separated by `:`)
  - CSRF check skipped in TESTING mode only
  - `generate_csrf_token()` produces unique nonces via `secrets.token_hex(32)`
  - `validate_csrf_token()` checks HMAC signature and timestamp expiry
  - CSRF token endpoint at `GET /api/auth/csrf-token`
  - Client sends token via `X-CSRF-Token` header on state-changing requests

### T3: Rate-limit bypass

- **Risk**: Attacker floods auth endpoints to brute-force or DoS
- **Impact**: Account lockout, resource exhaustion
- **Mitigations**:
  - Token-bucket rate limiter per-IP (strict: 10 req/60s) and per-user
  - Rate limiting configurable via env vars
  - Rate limiting enforced at the blueprint + global level

### T4: Firestore injection

- **Risk**: Malicious query via user-supplied filter fields
- **Impact**: Unauthorized data access or data corruption
- **Mitigations**:
  - Repositories accept structured `(field, op, value)` tuples only
  - No raw Firestore query strings built from user input
  - Pydantic validation on all request bodies before they reach services

### T5: Missing auth on protected endpoints

- **Risk**: Unauthenticated access to user data
- **Impact**: Data leakage
- **Mitigations**:
  - `require_auth` decorator on all non-public blueprint routes
  - Public routes: health check, register, login, csrf-token
  - `g.user_id` set by middleware for downstream use

### T6: Secret exposure

- **Risk**: SECRET_KEY or service account leaked in repo, logs, or env
- **Impact**: Full system compromise
- **Mitigations**:
  - `.gitignore` blocks `.env`, `credentials.json`, `service-account.json`, `*.pem`, `*.key`
  - Production secrets via Google Secret Manager (not env vars)
  - `validate_required_secrets()` fails fast at startup
  - Logging never prints secret values

## Data Flow Security

```
Registration:
  Client ─POST {email,password}──► Auth Blueprint
    └─ validate_body(Pydantic)
    └─ AuthService.register_user()
        └─ firebase_admin.auth.create_user()   # Firebase handles hashing
        └─ UserRepository.set(uid, profile)     # Firestore write

Login:
  Client ─POST {id_token}──► Auth Blueprint
    └─ AuthService.authenticate_user()
        └─ firebase_admin.auth.verify_id_token()

Authenticated Request:
  Client ─GET /api/activities (Bearer <token>)──► Middleware
    └─ require_auth verifies Firebase token
    └─ g.user_id set
    └─ Blueprint → Service → Repository → Firestore
```

## Security Headers

Applied globally via `@app.after_request`:

| Header | Value |
|---|---|
| `X-Content-Type-Options` | `nosniff` |
| `X-Frame-Options` | `DENY` |
| `X-XSS-Protection` | `1; mode=block` |

## Incident Response

1. **Rate-limit alerts**: Logged at WARNING level with IP
2. **Auth failures**: Logged at WARNING level (no PII)
3. **5xx errors**: Logged at ERROR with full traceback (no secrets)
4. **Secret rotation**: `SECRET_KEY` can be rotated with zero downtime via Secret Manager versioning

## Assumptions & Accepted Risks

- Firebase Admin SDK is the source of truth for auth; the app never stores passwords
- Firestore security rules are managed separately (GCP project level)
- CORS is configured per-environment; production restricts to known origins
- Cloud Run provides network isolation and automatic TLS termination
