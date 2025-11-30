#!/bin/bash
# Startup script for Cloud Run with better error handling

# Don't exit on error - we want to catch and show Python errors
# set -e

echo "=========================================="
echo "Starting Classroom Backend API"
echo "=========================================="

# Read PORT from environment (Cloud Run sets this)
PORT=${PORT:-8080}
echo "PORT: $PORT"

# Check required environment variables
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
    if [ -z "${!var}" ]; then
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
    echo "The application may fail to start or function correctly."
    echo "Please set these in Cloud Run service configuration."
    echo "=========================================="
    echo ""
fi

echo ""
echo "Starting uvicorn server on port $PORT..."
echo ""

# Test application startup using test script
echo "Testing application startup..."
if python3 test_startup.py 2>&1; then
    echo "✓ Startup tests passed"
else
    echo ""
    echo "=========================================="
    echo "ERROR: Application startup tests failed!"
    echo "=========================================="
    echo "Check the output above for details."
    echo ""
    echo "Common issues:"
    echo "  1. Missing required environment variables"
    echo "  2. Configuration validation errors"
    echo "  3. Python import errors"
    echo ""
    echo "=========================================="
    exit 1
fi

echo ""
echo "Starting uvicorn server..."
echo ""

# Start uvicorn with the app - use exec to replace shell process
exec python3 -m uvicorn app.main:app --host 0.0.0.0 --port $PORT --log-level info


