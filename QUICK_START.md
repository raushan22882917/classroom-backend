# Quick Start: Fixing Cloud Run Deployment

## The Problem

If you're seeing this error:
```
The user-provided container failed to start and listen on the port
```

This means **required environment variables are missing**. The application cannot start without them.

## Quick Fix

### Step 1: Set Required Environment Variables

Run this command **before** deploying (replace with your actual values):

```bash
gcloud run services update classroom-backend \
  --set-env-vars="\
SUPABASE_URL=https://your-project.supabase.co,\
SUPABASE_KEY=your-supabase-anon-key,\
SUPABASE_SERVICE_KEY=your-supabase-service-key,\
GOOGLE_CLOUD_PROJECT=buiseness-417505,\
GEMINI_API_KEY=your-gemini-api-key,\
WOLFRAM_APP_ID=your-wolfram-app-id,\
YOUTUBE_API_KEY=your-youtube-api-key\
" \
  --region=us-central1
```

### Step 2: Verify Variables Are Set

```bash
gcloud run services describe classroom-backend \
  --region=us-central1 \
  --format="value(spec.template.spec.containers[0].env)"
```

### Step 3: Redeploy

```bash
gcloud builds submit --config cloudbuild.yaml
```

## Alternative: Set Variables During First Deployment

Update `cloudbuild.yaml` to include environment variables in the deploy step:

```yaml
- '--set-env-vars'
- 'PORT=8080,SUPABASE_URL=...,SUPABASE_KEY=...,...'
```

## Required Environment Variables

| Variable | Description | Where to Get |
|----------|-------------|--------------|
| `SUPABASE_URL` | Supabase project URL | Supabase Dashboard > Settings > API |
| `SUPABASE_KEY` | Supabase anon/public key | Supabase Dashboard > Settings > API |
| `SUPABASE_SERVICE_KEY` | Supabase service role key | Supabase Dashboard > Settings > API |
| `GOOGLE_CLOUD_PROJECT` | GCP Project ID | Already have: `buiseness-417505` |
| `GEMINI_API_KEY` | Google Gemini API key | https://makersuite.google.com/app/apikey |
| `WOLFRAM_APP_ID` | Wolfram Alpha App ID | https://products.wolframalpha.com/api/ |
| `YOUTUBE_API_KEY` | YouTube Data API key | GCP Console > APIs & Services > Credentials |

## Troubleshooting

1. **Check logs**: The startup script now shows which variables are missing
2. **Verify values**: Make sure there are no typos in variable names
3. **Check quotes**: When setting multiple vars, don't use spaces around commas
4. **Secret Manager**: For sensitive values, use Secret Manager instead (see DEPLOYMENT.md)

## Next Steps

Once environment variables are set:
- The container will start successfully
- The startup script will verify all variables are present
- Uvicorn will start listening on port 8080
- Cloud Run health checks will pass

