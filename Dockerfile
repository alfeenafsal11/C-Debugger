# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Install system dependencies (GCC for compiler grounding)
RUN apt-get update && apt-get install -y \
    g++ \
    libclang-dev \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy and install requirements first (layer-cached separately from code)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Pre-download the ONNX embedding model at BUILD TIME.
# fastembed uses ONNX runtime - no PyTorch needed, ~210MB model, fits in 512MB.
# Setting FASTEMBED_CACHE_PATH keeps it inside /app so it survives.
ENV FASTEMBED_CACHE_PATH=/app/.cache/fastembed
RUN python -c "from fastembed import TextEmbedding; list(TextEmbedding('BAAI/bge-base-en-v1.5').embed(['warmup']))"

# Set execution permissions on start.sh
RUN chmod +x start.sh

# Expose the port the app runs on
EXPOSE 8000

# Run the startup script
CMD ["./start.sh"]
