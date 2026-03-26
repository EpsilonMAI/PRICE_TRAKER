FROM node:20-alpine AS frontend-build

WORKDIR /app

COPY frontend/tracker-ui/package*.json ./
RUN npm ci

COPY frontend/tracker-ui ./

ENV VITE_API_BASE_URL=/api

RUN npm run build

FROM caddy:2-alpine

COPY deploy/caddy/Caddyfile /etc/caddy/Caddyfile
COPY --from=frontend-build /app/dist /srv
