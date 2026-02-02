# ----------------------------------------
# Base image
# ----------------------------------------
# Change from 3.4 to 3.9 (or 3.8)
FROM python:3.9-slim

# This will now build successfully on your EC2
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "app.py"]
