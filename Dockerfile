FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy project files for install
COPY pyproject.toml README.md ./
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini .

# Install package
RUN pip install --no-cache-dir .

# Download spaCy model for PII detection
RUN python -m spacy download en_core_web_sm

# Create non-root user
RUN useradd -m -u 1000 appuser
USER appuser

# Default port (Railway/Render override via $PORT)
ENV PORT=8000
EXPOSE $PORT

# Run migrations then start server
CMD aptly init-db && uvicorn src.main:app --host 0.0.0.0 --port $PORT
