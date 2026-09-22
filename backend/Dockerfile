 
FROM python:3.11-slim

WORKDIR /app

# System libraries needed by torch, opencv, etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Render provides $PORT; default to 8000 for local
ENV PORT=8000
EXPOSE 8000
# Debug: verify files before starting
RUN echo "=== Files in /app ===" && ls -la /app && \
    echo "=== app dir ===" && ls -la /app/app

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]