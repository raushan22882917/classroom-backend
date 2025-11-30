# Multi-stage build for Class 12 Learning Platform Backend

FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies needed for Python packages
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
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

# Copy test script
COPY test_startup.py ./test_startup.py

# Note: Service account credentials are not copied - Cloud Run uses
# Application Default Credentials (ADC) via the service account attached to the service

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Cloud Run will set PORT environment variable (defaults to 8080)
# We'll read it from the environment at runtime
ENV PORT=8080

# Expose port (Cloud Run uses PORT env var)
EXPOSE 8080

# Install bash and curl for startup script and health checks
RUN apt-get update && apt-get install -y \
    bash \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy startup script and make it executable
COPY start.sh ./start.sh
RUN chmod +x ./start.sh

# Run the application using startup script (provides better error messages)
CMD ["./start.sh"]
