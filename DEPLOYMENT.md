# Google Cloud Run Deployment Guide

This guide explains how to deploy the Classroom Backend to Google Cloud Run.

## Prerequisites

1. Google Cloud SDK (`gcloud`) installed and configured
2. A Google Cloud project with billing enabled
3. Required APIs enabled:
   - Cloud Run API
   - Cloud Build API
   - Container Registry API (or Artifact Registry API)
   - Vertex AI API
   - Cloud Translation API

## Setup Steps

### 1. Enable Required APIs

```bash
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable aiplatform.googleapis.com
gcloud services enable translate.googleapis.com
```

### 2. Create a Service Account (if not already exists)

The service account should have the following roles:
- `roles/aiplatform.user` - For Vertex AI
- `roles/ml.developer` - For ML services
- `roles/cloudtranslate.user` - For Translation API

```bash
# Create service account (if needed)
gcloud iam service-accounts create classroom-backend-sa \
    --display-name="Classroom Backend Service Account"

# Grant necessary permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:classroom-backend-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:classroom-backend-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/ml.developer"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:classroom-backend-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/cloudtranslate.user"
```

### 3. Configure Environment Variables

Create a `.env` file for local development (this file should NOT be committed):

```bash
# .env (for local development only)
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
SUPABASE_SERVICE_KEY=your_supabase_service_key
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=./service-account.json  # Optional for local dev
GEMINI_API_KEY=your_gemini_api_key
WOLFRAM_APP_ID=your_wolfram_app_id
YOUTUBE_API_KEY=your_youtube_api_key
```

For Cloud Run, these will be set as environment variables or secrets.

### 4. Set Cloud Run Environment Variables

You have two options:

#### Option A: Using gcloud command

```bash
gcloud run services update classroom-backend \
    --set-env-vars="SUPABASE_URL=your_url,SUPABASE_KEY=your_key,GOOGLE_CLOUD_PROJECT=your-project-id,GEMINI_API_KEY=your_key" \
    --region=us-central1
```

#### Option B: Using Secret Manager (Recommended for sensitive data)

1. Create secrets in Secret Manager:

```bash
gcloud secrets create supabase-key --data-file=- <<< "your-supabase-key"
gcloud secrets create gemini-api-key --data-file=- <<< "your-gemini-key"
```

2. Grant Cloud Run service account access:

```bash
gcloud secrets add-iam-policy-binding supabase-key \
    --member="serviceAccount:classroom-backend-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

3. Update Cloud Run service to use secrets:

```bash
gcloud run services update classroom-backend \
    --update-secrets="SUPABASE_KEY=supabase-key:latest,GEMINI_API_KEY=gemini-api-key:latest" \
    --region=us-central1
```

### 5. Build and Deploy

#### Option A: Using Cloud Build (Recommended)

1. Submit the build:

```bash
gcloud builds submit --config cloudbuild.yaml
```

2. Or set up a trigger for automatic builds on git push:

```bash
gcloud builds triggers create github \
    --name="classroom-backend-deploy" \
    --repo-name="YOUR_REPO" \
    --branch-pattern="^main$" \
    --build-config="cloudbuild.yaml"
```

#### Option B: Manual Build and Deploy

1. Build the container:

```bash
docker build -t gcr.io/YOUR_PROJECT_ID/classroom-backend:latest .
```

2. Push to Container Registry:

```bash
docker push gcr.io/YOUR_PROJECT_ID/classroom-backend:latest
```

3. Deploy to Cloud Run:

```bash
gcloud run deploy classroom-backend \
    --image gcr.io/YOUR_PROJECT_ID/classroom-backend:latest \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --service-account classroom-backend-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --max-instances 10 \
    --set-env-vars="GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID"
```

### 6. Configure Service Account for Cloud Run

The Cloud Run service will automatically use Application Default Credentials (ADC) from the attached service account. No need to upload `service-account.json` files.

```bash
gcloud run services update classroom-backend \
    --service-account classroom-backend-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com \
    --region us-central1
```

## Authentication on Cloud Run

The application automatically uses **Application Default Credentials (ADC)** on Cloud Run. This means:

- ✅ **No `service-account.json` file needed** - The service account attached to the Cloud Run service is used automatically
- ✅ **More secure** - No credentials stored in container images
- ✅ **Simpler deployment** - No need to manage credential files

The code checks for credentials in this order:
1. `GOOGLE_APPLICATION_CREDENTIALS` environment variable (for local dev)
2. Service account JSON file path from config (for local dev)
3. Application Default Credentials (automatic on Cloud Run)

## Environment Variables Required on Cloud Run

Set these as environment variables or secrets in Cloud Run:

- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_KEY` - Your Supabase anon key
- `SUPABASE_SERVICE_KEY` - Your Supabase service role key
- `GOOGLE_CLOUD_PROJECT` - Your GCP project ID
- `GEMINI_API_KEY` - Google Gemini API key
- `WOLFRAM_APP_ID` - Wolfram Alpha App ID
- `YOUTUBE_API_KEY` - YouTube Data API key
- `PORT` - Automatically set by Cloud Run (defaults to 8000)

Optional:
- `VERTEX_AI_LOCATION` - Default: `us-central1`
- `VERTEX_AI_EMBEDDING_MODEL` - Default: `text-embedding-005`
- `CORS_ORIGINS` - Comma-separated list of allowed origins

## Health Check

The application exposes a health check endpoint:

```bash
curl https://your-service-url.run.app/api/health
```

## Troubleshooting

### Service won't start

1. Check logs:
```bash
gcloud run services logs read classroom-backend --region us-central1
```

2. Verify environment variables are set:
```bash
gcloud run services describe classroom-backend --region us-central1
```

3. Check service account permissions:
```bash
gcloud projects get-iam-policy YOUR_PROJECT_ID \
    --flatten="bindings[].members" \
    --filter="bindings.members:serviceAccount:classroom-backend-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com"
```

### Authentication errors

- Ensure the service account attached to Cloud Run has the necessary IAM roles
- Verify the service account has access to Vertex AI, Translation API, etc.
- Check that `GOOGLE_CLOUD_PROJECT` is set correctly

### Connection timeouts

- Increase the timeout in Cloud Run settings (default is 300 seconds)
- Check if the service is using too much memory - increase memory allocation

## CI/CD Integration

The `cloudbuild.yaml` file is configured for automatic deployments. To set up continuous deployment:

1. Connect your GitHub repository to Cloud Build
2. Create a trigger that builds on push to main branch
3. The trigger will automatically build and deploy to Cloud Run

## Cost Optimization

- Set `--max-instances` to limit scaling
- Use `--min-instances 0` to scale to zero when not in use
- Monitor usage in Cloud Console
- Consider using Cloud Run's request-based pricing

## Security Best Practices

1. ✅ Never commit `service-account.json` to git (already in `.gitignore`)
2. ✅ Use Secret Manager for sensitive environment variables
3. ✅ Use IAM service accounts instead of user credentials
4. ✅ Enable Cloud Armor for DDoS protection (if needed)
5. ✅ Use Cloud Run's built-in authentication/authorization features

## Next Steps

- Set up monitoring and alerts in Cloud Monitoring
- Configure custom domain mapping
- Set up Cloud CDN if needed for better performance
- Configure backup and disaster recovery strategies

