#!/bin/bash
set -e

# Load environment variables if needed
# source .env

# Start the application
echo "Starting MahaVistaar AI API..."
exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-80}
