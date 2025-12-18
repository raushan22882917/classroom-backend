#!/bin/bash
cd "$(dirname "$0")"
source venv_interactive_learning/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000