#!/bin/bash
# Startup script for Cloud Run with better error handling

# Exit on error for critical failures only
set -euo pipefail

echo "=========================================="
echo "Starting Classroom Backend API"
echo "=========================================="

# Read PORT from environment (Cloud Run sets this, default to 8080)
PORT=${PORT:-8080}
echo "PORT: $PORT"
export PORT

# Verify PORT is a number
if ! [[ "$PORT" =~ ^[0-9]+$ ]]; then
    echo "ERROR: PORT must be a number, got: $PORT"
    exit 1
fi

# Check required environment variables (warn but don't fail)
echo ""
echo "Checking environment variables..."

REQUIRED_VARS=(
    "SUPABASE_URL"
    "SUPABASE_KEY"
    "SUPABASE_SERVICE_KEY"
    "GOOGLE_CLOUD_PROJECT"
    "GEMINI_API_KEY"
    "WOLFRAM_APP_ID"
    "YOUTUBE_API_KEY"
)

MISSING_VARS=()
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var:-}" ]; then
        MISSING_VARS+=("$var")
        echo "  ❌ $var: NOT SET"
    else
        echo "  ✓ $var: SET"
    fi
done

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    echo ""
    echo "=========================================="
    echo "WARNING: Missing required environment variables!"
    echo "=========================================="
    echo "Missing: ${MISSING_VARS[*]}"
    echo ""
    echo "The application will attempt to start with minimal settings."
    echo "Some features may not work until these are configured."
    echo "=========================================="
    echo ""
fi

# Quick test - try to import the app (non-blocking)
echo ""
echo "Testing application import..."
if python3 -c "from app.main import app; print('✓ App import successful')" 2>&1; then
    echo "✓ Application can be imported"
else
    echo "⚠ Warning: App import check had issues, but continuing..."
    echo "  (Application will attempt to start - check logs for details)"
fi

echo ""
echo "=========================================="
echo "Starting uvicorn server..."
echo "Host: 0.0.0.0"
echo "Port: $PORT"
echo "=========================================="
echo ""

# Start uvicorn with the app
# Use exec to replace shell process (important for signal handling)
# --timeout-keep-alive: Keep connections alive
# --access-log: Enable access logging
# --log-level: Set log level
exec python3 -m uvicorn app.main:app \
    --host 0.0.0.0 \
    --port "$PORT" \
    --log-level info \
    --timeout-keep-alive 30 \
    --access-log \
    --no-use-colors


