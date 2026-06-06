# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Install system dependencies (GCC for compiler grounding)
RUN apt-get update && apt-get install -y \
    g++ \
    libclang-dev \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy and install requirements first (layer-cached)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Pre-download the lightweight embedding model during build time
# This caches the weights in the image so startup is fast and RAM-safe
ENV HF_HOME=/app/.cache/huggingface
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-small-en-v1.5')"

# Set execution permissions on start.sh
RUN chmod +x start.sh

# Expose the port the app runs on
EXPOSE 8000

# Run the startup script
CMD ["./start.sh"]
