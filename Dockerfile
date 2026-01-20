# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create uploads directory
RUN mkdir -p uploads

# Create startup script that properly expands PORT
RUN echo '#!/bin/bash\nexec gunicorn app.main:app --bind 0.0.0.0:${PORT:-5000} --workers 2 --timeout 120' > /start.sh && chmod +x /start.sh

# Run with shell script
CMD ["/start.sh"]
