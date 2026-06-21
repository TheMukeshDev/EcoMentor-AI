# Contributing to EcoMentor AI

## Setup

### Prerequisites
- Python 3.12+
- Node.js 20+
- Docker (for Firestore emulator)

### Getting Started

1. Fork and clone the repository.
2. Set up the backend:
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   cp .env.example .env
   ```
   Edit `backend/.env` and set at minimum `GEMINI_API_KEY` and `SECRET_KEY`.

3. Start the Firestore emulator:
   ```bash
   docker run -p 8080:8080 gcr.io/google.com/cloudsdktool/google-cloud-cli:emulators gcloud beta emulators firestore start --host-port=0.0.0.0:8080 --project=ecomentor-dev
   ```

4. Start the backend:
   ```bash
   flask run
   ```

5. Set up the frontend:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## Running Tests

```bash
# Backend (from backend/)
pytest                          # All tests
pytest --cov=app                # With coverage

# Frontend (from frontend/)
npm test                        # Vitest
npm run test:watch              # Watch mode
npm run test:coverage           # With coverage
```

## Code Style

- **Backend**: Follow existing Flask Blueprint → Services → Repository patterns. Use Ruff for linting (`ruff check app/`).
- **Frontend**: Vanilla JS with ES modules. Follow the existing component structure and naming conventions.
- **HTML/XSS**: All user-generated content rendered via `innerHTML` must be escaped with `htmlEscape()` from `utils.js`. For static HTML, add a `/* safe HTML */` comment.
- **CSS**: Use CSS custom properties for theming. Follow the existing naming conventions in component CSS files.

## PR Process

1. Create a feature branch from `main`.
2. Make your changes.
3. Run tests and linting locally.
4. Push and open a pull request against `main`.
5. Ensure CI passes (lint, security, backend tests, frontend tests).
6. Request review from a maintainer.
