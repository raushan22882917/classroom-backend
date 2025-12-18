#!/bin/bash

# Start script for Class 12 Learning Platform Backend
# This script provides better error handling and logging for Cloud Run deployment

set -e  # Exit on any error

echo "🚀 Starting Class 12 Learning Platform Backend..."
echo "📅 $(date)"
echo "🐍 Python version: $(python --version)"
echo "📦 Pip version: $(pip --version)"

# Check if PORT environment variable is set (Cloud Run sets this)
if [ -z "$PORT" ]; then
    echo "⚠️  PORT environment variable not set, defaulting to 8080"
    export PORT=8080
fi

echo "🌐 Server will start on port: $PORT"

# Check if required environment variables are set
if [ -z "$GEMINI_API_KEY" ]; then
    echo "⚠️  Warning: GEMINI_API_KEY not set"
fi

if [ -z "$SUPABASE_URL" ]; then
    echo "⚠️  Warning: SUPABASE_URL not set"
fi

if [ -z "$SUPABASE_KEY" ]; then
    echo "⚠️  Warning: SUPABASE_KEY not set"
fi

# Print working directory and list files for debugging
echo "📁 Working directory: $(pwd)"
echo "📋 Files in current directory:"
ls -la

# Check if app directory exists
if [ ! -d "app" ]; then
    echo "❌ Error: app directory not found!"
    exit 1
fi

echo "📋 Files in app directory:"
ls -la app/

# Check if main.py exists
if [ ! -f "app/main.py" ]; then
    echo "❌ Error: app/main.py not found!"
    exit 1
fi

echo "✅ All checks passed, starting server..."

# Test import first to catch any Python errors early
echo "🧪 Testing Python import..."
python -c "
try:
    import app.main
    print('✅ Python import successful')
except Exception as e:
    print(f'❌ Python import failed: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ Python import test failed, exiting"
    exit 1
fi

echo "🚀 Starting FastAPI server..."

# Start the FastAPI server with uvicorn
# Use 0.0.0.0 to bind to all interfaces (required for Cloud Run)
# Use the PORT environment variable set by Cloud Run
exec python -m uvicorn app.main:app \
    --host 0.0.0.0 \
    --port $PORT \
    --workers 1 \
    --log-level info \
    --access-log \
    --no-use-colors