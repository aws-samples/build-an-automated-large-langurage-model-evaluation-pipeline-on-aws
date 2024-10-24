#!/bin/bash

# Start the Node.js server in the background
node /app/backend/server.mjs &

# Serve the React build directory in the background
npx serve -s build -l tcp://0.0.0.0:3000 &

# Wait and keep the container running
wait -n
