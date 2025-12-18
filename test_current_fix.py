#!/usr/bin/env python3
"""
Test the current electricity question fix
"""

import requests
import json

BASE_URL = "https://classroom-backend-121270846496.europe-west1.run.app"

def test_current_question():
    """Test the specific current question that was truncated"""
    
    print("🔌 Testing Current Electricity Question")
    print("=" * 50)
    
    test_query = {
        "query": "What is current in electricity? Explain with examples.",
        "subject": "physics",
        "max_tokens": 500
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/rag/query",
            json=test_query,
            timeout=60,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ SUCCESS!")
            print(f"Mode: {data.get('metadata', {}).get('mode', 'unknown')}")
            print(f"Confidence: {data.get('confidence', 0):.2f}")
            print(f"Response length: {len(data.get('generated_text', ''))}")
            print(f"\nFull Response:")
            print("-" * 30)
            print(data.get('generated_text', ''))
            print("-" * 30)
            
            # Check if response is complete (not truncated)
            response_text = data.get('generated_text', '')
            if len(response_text) > 100 and not response_text.endswith('...'):
                print("✅ Response appears complete!")
            else:
                print("⚠️ Response may still be truncated")
                
        else:
            print(f"❌ Error {response.status_code}")
            try:
                error_data = response.json()
                print(f"Details: {error_data}")
            except:
                print(f"Raw: {response.text}")
                
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_current_question()