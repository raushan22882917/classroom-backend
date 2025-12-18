# Vertex AI Search Setup Guide

## Overview
This guide explains how to set up Google Vertex AI Search for content indexing in your RAG system.

## Prerequisites
- Google Cloud Project with billing enabled
- Vertex AI API enabled
- Discovery Engine API enabled
- Service account with appropriate permissions

## Step 1: Enable Required APIs

```bash
gcloud services enable discoveryengine.googleapis.com
gcloud services enable aiplatform.googleapis.com
```

## Step 2: Create a Data Store

1. Go to the [Vertex AI Search Console](https://console.cloud.google.com/ai/search)
2. Click "Create Data Store"
3. Choose "Unstructured documents" as the data type
4. Select "Global" as the region
5. Name your data store (e.g., "classroom-content")
6. Note the Data Store ID from the URL or details page

## Step 3: Create a Search Engine

1. In the Vertex AI Search Console, click "Create App"
2. Choose "Search" as the app type
3. Select your data store created in Step 2
4. Name your search engine (e.g., "classroom-search")
5. Note the Search Engine ID from the URL or details page

## Step 4: Update Environment Variables

Add these to your `.env` file:

```env
# Google RAG Configuration (Vertex AI Search)
VERTEX_SEARCH_ENGINE_ID=your_search_engine_id_here
VERTEX_DATA_STORE_ID=your_data_store_id_here
GCS_BUCKET_NAME=your_bucket_name_here  # Optional: for document storage
```

## Step 5: Service Account Permissions

Ensure your service account has these roles:
- `roles/discoveryengine.admin` - For managing documents
- `roles/aiplatform.user` - For Vertex AI operations
- `roles/storage.admin` - If using GCS bucket (optional)

## Step 6: Test the Setup

Run the content indexing test:

```bash
python3 test_content_indexing.py
```

## Troubleshooting

### Common Issues

1. **"Data store not found" error**
   - Verify the `VERTEX_DATA_STORE_ID` is correct
   - Check that the data store exists in your project

2. **"Permission denied" error**
   - Verify service account has required roles
   - Check that APIs are enabled

3. **"Search engine not found" error**
   - Verify the `VERTEX_SEARCH_ENGINE_ID` is correct
   - Ensure the search engine is properly configured

### Fallback Mode

If Vertex AI Search is not configured, the system will use fallback mode:
- Content will be uploaded to the database
- Indexing will be marked as successful
- RAG queries will use Gemini with grounding instead of search

## Cost Considerations

- Vertex AI Search charges per document and per search query
- Consider setting up quotas and monitoring usage
- For development, you can use the fallback mode to avoid costs

## Next Steps

Once configured:
1. Upload content through the admin panel
2. Monitor indexing progress in the content status endpoint
3. Test RAG queries to verify content is searchable
4. Set up monitoring and alerting for production use