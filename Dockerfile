# Hammy the Hire Tracker - Dockerfile
# Production-ready Docker image for local deployment

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements-local.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements-local.txt

# Copy application code
COPY *.py ./
COPY resumes/ ./resumes/
COPY dist/ ./dist/
COPY *.html ./
COPY *.js ./
COPY extension/ ./extension/

# Create directories for mounted volumes
RUN mkdir -p /app/data /app/config

# Set environment variables
ENV FLASK_APP=local_app.py
ENV PYTHONUNBUFFERED=1

# Expose Flask port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000').read()" || exit 1

# Run the application
CMD ["python", "local_app.py"]
