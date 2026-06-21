# ── Build stage ────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Runtime stage ──────────────────────────────────
FROM python:3.12-slim

# Security: non-root user
RUN groupadd -r ecomentor && useradd -r -g ecomentor ecomentor

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY . .

# Remove test files from production image
RUN rm -rf tests/ pytest.ini .env.example

# Set ownership
RUN chown -R ecomentor:ecomentor /app

# Switch to non-root user
USER ecomentor

EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

CMD ["gunicorn", "--bind", ":8080", "--workers", "4", "--worker-class", "gevent", "--timeout", "120", "main:app"]
