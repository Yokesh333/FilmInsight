FROM flowiseai/flowise:latest

USER root

# Set working directory to /app
WORKDIR /app

# Copy chatflow config, import script, and entrypoint
COPY ["500DaysofSummer Chatflow.json", "/app/"]
COPY import-chatflow.js /app/
COPY start.sh /app/

# Convert entrypoint script line endings to Unix LF, make it executable, and change owner to node
RUN sed -i 's/\r$//' /app/start.sh && \
    chmod +x /app/start.sh && \
    chown -R node:node /app

# Switch back to the node user
USER node

# Expose server port
EXPOSE 3000

# Set entrypoint
ENTRYPOINT ["/app/start.sh"]
