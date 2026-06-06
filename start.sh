#!/bin/sh

# Start the unified FastAPI backend
echo "Starting Agentic Bug Hunter Unified Service on port ${PORT:-8000}..."
exec uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT:-8000}
