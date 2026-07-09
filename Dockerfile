# Pin to a specific stable release to avoid broken :latest regressions.
# v2.2.7 is the last release before the @langchain/core ./utils/uuid subpath
# was removed from the exports map, which caused ERR_PACKAGE_PATH_NOT_EXPORTED.
FROM flowiseai/flowise:2.2.7

USER root

# Set working directory to /app
WORKDIR /app

# Copy chatflow config, import script, and entrypoint
COPY ["500DaysofSummer Chatflow.json", "/app/"]
COPY import-chatflow.js /app/
COPY start.sh /app/

# Pre-create all Flowise data directories while still root.
# Flowise's logger.js calls mkdirSync() WITHOUT {recursive: true}, so if
# /home/node/.flowise (or any subdirectory) doesn't exist at startup it
# throws ENOENT and the process exits before binding to port 3000.
RUN mkdir -p \
      /home/node/.flowise/logs \
      /home/node/.flowise/storage && \
    sed -i 's/\r$//' /app/start.sh && \
    chmod +x /app/start.sh && \
    chown -R node:node /app /home/node/.flowise

# Switch back to the node user
USER node

# Set Flowise directories to writable paths owned by node user
ENV DATABASE_PATH=/home/node/.flowise
ENV APIKEY_PATH=/home/node/.flowise
ENV SECRETKEY_PATH=/home/node/.flowise
ENV LOG_PATH=/home/node/.flowise/logs
ENV BLOB_STORAGE_PATH=/home/node/.flowise/storage

# Expose server port
EXPOSE 3000

# Set entrypoint
ENTRYPOINT ["/app/start.sh"]
