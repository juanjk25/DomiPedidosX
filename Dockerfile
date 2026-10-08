# Build the single-container development image with the agreed Node.js version.
FROM node:24.21.0-bookworm-slim AS node-runtime

# Keep Python/Django as the base runtime and add Node/npm from the pinned image.
FROM python:3.12.15-slim-trixie

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY --from=node-runtime /usr/local/ /usr/local/

WORKDIR /app

COPY backend/requirements.txt /app/backend/requirements.txt
RUN python -m pip install --no-cache-dir -r /app/backend/requirements.txt

COPY backend/ /app/backend/
COPY frontend/package.json frontend/package-lock.json /app/frontend/
WORKDIR /app/frontend
RUN npm install
COPY frontend/ /app/frontend/

COPY start-services.mjs /app/start-services.mjs

EXPOSE 8000 5173

CMD ["node", "/app/start-services.mjs"]
