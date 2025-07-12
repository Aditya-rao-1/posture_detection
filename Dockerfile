# Use a lightweight Python base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libgl1-mesa-glx \
    libglib2.0-0 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project files
COPY backend/ .

# Create necessary directories with proper permissions
RUN mkdir -p uploads outputs && chmod -R 755 uploads outputs

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt


# Set environment variable for Flask
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV PORT=8080

# Expose the port
EXPOSE 8080

# Start the server
CMD flask run --port=$PORT




