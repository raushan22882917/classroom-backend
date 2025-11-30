#!/bin/bash

# Script to grant Vertex AI permissions to service account
# Run this script to fix the 403 permission error

PROJECT_ID="buiseness-417505"
SERVICE_ACCOUNT="classroom@buiseness-417505.iam.gserviceaccount.com"
ROLE="roles/aiplatform.user"

echo "Granting Vertex AI User role to service account..."
echo "Project: $PROJECT_ID"
echo "Service Account: $SERVICE_ACCOUNT"
echo "Role: $ROLE"
echo ""

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="$ROLE"

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Successfully granted Vertex AI User role!"
    echo "Please wait 1-2 minutes for permissions to propagate, then restart your backend server."
else
    echo ""
    echo "✗ Failed to grant role. Please check:"
    echo "  1. You have permission to modify IAM policies"
    echo "  2. gcloud CLI is installed and authenticated"
    echo "  3. You're using: gcloud auth login"
    echo ""
    echo "Alternatively, use Google Cloud Console:"
    echo "https://console.cloud.google.com/iam-admin/iam?project=$PROJECT_ID"
fi




