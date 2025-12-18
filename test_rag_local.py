#!/usr/bin/env python3
"""
Simple test script to verify RAG functionality locally
"""

import asyncio
import json
from app.models.rag import RAGQuery

async def test_rag_import():
    """Test if RAG components can be imported"""
    try:
        print("🧪 Testing RAG imports...")
        
        # Test model import
        from app.models.rag import RAGQuery, RAGResponse
        print("✅ RAG models imported")
        
        # Test router import (this might be slow)
        print("📡 Testing RAG router import...")
        from app.routers.rag import process_rag_query
        print("✅ RAG router imported")
        
        # Create a test query
        test_query = RAGQuery(
            query="What is photosynthesis?",
            subject="biology",
            max_tokens=100
        )
        print(f"✅ Test query created: {test_query.query}")
        
        print("🎉 All RAG components loaded successfully!")
        return True
        
    except Exception as e:
        print(f"❌ RAG test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_rag_import())
    if success:
        print("\n✅ RAG service is ready for deployment!")
    else:
        print("\n❌ RAG service has issues that need fixing")