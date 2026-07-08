FROM node:20-alpine

# Install system dependencies needed for Flowise and canvas/chromium components
RUN apk add --no-cache git python3 py3-pip make g++ build-base cairo-dev pango-dev chromium curl

# Skip downloading Puppeteer chrome; use system chromium
ENV PUPPETEER_SKIP_DOWNLOAD=true
ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium-browser

# Set environment variables for Flowise
ENV FLOWISE_PATH=/usr/local/lib/node_modules/flowise
ENV BASE_PATH=/root/.flowise
ENV PORT=9000

# Install Flowise globally
RUN npm install -g flowise

# Set working directory
WORKDIR /app

# Copy chatflow config, import script, and entrypoint
COPY "500DaysofSummer Chatflow.json" /app/
COPY import-chatflow.js /app/
COPY start.sh /app/

# Convert entrypoint script line endings to Unix LF and make it executable
RUN sed -i 's/\r$//' /app/start.sh && chmod +x /app/start.sh

# Expose server port
EXPOSE 3000

# Set entrypoint
ENTRYPOINT ["/app/start.sh"]
