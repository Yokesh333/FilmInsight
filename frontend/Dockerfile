# ── Build Stage ─────────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci --silent

COPY . .
RUN npm run build

# ── Production Stage ─────────────────────────────────────────────
FROM nginx:1.25-alpine AS production

# Copy built assets
COPY --from=builder /app/dist /usr/share/nginx/html

# Nginx config for React SPA
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD wget -qO- http://localhost || exit 1

CMD ["nginx", "-g", "daemon off;"]
