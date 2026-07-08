FROM flowiseai/flowise:latest

USER root

# Set working directory to /app
WORKDIR /app

# Copy chatflow config, import script, and entrypoint
COPY ["500DaysofSummer Chatflow.json", "/app/"]
COPY import-chatflow.js /app/
COPY start.sh /app/

# Convert entrypoint script line endings to Unix LF and make it executable
RUN sed -i 's/\r$//' /app/start.sh && chmod +x /app/start.sh

# Expose server port
EXPOSE 3000

# Set entrypoint
ENTRYPOINT ["/app/start.sh"]
