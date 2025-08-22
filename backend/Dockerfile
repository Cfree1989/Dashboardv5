FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies (cached until requirements.txt changes)
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code (changes frequently, so copied last)
COPY . .

# Make scripts executable
RUN chmod +x /app/health_check.sh /app/graceful_shutdown.sh

# Create storage directory
RUN mkdir -p /app/storage

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:5000/api/v1/health || exit 1

# Run the application
CMD ["python", "run.py"] 