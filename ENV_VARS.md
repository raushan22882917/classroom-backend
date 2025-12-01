# Required Environment Variables for Cloud Run

These environment variables **must** be set in your Cloud Run service configuration before the application can start.

## Required Variables

1. **SUPABASE_URL** - Your Supabase project URL
   - Example: `https://xxxxx.supabase.co`

2. **SUPABASE_KEY** - Your Supabase anon/public key

3. **SUPABASE_SERVICE_KEY** - Your Supabase service role key (has admin access)

4. **GOOGLE_CLOUD_PROJECT** - Your Google Cloud Project ID
   - Example: `buiseness-417505`

5. **GEMINI_API_KEY** - Google Gemini API key
   - Get from: https://makersuite.google.com/app/apikey

6. **WOLFRAM_APP_ID** - Wolfram Alpha API App ID
   - Get from: https://products.wolframalpha.com/api/

7. **YOUTUBE_API_KEY** - YouTube Data API v3 key
   - Get from: Google Cloud Console > APIs & Services > Credentials

## Optional Variables

- **PORT** - Port to run on (Cloud Run sets this automatically, defaults to 8080)
- **GOOGLE_APPLICATION_CREDENTIALS** - Path to service account JSON (only needed for local dev)
- **VERTEX_AI_LOCATION** - Default: `us-central1`
- **CORS_ORIGINS** - Comma-separated list of allowed origins (default includes localhost and Vercel production URL)
  - Example: `http://localhost:5173,https://eduverse-dashboard-iota.vercel.app`
  - Note: When using credentials, you must specify exact origins (cannot use "*")

## How to Set in Cloud Run

```bash
gcloud run services update classroom-backend \
  --set-env-vars="SUPABASE_URL=https://xxx.supabase.co,SUPABASE_KEY=xxx,SUPABASE_SERVICE_KEY=xxx,GOOGLE_CLOUD_PROJECT=buiseness-417505,GEMINI_API_KEY=xxx,WOLFRAM_APP_ID=xxx,YOUTUBE_API_KEY=xxx" \
  --region=us-central1
```

Or use Secret Manager for sensitive values:

```bash
# Create secrets
gcloud secrets create supabase-key --data-file=supabase-key.txt
gcloud secrets create gemini-api-key --data-file=gemini-key.txt

# Grant access
gcloud secrets add-iam-policy-binding supabase-key \
  --member="serviceAccount:YOUR_SERVICE_ACCOUNT@YOUR_PROJECT.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Use in Cloud Run
gcloud run services update classroom-backend \
  --update-secrets="SUPABASE_KEY=supabase-key:latest,GEMINI_API_KEY=gemini-api-key:latest" \
  --region=us-central1
```


