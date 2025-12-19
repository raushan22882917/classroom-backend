#!/usr/bin/env python3
"""Test script for Oersted's experiment question"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000"

# Test with increased max_tokens
query_data = {
    "query": "Explain Oersted's experiment. What conclusion did Oersted draw about the relationship between electric current and magnetic field?",
    "user_id": "test_user_physics",
    "subject": "physics",
    "grade": 12,
    "max_tokens": 2000
}

print("Testing RAG endpoint with max_tokens=2000...")
response = requests.post(f"{BASE_URL}/api/rag/query", json=query_data)

print(f"Status Code: {response.status_code}")
print(f"Response Headers: {dict(response.headers)}")
print(f"\nFull Response:")
print(json.dumps(response.json(), indent=2))

# Also test direct endpoint
print("\n" + "="*80)
print("Testing Direct Gemini endpoint...")
response_direct = requests.post(f"{BASE_URL}/api/rag/query-direct", json=query_data)

print(f"Status Code: {response_direct.status_code}")
print(f"\nFull Response:")
result = response_direct.json()
print(f"Query: {result['query']}")
print(f"\nGenerated Text Length: {len(result['generated_text'])} characters")
print(f"\nGenerated Text:")
print(result['generated_text'])
