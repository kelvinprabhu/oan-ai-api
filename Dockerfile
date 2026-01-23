# Use Python 3.10 slim image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Set environment variables
# PYTHONUNBUFFERED ensures logs are streamed in real-time
# PYTHONPATH ensures 'app' and other modules are importable
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PORT=80

# Install minimal system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Ensure scripts are Unix-style and executable
RUN chmod +x start.sh && \
    find . -type f -name "*.sh" -exec sed -i 's/\r$//' {} +

# Expose port
EXPOSE 80

# Health check (checks the root endpoint we added)
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:80/ || exit 1

# Start the application using uvicorn
CMD ["/bin/bash", "start.sh"]
