# Multi-stage Dockerfile for Unified Backend Lambda
# Builds optimized arm64 image for AWS Lambda

FROM python:3.12-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Copy requirements
COPY requirements.txt .

# Install Python dependencies for arm64
RUN pip install --platform manylinux2014_aarch64 \
    --target . \
    --implementation cp \
    --python-version 3.12 \
    --only-binary=:all: \
    -r requirements.txt

# ==================== Runtime Stage ====================

FROM python:3.12-slim

# Set Lambda environment
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /var/task

# Copy dependencies from builder
COPY --from=builder /build .

# Copy application code
COPY lambda_handler.py .
COPY app/ app/

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD test -n "$DYNAMODB_WORKFLOWS_TABLE" || exit 1

# Lambda RIC entry point
ENTRYPOINT [ "/var/lang/bin/python", "-m", "awslambdaric" ]
CMD [ "lambda_handler.handler" ]

# Image size optimization
RUN find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true && \
    find . -type f -name "*.pyc" -delete && \
    find . -type f -name "*.pyo" -delete

LABEL org.opencontainers.image.title="Unified Agentic Backend" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.description="Production-ready unified backend for agentic workflows"
