# Use Python slim image as base
FROM python:3.13-slim

# Install TeX Live and required packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    texlive-latex-base \
    texlive-latex-extra \
    texlive-fonts-recommended \
    texlive-science \
    texlive-plain-generic \
    poppler-utils \
    curl && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies first (for better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy only the necessary application files, not tests or potential secrets
COPY api.py .
COPY src/ src/

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV USE_LOCAL_STORAGE=false
ENV STORAGE_BUCKET=benchmark-eval-storage

# Note: When deployed in Google Cloud (Cloud Run, GKE, etc.), the container will 
# automatically use the service account assigned to the resource
# No need to explicitly set GOOGLE_APPLICATION_CREDENTIALS

# Expose the port from the environment variable
EXPOSE ${PORT}

# Add a health check (checks the /health endpoint based on PORT)
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:${PORT}/health || exit 1

# Command to run the application with gunicorn using the PORT environment variable
CMD gunicorn --bind 0.0.0.0:${PORT} api:app 