FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Make health check script executable
RUN chmod +x /app/health_check.sh

# Make graceful shutdown script executable
RUN chmod +x /app/graceful_shutdown.sh

# Create storage directory
RUN mkdir -p /app/storage

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "run.py"] 