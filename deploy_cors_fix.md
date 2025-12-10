# CORS Fix Deployment Guide

## Issue
Frontend at `http://localhost:8080` is blocked by CORS policy when accessing the deployed backend.

## Solution Applied

### 1. Updated CORS Configuration in `app/main.py`

- Added `http://localhost:8080` to required origins
- Added comprehensive localhost origins for development
- Added CORS middleware with debugging
- Added OPTIONS handler for preflight requests

### 2. Updated Environment Variables in `.env`

- Fixed CORS_ORIGINS to include `http://localhost:8080`
- Removed trailing slash from Vercel URL

### 3. Added CORS Debugging

- Added middleware to log CORS requests
- Added test endpoints for CORS verification

## Deployment Steps

### Option 1: Redeploy to Cloud Run

```bash
# If using gcloud CLI
gcloud run deploy classroom-backend \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars CORS_ORIGINS="http://localhost:5173,http://localhost:3000,http://localhost:8080,https://eduverse-dashboard-iota.vercel.app"
```

### Option 2: Update Environment Variables Only

If the backend supports runtime environment variable updates:

```bash
gcloud run services update classroom-backend \
  --region us-central1 \
  --set-env-vars CORS_ORIGINS="http://localhost:5173,http://localhost:3000,http://localhost:8080,https://eduverse-dashboard-iota.vercel.app"
```

### Option 3: Quick Test

Test the CORS fix with a simple curl command:

```bash
# Test preflight request
curl -X OPTIONS \
  -H "Origin: http://localhost:8080" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type" \
  https://classroom-backend-821372121985.us-central1.run.app/api/magic-learn/cors-test

# Should return CORS headers in response
```

## Verification

After deployment, test these endpoints:

1. **Health Check**: `GET /api/magic-learn/health`
2. **CORS Test**: `GET /api/magic-learn/cors-test`
3. **DrawInAir**: `POST /api/magic-learn/draw-in-air/recognize`

## Frontend Testing

From your frontend at `http://localhost:8080`, try:

```javascript
// Test CORS
fetch('https://classroom-backend-821372121985.us-central1.run.app/api/magic-learn/cors-test')
  .then(response => response.json())
  .then(data => console.log('CORS test successful:', data))
  .catch(error => console.error('CORS test failed:', error));
```

## Immediate Workaround

If deployment takes time, you can temporarily disable CORS in your browser for testing:

```bash
# Chrome with disabled security (for testing only)
google-chrome --disable-web-security --user-data-dir="/tmp/chrome_dev_test"
```

**⚠️ Warning**: Only use this for development testing, never in production.

## Production Considerations

For production deployment:

1. Remove localhost origins from CORS configuration
2. Add only your production frontend domains
3. Remove CORS debugging logs
4. Ensure proper SSL/TLS configuration

## Files Modified

- `app/main.py` - CORS configuration and middleware
- `app/routers/magic_learn.py` - OPTIONS handler and test endpoints
- `.env` - CORS_ORIGINS environment variable

The backend should now accept requests from `http://localhost:8080` after redeployment.