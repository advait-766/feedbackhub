# ----------------------------------------
# Base image
# ----------------------------------------
FROM python:3.13.11-slim

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
    && pip install --no-cache-dir -r requirements.txt

# ----------------------------------------
# Application source (changes most often)
# ----------------------------------------
COPY app/ ./app

# ----------------------------------------
# Expose Flask port
# ----------------------------------------
EXPOSE 5000

# ----------------------------------------
# Start application
# ----------------------------------------
CMD ["python", "app/app.py"]
