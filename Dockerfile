# Multi-stage build for Class 12 Learning Platform Backend

FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY app/ ./app/

# Note: Service account credentials are not copied - Cloud Run uses
# Application Default Credentials (ADC) via the service account attached to the service

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Cloud Run will set PORT environment variable, default to 8000
ENV PORT=8000

# Expose port (Cloud Run uses PORT env var, but we keep this for compatibility)
EXPOSE 8000

# Run the application
# Cloud Run sets PORT env var automatically, so we use it
CMD exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
