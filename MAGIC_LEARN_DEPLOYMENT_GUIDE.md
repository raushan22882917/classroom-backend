# Magic Learn Deployment Guide

This guide covers the complete deployment process for the Magic Learn backend API with all advanced features.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Local Development](#local-development)
4. [Production Deployment](#production-deployment)
5. [Configuration](#configuration)
6. [Monitoring & Maintenance](#monitoring--maintenance)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

#### Minimum Requirements
- **CPU**: 2 cores, 2.4GHz
- **RAM**: 4GB
- **Storage**: 20GB SSD
- **OS**: Ubuntu 20.04+ / CentOS 8+ / macOS 10.15+ / Windows 10+

#### Recommended for Production
- **CPU**: 8 cores, 3.0GHz+
- **RAM**: 16GB+
- **Storage**: 100GB+ SSD
- **Network**: 1Gbps+ bandwidth

### Software Dependencies

#### Required
- **Python**: 3.9+
- **pip**: Latest version
- **Git**: For version control

#### Optional (for enhanced features)
- **Redis**: For collaborative sessions and caching
- **PostgreSQL**: For persistent data storage
- **Docker**: For containerized deployment
- **Nginx**: For reverse proxy and load balancing

---

## Environment Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd magic-learn-backend
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install core dependencies
pip install -r requirements.txt

# Install optional dependencies for enhanced features
pip install redis psycopg2-binary

# For development
pip install pytest pytest-asyncio black flake8
```

### 4. Install System Dependencies

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install -y python3-dev build-essential libgl1-mesa-glx libglib2.0-0
```

#### CentOS/RHEL
```bash
sudo yum install -y python3-devel gcc gcc-c++ mesa-libGL glib2
```

#### macOS
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python@3.9
```

---

## Local Development

### 1. Environment Variables

Create a `.env` file in the project root:

```bash
# Core Configuration
APP_ENV=development
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=true

# API Keys
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here  # Optional

# Google Cloud (if using)
GOOGLE_APPLICATION_CREDENTIALS=./service-account.json
GOOGLE_CLOUD_PROJECT=your-project-id

# Database (optional)
DATABASE_URL=postgresql://user:password@localhost:5432/magiclearn
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# Redis (optional)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# CORS Configuration
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:8080

# Security
SECRET_KEY=your-secret-key-here
JWT_SECRET=your-jwt-secret-here

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=60

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Feature Flags
ENABLE_COLLABORATIVE_FEATURES=true
ENABLE_AI_TUTOR=true
ENABLE_REAL_TIME_ANALYSIS=true
ENABLE_BATCH_PROCESSING=true
```

### 2. Start Development Server

```bash
# Start the server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or use the start script
chmod +x start_server.sh
./start_server.sh
```

### 3. Verify Installation

```bash
# Test health endpoint
curl http://localhost:8000/api/health

# Test Magic Learn health
curl http://localhost:8000/api/magic-learn/health

# Check API documentation
open http://localhost:8000/docs
```

---

## Production Deployment

### Option 1: Docker Deployment

#### 1. Create Dockerfile

```dockerfile
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Start application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 2. Create docker-compose.yml

```yaml
version: '3.8'

services:
  magic-learn-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - APP_ENV=production
      - REDIS_HOST=redis
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/magiclearn
    depends_on:
      - redis
      - postgres
    volumes:
      - ./service-account.json:/app/service-account.json:ro
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=magiclearn
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - magic-learn-api
    restart: unless-stopped

volumes:
  redis_data:
  postgres_data:
```

#### 3. Deploy with Docker

```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f magic-learn-api

# Scale API instances
docker-compose up -d --scale magic-learn-api=3
```

### Option 2: Cloud Deployment (Google Cloud Run)

#### 1. Prepare for Cloud Run

```bash
# Build and push Docker image
gcloud builds submit --tag gcr.io/PROJECT_ID/magic-learn-api

# Deploy to Cloud Run
gcloud run deploy magic-learn-api \
    --image gcr.io/PROJECT_ID/magic-learn-api \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --max-instances 10 \
    --set-env-vars APP_ENV=production
```

#### 2. Configure Environment Variables

```bash
# Set environment variables
gcloud run services update magic-learn-api \
    --set-env-vars GEMINI_API_KEY=your_key_here \
    --set-env-vars REDIS_HOST=your_redis_host \
    --set-env-vars DATABASE_URL=your_database_url
```

### Option 3: Traditional Server Deployment

#### 1. Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install -y python3.9 python3.9-venv python3.9-dev build-essential nginx redis-server postgresql

# Create application user
sudo useradd -m -s /bin/bash magiclearn
sudo su - magiclearn

# Clone and setup application
git clone <repository-url> magic-learn-backend
cd magic-learn-backend
python3.9 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 2. Configure Systemd Service

Create `/etc/systemd/system/magic-learn.service`:

```ini
[Unit]
Description=Magic Learn API
After=network.target

[Service]
Type=exec
User=magiclearn
Group=magiclearn
WorkingDirectory=/home/magiclearn/magic-learn-backend
Environment=PATH=/home/magiclearn/magic-learn-backend/venv/bin
EnvironmentFile=/home/magiclearn/magic-learn-backend/.env
ExecStart=/home/magiclearn/magic-learn-backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

#### 3. Configure Nginx

Create `/etc/nginx/sites-available/magic-learn`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL Configuration
    ssl_certificate /etc/ssl/certs/your-domain.crt;
    ssl_certificate_key /etc/ssl/private/your-domain.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;

    # File upload size
    client_max_body_size 50M;

    # Proxy to API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check
    location /health {
        proxy_pass http://127.0.0.1:8000/api/health;
        access_log off;
    }

    # Static files (if any)
    location /static/ {
        alias /home/magiclearn/magic-learn-backend/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

#### 4. Start Services

```bash
# Enable and start services
sudo systemctl enable magic-learn
sudo systemctl start magic-learn
sudo systemctl enable nginx
sudo systemctl restart nginx

# Check status
sudo systemctl status magic-learn
sudo systemctl status nginx
```

---

## Configuration

### Environment Variables Reference

#### Core Settings
```bash
# Application
APP_ENV=production|development|testing
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=false

# Security
SECRET_KEY=your-secret-key-here
JWT_SECRET=your-jwt-secret-here
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

#### AI Services
```bash
# Gemini AI
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash-lite

# OpenAI (optional)
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4

# Google Cloud
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
GOOGLE_CLOUD_PROJECT=your-project-id
```

#### Database & Cache
```bash
# PostgreSQL
DATABASE_URL=postgresql://user:password@host:port/database

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your-redis-password
REDIS_DB=0
```

#### Feature Flags
```bash
# Enable/disable features
ENABLE_COLLABORATIVE_FEATURES=true
ENABLE_AI_TUTOR=true
ENABLE_REAL_TIME_ANALYSIS=true
ENABLE_BATCH_PROCESSING=true
ENABLE_CONTENT_GENERATION=true
ENABLE_ASSESSMENTS=true
```

#### Performance & Scaling
```bash
# Rate limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=60
RATE_LIMIT_BURST=20

# Caching
CACHE_TTL_SECONDS=3600
CACHE_MAX_SIZE=1000

# Processing
MAX_CONCURRENT_REQUESTS=10
MAX_BATCH_SIZE=10
MAX_FILE_SIZE_MB=10
```

### Configuration Files

#### config.py Updates

Add advanced configuration options:

```python
from pydantic import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    # ... existing settings ...
    
    # Advanced Features
    enable_collaborative_features: bool = True
    enable_ai_tutor: bool = True
    enable_real_time_analysis: bool = True
    enable_batch_processing: bool = True
    enable_content_generation: bool = True
    enable_assessments: bool = True
    
    # AI Configuration
    gemini_model: str = "gemini-2.5-flash-lite"
    openai_model: str = "gpt-4"
    max_ai_retries: int = 3
    ai_timeout_seconds: int = 30
    
    # Performance
    max_concurrent_requests: int = 10
    max_batch_size: int = 10
    max_file_size_mb: int = 10
    cache_ttl_seconds: int = 3600
    
    # Redis Configuration
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: Optional[str] = None
    redis_db: int = 0
    
    class Config:
        env_file = ".env"
```

---

## Monitoring & Maintenance

### Health Checks

#### Application Health
```bash
# Basic health check
curl http://localhost:8000/api/health

# Magic Learn specific health
curl http://localhost:8000/api/magic-learn/health

# Detailed system status
curl http://localhost:8000/api/magic-learn/system-status
```

#### Service Health Monitoring

Create monitoring script `monitor.sh`:

```bash
#!/bin/bash

# Check API health
API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/health)
if [ $API_STATUS -ne 200 ]; then
    echo "API health check failed: $API_STATUS"
    # Send alert
fi

# Check Redis
redis-cli ping > /dev/null
if [ $? -ne 0 ]; then
    echo "Redis connection failed"
    # Send alert
fi

# Check disk space
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "Disk usage high: $DISK_USAGE%"
    # Send alert
fi

# Check memory usage
MEMORY_USAGE=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
if [ $MEMORY_USAGE -gt 80 ]; then
    echo "Memory usage high: $MEMORY_USAGE%"
    # Send alert
fi
```

### Logging Configuration

#### Structured Logging Setup

```python
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'session_id'):
            log_entry['session_id'] = record.session_id
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
            
        return json.dumps(log_entry)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.FileHandler('/var/log/magic-learn/app.log'),
        logging.StreamHandler()
    ]
)

# Set JSON formatter
for handler in logging.getLogger().handlers:
    handler.setFormatter(JSONFormatter())
```

### Performance Monitoring

#### Metrics Collection

```python
import time
import psutil
from prometheus_client import Counter, Histogram, Gauge

# Metrics
REQUEST_COUNT = Counter('magic_learn_requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('magic_learn_request_duration_seconds', 'Request duration')
ACTIVE_SESSIONS = Gauge('magic_learn_active_sessions', 'Active collaborative sessions')
MEMORY_USAGE = Gauge('magic_learn_memory_usage_bytes', 'Memory usage')
CPU_USAGE = Gauge('magic_learn_cpu_usage_percent', 'CPU usage')

# Middleware for metrics collection
@app.middleware("http")
async def metrics_middleware(request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    REQUEST_DURATION.observe(duration)
    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path).inc()
    
    return response

# System metrics collection
def collect_system_metrics():
    MEMORY_USAGE.set(psutil.virtual_memory().used)
    CPU_USAGE.set(psutil.cpu_percent())
```

### Backup & Recovery

#### Database Backup

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backups/magic-learn"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup PostgreSQL
pg_dump $DATABASE_URL > $BACKUP_DIR/postgres_$DATE.sql

# Backup Redis
redis-cli --rdb $BACKUP_DIR/redis_$DATE.rdb

# Backup application data
tar -czf $BACKUP_DIR/app_data_$DATE.tar.gz /home/magiclearn/magic-learn-backend/data

# Clean old backups (keep 7 days)
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.rdb" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
```

#### Automated Backup with Cron

```bash
# Add to crontab
crontab -e

# Backup daily at 2 AM
0 2 * * * /home/magiclearn/scripts/backup.sh >> /var/log/magic-learn/backup.log 2>&1
```

---

## Troubleshooting

### Common Issues

#### 1. Import Errors

**Problem**: ModuleNotFoundError for magic_learn modules

**Solution**:
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt

# Check Python path
python -c "import sys; print(sys.path)"
```

#### 2. Gemini API Errors

**Problem**: Gemini API authentication fails

**Solution**:
```bash
# Verify API key
echo $GEMINI_API_KEY

# Test API key
curl -H "Authorization: Bearer $GEMINI_API_KEY" \
     https://generativelanguage.googleapis.com/v1/models

# Check quota and billing
```

#### 3. MediaPipe Installation Issues

**Problem**: MediaPipe fails to install or import

**Solution**:
```bash
# Install system dependencies
sudo apt install -y libgl1-mesa-glx libglib2.0-0

# Reinstall MediaPipe
pip uninstall mediapipe
pip install mediapipe

# For Apple Silicon Macs
pip install mediapipe-silicon
```

#### 4. Redis Connection Issues

**Problem**: Cannot connect to Redis

**Solution**:
```bash
# Check Redis status
sudo systemctl status redis

# Test connection
redis-cli ping

# Check configuration
redis-cli config get "*"

# Restart Redis
sudo systemctl restart redis
```

#### 5. High Memory Usage

**Problem**: Application consuming too much memory

**Solution**:
```bash
# Monitor memory usage
htop

# Check for memory leaks
python -m memory_profiler app/main.py

# Optimize configuration
# Reduce batch sizes, enable garbage collection
export PYTHONMALLOC=malloc
export MALLOC_ARENA_MAX=2
```

### Debug Mode

Enable debug mode for detailed error information:

```bash
# Set environment variable
export DEBUG=true
export LOG_LEVEL=DEBUG

# Run with debug
python -m uvicorn app.main:app --reload --log-level debug
```

### Performance Optimization

#### 1. Database Optimization

```sql
-- Create indexes for better performance
CREATE INDEX idx_sessions_user_id ON magic_learn_sessions(user_id);
CREATE INDEX idx_progress_user_id ON user_progress(user_id);
CREATE INDEX idx_assessments_created_at ON assessments(created_at);
```

#### 2. Caching Strategy

```python
# Implement caching for expensive operations
from functools import lru_cache
import redis

redis_client = redis.Redis(host='localhost', port=6379, db=0)

@lru_cache(maxsize=1000)
def get_cached_analysis(image_hash):
    # Check Redis cache first
    cached = redis_client.get(f"analysis:{image_hash}")
    if cached:
        return json.loads(cached)
    
    # Perform analysis and cache result
    result = perform_analysis(image_hash)
    redis_client.setex(f"analysis:{image_hash}", 3600, json.dumps(result))
    return result
```

#### 3. Load Balancing

```nginx
# nginx.conf - Load balancing configuration
upstream magic_learn_backend {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
}

server {
    location /api/ {
        proxy_pass http://magic_learn_backend;
        # ... other proxy settings
    }
}
```

### Maintenance Tasks

#### Weekly Maintenance

```bash
#!/bin/bash
# weekly_maintenance.sh

# Update system packages
sudo apt update && sudo apt upgrade -y

# Clean up logs
find /var/log/magic-learn -name "*.log" -mtime +30 -delete

# Optimize database
psql $DATABASE_URL -c "VACUUM ANALYZE;"

# Clear old cache entries
redis-cli FLUSHDB

# Restart services
sudo systemctl restart magic-learn
sudo systemctl restart nginx

echo "Weekly maintenance completed"
```

#### Monthly Maintenance

```bash
#!/bin/bash
# monthly_maintenance.sh

# Security updates
sudo apt update && sudo apt upgrade -y

# Certificate renewal (if using Let's Encrypt)
sudo certbot renew

# Database maintenance
psql $DATABASE_URL -c "REINDEX DATABASE magiclearn;"

# Clean up old backups
find /backups -mtime +30 -delete

# Update dependencies
source venv/bin/activate
pip list --outdated
# Review and update as needed

echo "Monthly maintenance completed"
```

This deployment guide provides comprehensive instructions for setting up and maintaining the Magic Learn backend in various environments, from local development to production deployment with monitoring and maintenance procedures.