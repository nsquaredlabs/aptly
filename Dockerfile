FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model for PII detection
RUN python -m spacy download en_core_web_sm

# Copy source code
COPY src/ ./src/

# Create non-root user
RUN useradd -m -u 1000 appuser
USER appuser

# Default port (Railway overrides via $PORT)
ENV PORT=8000
EXPOSE $PORT

# Run the application (shell form to expand $PORT)
CMD uvicorn src.main:app --host 0.0.0.0 --port $PORT
