#!/bin/sh

# Start the MCP server in the background
echo "Starting MCP Server..."
python src/mcp/provided_server/infineon_mcp_server.py > mcp_server.log 2>&1 &

# Wait for MCP server to start and load embeddings/database
echo "Waiting 12 seconds for MCP server index to load..."
sleep 12

# Check if MCP server started successfully
if curl -s http://localhost:8003/sse > /dev/null; then
    echo "MCP Server is up and running!"
else
    echo "Warning: MCP Server might still be starting or failed. Check mcp_server.log."
fi

# Start the FastAPI backend
echo "Starting FastAPI backend on port ${PORT:-8000}..."
exec uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT:-8000}
