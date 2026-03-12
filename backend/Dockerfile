FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ── Step 1: ติดตั้ง PyTorch CPU-only ─────────────────────────────────────────
RUN pip install --no-cache-dir \
    torch==2.3.1+cpu \
    --index-url https://download.pytorch.org/whl/cpu

# ── Step 2: ติดตั้ง dependencies (numpy 2.x ตรงกับ model) ────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Step 3: Copy source code ──────────────────────────────────────────────────
COPY . .

RUN mkdir -p database RL_model data logs

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
