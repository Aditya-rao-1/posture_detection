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

# Expose port for docs (Render sets its own internally)
EXPOSE 5000

# Run the app using Gunicorn
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:$PORT", "--timeout", "300"]
