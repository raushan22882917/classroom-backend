#!/bin/bash

# Script to grant Cloud Run service account access to the service-account-json secret
# Usage: ./grant_secret_access.sh [SERVICE_ACCOUNT_EMAIL]

set -e

PROJECT_ID="buiseness-417505"
SECRET_NAME="service-account-json"

# Get service account email from argument or from service-account.json
if [ -z "$1" ]; then
    if [ -f "service-account.json" ]; then
        SERVICE_ACCOUNT_EMAIL=$(cat service-account.json | grep -o '"client_email": "[^"]*"' | cut -d'"' -f4)
        echo "📋 Using service account from service-account.json: $SERVICE_ACCOUNT_EMAIL"
    else
        echo "❌ Error: Please provide service account email as argument or ensure service-account.json exists"
        echo "Usage: $0 [SERVICE_ACCOUNT_EMAIL]"
        echo "Example: $0 classroom@buiseness-417505.iam.gserviceaccount.com"
        exit 1
    fi
else
    SERVICE_ACCOUNT_EMAIL="$1"
fi

echo "🔐 Granting access to secret '$SECRET_NAME' for service account: $SERVICE_ACCOUNT_EMAIL"
echo "Project ID: $PROJECT_ID"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ Error: gcloud CLI is not installed"
    exit 1
fi

# Set the project
gcloud config set project $PROJECT_ID

# Grant access to the secret
echo "🔑 Granting secret accessor role..."
gcloud secrets add-iam-policy-binding $SECRET_NAME \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/secretmanager.secretAccessor" \
    --project=$PROJECT_ID

echo ""
echo "✅ Service account '$SERVICE_ACCOUNT_EMAIL' now has access to secret '$SECRET_NAME'"
echo ""
echo "Note: If you're using a different service account for Cloud Run, grant access to that account too:"
echo "  gcloud secrets add-iam-policy-binding $SECRET_NAME \\"
echo "      --member=\"serviceAccount:YOUR_CLOUD_RUN_SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com\" \\"
echo "      --role=\"roles/secretmanager.secretAccessor\" \\"
echo "      --project=$PROJECT_ID"
echo ""



