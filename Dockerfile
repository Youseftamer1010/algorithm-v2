# ── Stage 1: Build frontend ──────────────────────────────────────────────
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# ── Stage 2: Production image ───────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Install backend Python deps
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy all Python source code
COPY data/ ./data/
COPY algorithms/ ./algorithms/
COPY simulation/ ./simulation/
COPY backend/ ./backend/
COPY main.py ./main.py

# Copy built frontend from stage 1
COPY --from=frontend-build /app/frontend/.next ./frontend/.next
COPY --from=frontend-build /app/frontend/public ./frontend/public
COPY --from=frontend-build /app/frontend/package.json ./frontend/package.json
COPY --from=frontend-build /app/frontend/node_modules ./frontend/node_modules
COPY --from=frontend-build /app/frontend/next.config.js ./frontend/next.config.js

# Expose ports
EXPOSE 8000 3000

# Start both backend and frontend via a simple script
COPY <<'EOF' /app/start.sh
#!/bin/sh
cd /app && uvicorn backend.main:app --host 0.0.0.0 --port 8000 &
cd /app/frontend && npx next start -p 3000 &
wait
EOF
RUN chmod +x /app/start.sh

CMD ["/app/start.sh"]
