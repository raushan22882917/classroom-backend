#!/bin/bash
# Startup script for Cloud Run with better error handling

# Don't exit on error - we want to show all errors and attempt to start
set +e
set -u  # Still fail on undefined variables

echo "=========================================="
echo "Starting Classroom Backend API"
echo "=========================================="

# Read PORT from environment (Cloud Run sets this, default to 8080)
PORT=${PORT:-8080}
echo "PORT: $PORT"
export PORT

# Verify PORT is a number (critical - must exit if invalid)
if ! [[ "$PORT" =~ ^[0-9]+$ ]]; then
    echo "ERROR: PORT must be a number, got: $PORT"
    exit 1
fi

# Verify PORT is in valid range
if [ "$PORT" -lt 1 ] || [ "$PORT" -gt 65535 ]; then
    echo "ERROR: PORT must be between 1 and 65535, got: $PORT"
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
IMPORT_OUTPUT=$(python3 -c "from app.main import app; print('✓ App import successful')" 2>&1)
IMPORT_EXIT=$?

if [ $IMPORT_EXIT -eq 0 ]; then
    echo "✓ Application can be imported"
else
    echo "⚠ Warning: App import check had issues:"
    echo "$IMPORT_OUTPUT" | head -20
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
# This is the critical command - if it fails, we exit
set +e  # Temporarily disable exit on error for the exec
exec python3 -m uvicorn app.main:app \
    --host 0.0.0.0 \
    --port "$PORT" \
    --log-level info \
    --timeout-keep-alive 30 \
    --access-log \
    --no-use-colors

# If we get here, exec failed (shouldn't happen, but just in case)
echo "ERROR: Failed to start uvicorn server"
exit 1


