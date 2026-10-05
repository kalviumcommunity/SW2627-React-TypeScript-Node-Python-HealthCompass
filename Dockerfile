# Multi-stage Dockerfile for HealthCompass Backend
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency specifications
COPY requirements.txt pyproject.toml ./

# Install python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source and documentation
COPY src/ src/
COPY data/ data/
COPY prompts/ prompts/
COPY docs/ docs/
COPY evaluation/ evaluation/

# Install local package in editable mode
RUN pip install --no-cache-dir -e .

# Expose FastAPI port
EXPOSE 8000

ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["python", "-m", "uvicorn", "src.api_server:app", "--host", "0.0.0.0", "--port", "8000"]
