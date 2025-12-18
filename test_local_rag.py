#!/usr/bin/env python3
"""
Test RAG service locally to verify the fix works
"""

import asyncio
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.models.rag import RAGQuery, Subject
from app.services.google_rag_service import google_rag_service

async def test_local_rag():
    """Test the RAG service locally"""
    
    print("🔌 Testing RAG Service Locally")
    print("=" * 50)
    
    # Initialize the service
    await google_rag_service.initialize()
    
    # Create test query
    query = RAGQuery(
        query="What is current in electricity? Explain with examples and provide a detailed answer.",
        subject=Subject.PHYSICS,
        max_tokens=500
    )
    
    try:
        response = await google_rag_service.query(query)
        
        print(f"✅ SUCCESS!")
        print(f"Mode: {response.metadata.get('mode', 'unknown')}")
        print(f"Confidence: {response.confidence:.2f}")
        print(f"Response length: {len(response.generated_text)}")
        print(f"\nFull Response:")
        print("-" * 30)
        print(response.generated_text)
        print("-" * 30)
        
        # Check if response is complete
        if len(response.generated_text) > 200:
            print("✅ Response appears complete!")
        else:
            print("⚠️ Response may still be truncated")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_local_rag())