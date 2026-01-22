# ----------------------------------------
# Explicit, pinned Python version
# ----------------------------------------
FROM python:3.13.11-slim

# ----------------------------------------
# Runtime environment hardening
# ----------------------------------------
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# ----------------------------------------
# Working directory inside container
# ----------------------------------------
WORKDIR /app

# ----------------------------------------
# Minimal system dependencies
# (needed for some Python wheels)
# ----------------------------------------
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# ----------------------------------------
# Python dependencies
# ----------------------------------------
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ----------------------------------------
# Application source code
# ----------------------------------------
COPY app/ .

# ----------------------------------------
# Expose Flask port
# ----------------------------------------
EXPOSE 5000

# ----------------------------------------
# Start the Flask application
# ----------------------------------------
CMD ["python", "app.py"]
