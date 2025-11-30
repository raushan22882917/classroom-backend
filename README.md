# Eduverse Dashboard - Backend API

Backend API for the Eduverse Dashboard educational platform built with FastAPI, integrating RAG pipelines, LLM capabilities, autonomous AI agents, and adaptive learning features.

## Prerequisites

- Python 3.11 or higher
- Google Cloud SDK (for GCP services)
- Service account JSON file for Google Cloud authentication

## Setup

### 1. Create Virtual Environment

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Copy the example environment file and fill in your API keys:

```bash
cp .env.example .env
```

Edit `.env` and add your credentials:
- Supabase URL and keys
- Google Cloud project ID
- Gemini API key
- Wolfram Alpha App ID
- YouTube API key
- Pinecone API key and environment
- Redis configuration (if using)

### 4. Set Up Google Cloud Authentication

Place your service account JSON file in the backend directory:

```bash
# Download from Google Cloud Console
# IAM & Admin > Service Accounts > Create Key (JSON)
mv ~/Downloads/service-account-key.json ./service-account.json
```

Update the `.env` file:
```
GOOGLE_APPLICATION_CREDENTIALS=./service-account.json
```

### 5. Run the Development Server

```bash
python -m app.main
```

Or using uvicorn directly:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Configuration management
│   ├── models/              # Pydantic models and schemas
│   │   ├── __init__.py
│   │   └── base.py          # Base models and enums
│   ├── routers/             # API route handlers
│   │   ├── __init__.py
│   │   └── health.py        # Health check endpoints
│   ├── services/            # Business logic services
│   │   └── __init__.py
│   └── utils/               # Utility functions
│       ├── __init__.py
│       └── exceptions.py    # Custom exception handlers
├── requirements.txt         # Python dependencies
├── .env.example            # Example environment variables
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

## API Endpoints

### Health Check

- `GET /api/health` - Basic health check
- `GET /api/health/config` - Configuration status (non-sensitive)

### API Endpoints

- `/api/health` - Health check endpoints
- `/api/rag/*` - RAG pipeline queries and content retrieval
- `/api/doubt/*` - AI-powered doubt solver (text, image, voice)
- `/api/homework/*` - Homework assistant with graduated hints
- `/api/microplan/*` - Adaptive learning micro-plans
- `/api/exam/*` - Exam creation and management
- `/api/quiz/*` - Quiz system
- `/api/videos/*` - Video content and transcript management
- `/api/hots/*` - Higher Order Thinking Skills questions
- `/api/admin/*` - Admin panel endpoints
- `/api/progress/*` - Student progress tracking
- `/api/analytics/*` - Analytics and reporting
- `/api/ai-tutoring/*` - AI tutoring agent endpoints
- `/api/translation/*` - Multi-language translation
- `/api/teacher/*` - Teacher tools and management
- `/api/messages/*` - Messaging system
- `/api/notification/*` - Notification system
- `/api/wellbeing/*` - Student wellbeing features

See the main [README.md](../README.md) and [AI Features Documentation](../docs/AI_FEATURES.md) for detailed information about AI capabilities.

## Development

### Code Style

Follow PEP 8 guidelines. Use type hints for all functions.

### Adding New Endpoints

1. Create a new router in `app/routers/`
2. Define Pydantic models in `app/models/`
3. Implement business logic in `app/services/`
4. Register the router in `app/main.py`

## Environment Variables

See `.env.example` for all required environment variables.

Key configurations:
- `SUPABASE_URL`, `SUPABASE_KEY` - Database connection
- `GEMINI_API_KEY` - LLM for content generation
- `WOLFRAM_APP_ID` - Math verification
- `YOUTUBE_API_KEY` - Video curation
- `PINECONE_API_KEY` - Vector database
- `GOOGLE_CLOUD_PROJECT` - GCP project ID

## Rate Limiting

API endpoints are rate-limited to 100 requests per minute per IP address by default. Configure via `RATE_LIMIT_PER_MINUTE` environment variable.

## CORS Configuration

CORS is configured to allow requests from the frontend. Update `CORS_ORIGINS` in `.env` to add additional origins.

## Deployment

The application is designed to run on Google Cloud Run. See the [Deployment Guide](../docs/DEPLOYMENT.md) for detailed deployment instructions.

## Related Documentation

- [Main README](../README.md) - Project overview and setup
- [AI Features Documentation](../docs/AI_FEATURES.md) - Detailed AI capabilities
- [Deployment Guide](../docs/DEPLOYMENT.md) - Production deployment
- [Google Cloud Setup](./GOOGLE_CLOUD_AUTH_SETUP.md) - GCP authentication
- [Vertex AI Vector Search Setup](./VERTEX_AI_VECTOR_SEARCH_SETUP.md) - Vector database setup

## License

MIT License - See [LICENSE](../LICENSE) file for details.
