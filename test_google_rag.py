#!/usr/bin/env python3
"""
Test the new Google RAG service locally
"""

import asyncio
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

async def test_google_rag():
    """Test Google RAG service"""
    try:
        print("🧪 Testing Google RAG Service")
        print("=" * 50)
        
        # Import the service
        from app.services.google_rag_service import google_rag_service
        from app.models.rag import RAGQuery
        from app.models.base import Subject
        
        print("✅ Imports successful")
        
        # Initialize the service
        print("🔧 Initializing Google RAG service...")
        await google_rag_service.initialize()
        print("✅ Service initialized")
        
        # Test queries
        test_queries = [
            {
                "query": "What is the Pythagorean theorem?",
                "subject": Subject.MATHEMATICS,
                "description": "Math query"
            },
            {
                "query": "Explain photosynthesis",
                "subject": Subject.BIOLOGY,
                "description": "Biology query"
            },
            {
                "query": "What is gravity?",
                "subject": Subject.PHYSICS,
                "description": "Physics query"
            }
        ]
        
        for i, test_case in enumerate(test_queries, 1):
            print(f"\n🧪 Test {i}: {test_case['description']}")
            print(f"   Query: {test_case['query']}")
            
            try:
                # Create RAG query
                rag_query = RAGQuery(
                    query=test_case["query"],
                    subject=test_case["subject"],
                    max_tokens=200
                )
                
                # Process query
                response = await google_rag_service.query(rag_query)
                
                print(f"   ✅ Success!")
                print(f"   Mode: {response.metadata.get('mode', 'unknown')}")
                print(f"   Confidence: {response.confidence:.2f}")
                print(f"   Response length: {len(response.generated_text)}")
                print(f"   Preview: {response.generated_text[:100]}...")
                
                if response.sources:
                    print(f"   Sources: {len(response.sources)}")
                
            except Exception as e:
                print(f"   ❌ Failed: {e}")
        
        print(f"\n🎉 Google RAG service test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_google_rag())