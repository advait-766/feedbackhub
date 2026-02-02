# ----------------------------------------
# Base image
# ----------------------------------------
FROM python:3.13.11-slim
FROM python:3.13-slim-bookworm
RUN apt-get update && apt-get upgrade -y && apt-get clean

# ----------------------------------------
# Runtime environment hardening
# ----------------------------------------
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# ----------------------------------------
# Working directory
# ----------------------------------------
WORKDIR /app

# ----------------------------------------
# System dependencies (build only)
# ----------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# ----------------------------------------
# Python dependencies (cached layer)
# ----------------------------------------
COPY app/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
