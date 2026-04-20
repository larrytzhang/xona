# GPS Shield Backend — Production Dockerfile.
#
# Builds a slim Python 3.12 image with all backend dependencies.
# Runs the FastAPI app via uvicorn on port 8000.
#
# Build:   docker build -t gps-shield-backend .
# Run:     docker run -p 8000:8000 --env-file .env gps-shield-backend

FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for asyncpg and scipy
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -r -s /bin/false appuser

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code with the non-root user as owner.
COPY --chown=appuser:appuser . .

# Switch to non-root user for runtime
USER appuser

# Run database migrations on startup, then start the server
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]

EXPOSE 8000
