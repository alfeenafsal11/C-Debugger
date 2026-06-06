#!/bin/sh

# HF Spaces uses port 7860 by default
exec uvicorn src.api.main:app --host 0.0.0.0 --port 7860
