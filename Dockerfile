FROM python:3.13-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv from official Astral image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# Copy dependency definition files
COPY pyproject.toml uv.lock ./

# Install project dependencies
RUN uv sync --frozen --no-cache

# Copy project source code
COPY src/ ./src/
COPY README.md ./

# Create directory for PDF uploads
RUN mkdir -p uploads

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src"

EXPOSE 8000

# Default command: run FastAPI with Uvicorn
CMD ["uvicorn", "job_fastapi.main:app", "--host", "0.0.0.0", "--port", "8000"]
