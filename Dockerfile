# =============================================================================
# LGX-OPS-BOT — Multi-stage Docker build (python:3.11-slim)
# =============================================================================

# --------------- Stage 1: build dependencies --------------------------------
FROM python:3.11-slim AS builder

WORKDIR /build

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# --------------- Stage 2: runtime image -------------------------------------
FROM python:3.11-slim

LABEL maintainer="lgx-ops-bot@squareup.com" \
      app="lgx-ops-bot" \
      team="LGX"

# Install curl for HEALTHCHECK probe
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Non-root user
RUN groupadd -r botuser && useradd -r -g botuser -d /app -s /sbin/nologin botuser

WORKDIR /app

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY bot/        ./bot/
COPY scripts/    ./scripts/
COPY shared/     ./shared/
COPY docs/       ./docs/

# Ensure __init__.py exists so bot is a package
RUN test -f bot/__init__.py || touch bot/__init__.py

# Own everything by the non-root user
RUN chown -R botuser:botuser /app

USER botuser

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

ENTRYPOINT ["python", "-m", "bot.main"]
