# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Install system dependencies (GCC for compiler grounding, curl for startup verification)
RUN apt-get update && apt-get install -y \
    g++ \
    libclang-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Set execution permissions on start.sh
RUN chmod +x start.sh

# Expose the ports the app runs on
EXPOSE 8000
EXPOSE 8003

# Run the startup script
CMD ["./start.sh"]
