#!/bin/sh

# If admin credentials are provided, pre-create the user before starting
if [ -n "$FLOWISE_USERNAME" ] && [ -n "$FLOWISE_PASSWORD" ]; then
    echo "Pre-creating admin user..."
    npx flowise user --email "$FLOWISE_USERNAME" --password "$FLOWISE_PASSWORD"
fi

# Run import script in the background
node /app/import-chatflow.js &

# Start Flowise in the foreground
exec npx flowise start
