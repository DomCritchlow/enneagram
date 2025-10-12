# Use Python 3.11 slim image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Create empty .env file so environment variables from Cloud Run secrets take precedence
RUN touch .env

# Create logs directory
RUN mkdir -p app/logs

# Expose port (Cloud Run will set PORT env var)
EXPOSE 8080

# Change to app directory and start the application
WORKDIR /app/app

# Run the application with Gunicorn for production
CMD ["sh", "-c", "gunicorn main:app -w 2 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:${PORT:-8080} --access-logfile - --error-logfile -"]
