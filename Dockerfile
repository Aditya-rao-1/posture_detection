# Use Python 3.10 base image
FROM python:3.11-slim

# Install system dependencies required by mediapipe
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy backend files
COPY backend/ .

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expose port (just for docs; Render sets its own)
EXPOSE 5000

# Run the app using Gunicorn, binding to Render's PORT
CMD exec gunicorn app:app --bind 0.0.0.0:$PORT
