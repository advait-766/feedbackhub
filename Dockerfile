FROM python:3.9-slim

# Install basic tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Ensure requirements.txt exists in your repo!
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your app (app.py, templates, etc.)
COPY . .

CMD ["python", "app.py"]
