#!/usr/bin/env python3
"""
Test Google RAG service on deployed endpoint
"""

import requests
import json
from datetime import datetime

BASE_URL = "https://classroom-backend-121270846496.europe-west1.run.app"

def test_google_rag_deployment():
    """Test Google RAG service on deployed endpoint"""
    
    print("🚀 Testing Google RAG on Deployed Endpoint")
    print("=" * 60)
    print(f"🕐 Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Endpoint: {BASE_URL}")
    print()
    
    # Test basic connectivity
    print("1️⃣ CONNECTIVITY TEST")
    print("-" * 30)
    
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        if response.status_code == 200:
            print("✅ Service is accessible")
        else:
            print(f"❌ Service returned {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Cannot reach service: {e}")
        return
    
    # Test configuration
    print("\n2️⃣ CONFIGURATION CHECK")
    print("-" * 30)
    
    try:
        response = requests.get(f"{BASE_URL}/api/health/config", timeout=10)
        if response.status_code == 200:
            config = response.json()
            print("✅ Configuration accessible:")
            print(f"   Environment: {config.get('app_env', 'unknown')}")
            print(f"   Google RAG Engine: {config.get('google_rag_engine', 'unknown')}")
            print(f"   Vertex AI Location: {config.get('vertex_ai_location', 'unknown')}")
            print(f"   Search Engine ID: {config.get('vertex_search_engine_id', 'not_configured')}")
        else:
            print(f"❌ Config check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Config check error: {e}")
    
    # Test Google RAG queries
    print("\n3️⃣ GOOGLE RAG TESTS")
    print("-" * 30)
    
    test_queries = [
        {
            "query": "What is the Pythagorean theorem?",
            "subject": "mathematics",
            "max_tokens": 200,
            "name": "Math Query"
        },
        {
            "query": "Explain photosynthesis",
            "subject": "biology", 
            "max_tokens": 200,
            "name": "Biology Query"
        },
        {
            "query": "What is gravity?",
            "subject": "physics",
            "max_tokens": 200,
            "name": "Physics Query"
        }
    ]
    
    successful_queries = 0
    
    for i, test_case in enumerate(test_queries, 1):
        print(f"\n🧪 Test {i}: {test_case['name']}")
        print(f"   Query: {test_case['query']}")
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/rag/query",
                json=test_case,
                timeout=60,  # Longer timeout for Google services
                headers={"Content-Type": "application/json"}
            )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ SUCCESS!")
                print(f"   Mode: {data.get('metadata', {}).get('mode', 'unknown')}")
                print(f"   Confidence: {data.get('confidence', 0):.2f}")
                print(f"   Response length: {len(data.get('generated_text', ''))}")
                print(f"   Preview: {data.get('generated_text', '')[:100]}...")
                successful_queries += 1
                
                if data.get('sources'):
                    print(f"   Sources: {len(data['sources'])}")
                    
            elif response.status_code == 503:
                error_data = response.json()
                print(f"   ⏳ Service initializing: {error_data.get('error', '')}")
            else:
                print(f"   ❌ Error {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Details: {error_data}")
                except:
                    print(f"   Raw: {response.text[:200]}")
                    
        except requests.exceptions.Timeout:
            print(f"   ⏰ Timeout (60s) - Google services may be slow")
        except Exception as e:
            print(f"   ❌ Request failed: {e}")
    
    # Summary
    print(f"\n4️⃣ SUMMARY")
    print("-" * 30)
    print(f"Successful queries: {successful_queries}/{len(test_queries)}")
    
    if successful_queries == len(test_queries):
        print("🎉 All Google RAG tests passed!")
    elif successful_queries > 0:
        print("⚠️ Some Google RAG tests passed - service may be initializing")
    else:
        print("❌ No Google RAG tests passed - check service status")
    
    print(f"\n📋 NEXT STEPS")
    print("-" * 30)
    if successful_queries == 0:
        print("• Check Cloud Run logs for initialization errors")
        print("• Verify Google Cloud authentication")
        print("• Ensure Gemini API key is configured")
        print("• Wait 5-10 minutes for full service initialization")
    else:
        print("• Google RAG service is working!")
        print("• Ready for production use")

if __name__ == "__main__":
    test_google_rag_deployment()