FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    git \
    git-lfs \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

# Try to ensure the actual model file is present (LFS or full file)
RUN git lfs install --local 2>/dev/null; \
    git lfs pull 2>/dev/null; \
    echo "=== Checking /app/models ===" ; \
    ls -la /app/models/ ; \
    echo "=== File size ===" ; \
    du -h /app/models/best_model.pth 2>&1 || echo "MODEL FILE MISSING"

ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]