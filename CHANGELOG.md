# Changelog

## [Unreleased]

### Added
- Frontend test job to CI pipeline
- GEMINI_API_KEY environment variable to backend CI test job
- CHANGELOG.md and CONTRIBUTING.md
- XSS safety audit comments for all innerHTML assignments in frontend
- Number conversion for API carbon_saved value in coach.js

### Fixed
- Unescaped API value in coach.js what-if result (carbon_saved now cast to Number)

## [1.0.0] - 2025-01-15

### Added
- AI-powered carbon footprint tracking and analysis
- Personalized coaching with Google Gemini 2.0 Flash
- Daily missions and weekly challenges
- Activity logging wizard (transport, food, energy, waste)
- Interactive dashboard with eco score, trends, and charts
- AI chat assistant for sustainability Q&A
- What-if impact analyzer
- Leaderboard with global rankings
- Achievement badges and eco tree progression
- User authentication (email/password + Google SSO)
- Dark mode theme support
- Weekly carbon report generation
- Responsive design for mobile and desktop
- Firestore integration for data persistence
- GitHub Actions CI with linting, security scanning, and testing
- Docker Compose setup for local development

### Security
- HTML escaping via htmlEscape utility for all user-generated content
- JWT-based authentication with CSRF protection
