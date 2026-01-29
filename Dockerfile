# ----------------------------------------
# Base image
# ----------------------------------------
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
# ... (Base image and deps stay the same)

WORKDIR /app

COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ .

EXPOSE 5000

CMD ["python", "app.py"]
