# ============================================================================
# Stage 1: build the React frontend
# Uses a Node image just to run `npm run build`, producing static files in
# /frontend/dist. None of Node stays in the final image - we only copy the
# built output out in stage 2. Vite 8 needs Node 20.19+/22.12+, so node:22.
# ============================================================================
FROM node:22-slim AS frontend-build

WORKDIR /frontend

# Copy only the dependency manifests first, so Docker can cache the (slow)
# npm install layer and skip it when only source code changes.
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

# Now the rest of the frontend source (includes .env.production -> VITE_API_URL=/api)
COPY frontend/ ./
RUN npm run build   # outputs to /frontend/dist

# ============================================================================
# Stage 2: the Python API, which also serves the built React app
# ============================================================================
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

COPY Todoapp/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# The backend source (main.py serves frontend/dist if it exists - see below)
COPY . .

# Bring in ONLY the built frontend from stage 1. This lands at
# /app/frontend/dist, which is exactly where main.py's FRONTEND_DIST looks.
COPY --from=frontend-build /frontend/dist ./frontend/dist

EXPOSE 8000

CMD ["uvicorn", "Todoapp.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
