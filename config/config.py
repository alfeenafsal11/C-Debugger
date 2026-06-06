"""
Configuration file for the Agentic Bug Hunter pipeline.
Store API keys and server settings here.
"""

import os
# HF_TOKEN = os.getenv("HF_TOKEN")
MCP_SERVER_URL = "http://localhost:8003/sse"
HUGGINGFACE_API_KEY = os.getenv("HF_TOKEN")
