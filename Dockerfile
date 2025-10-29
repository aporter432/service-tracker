# Multi-stage Dockerfile for ORBCOMM Service Tracker
# Stage 1: Build stage
FROM python:3.10-slim AS builder

LABEL maintainer="Aaron Porter"
LABEL description="ORBCOMM Service Tracker - Email notification monitoring and analytics"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install gunicorn gevent

# Stage 2: Runtime stage
FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    FLASK_APP=orbcomm_dashboard.py \
    FLASK_ENV=production \
    ORBCOMM_DATA_DIR=/app/data

# Create non-root user
RUN useradd -m -u 1000 orbcomm && \
    mkdir -p /app /app/data /app/logs && \
    chown -R orbcomm:orbcomm /app

# Copy virtual environment from builder
COPY --from=builder --chown=orbcomm:orbcomm /opt/venv /opt/venv

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=orbcomm:orbcomm . .

# Copy database backup and init script
COPY --chown=orbcomm:orbcomm database_backup.sql /app/database_backup.sql
COPY --chown=orbcomm:orbcomm init_database.sh /app/init_database.sh

# Install sqlite3 for database initialization
USER root
RUN apt-get update && apt-get install -y --no-install-recommends sqlite3 && \
    rm -rf /var/lib/apt/lists/* && \
    chmod +x /app/init_database.sh && \
    chown orbcomm:orbcomm /app/init_database.sh /app/database_backup.sql

# Switch to non-root user
USER orbcomm

# Create necessary directories
RUN mkdir -p /app/data/logs /app/data/inbox1 /app/data/inbox2 /home/orbcomm/.orbcomm

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/health')" || exit 1

# Initialize database and run gunicorn
CMD ["/bin/bash", "-c", "/app/init_database.sh && gunicorn --bind 0.0.0.0:5000 --workers 4 --worker-class gevent --timeout 120 --access-logfile - --error-logfile - orbcomm_dashboard:app"]
