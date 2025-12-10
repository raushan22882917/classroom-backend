#!/bin/bash

# Script to upload service-account.json to Google Cloud Secret Manager
# Usage: ./upload_service_account_secret.sh

set -e

PROJECT_ID="buiseness-417505"
SECRET_NAME="service-account-json"
SECRET_FILE="service-account.json"

echo "🔐 Uploading service account JSON to Google Cloud Secret Manager..."
echo "Project ID: $PROJECT_ID"
echo "Secret Name: $SECRET_NAME"
echo ""

# Check if service-account.json exists
if [ ! -f "$SECRET_FILE" ]; then
    echo "❌ Error: $SECRET_FILE not found in current directory"
    exit 1
fi

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ Error: gcloud CLI is not installed"
    echo "Install it from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Set the project
gcloud config set project $PROJECT_ID

# Check if secret already exists
if gcloud secrets describe $SECRET_NAME --project=$PROJECT_ID &> /dev/null; then
    echo "⚠️  Secret '$SECRET_NAME' already exists. Updating..."
    gcloud secrets versions add $SECRET_NAME --data-file=$SECRET_FILE --project=$PROJECT_ID
    echo "✅ Secret updated successfully!"
else
    echo "📝 Creating new secret '$SECRET_NAME'..."
    gcloud secrets create $SECRET_NAME --data-file=$SECRET_FILE --project=$PROJECT_ID
    echo "✅ Secret created successfully!"
fi

# Get the service account email from the JSON file
SERVICE_ACCOUNT_EMAIL=$(cat $SECRET_FILE | grep -o '"client_email": "[^"]*"' | cut -d'"' -f4)
echo ""
echo "📋 Service Account: $SERVICE_ACCOUNT_EMAIL"
echo ""
echo "✅ Done! The secret is now available in Secret Manager."
echo ""
echo "Next steps:"
echo "1. Grant Cloud Run service account access to the secret:"
echo "   gcloud secrets add-iam-policy-binding $SECRET_NAME \\"
echo "       --member=\"serviceAccount:$SERVICE_ACCOUNT_EMAIL\" \\"
echo "       --role=\"roles/secretmanager.secretAccessor\" \\"
echo "       --project=$PROJECT_ID"
echo ""
echo "2. Update your Cloud Run service to mount the secret (see cloudbuild.yaml)"
echo ""




