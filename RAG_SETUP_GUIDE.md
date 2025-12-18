# Physics RAG System

Simple RAG system for physics questions using Supabase and Gemini 2.5 Flash.

## Files
- **`modern_supabase_rag.py`** - Main RAG system with AI
- **`simple_supabase_rag.py`** - Fallback without AI
- **`leph104.pdf`** - Physics textbook
- **`.env`** - Configuration

## Setup
```bash
source venv_interactive_learning/bin/activate
pip install sentence-transformers PyPDF2
python modern_supabase_rag.py
```

## Usage
- Automatically processes PDF and uploads to Supabase
- Ask physics questions interactively
- Type 'quit' to exit