#!/usr/bin/env python3
"""
Test content indexing functionality
"""

import asyncio
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.models.content import ContentItem
from app.models.base import Subject
from app.services.content_indexer import content_indexer

async def test_content_indexing():
    """Test content indexing with a sample content item"""
    
    print("🔍 Testing Content Indexing")
    print("=" * 50)
    
    from datetime import datetime
    from app.models.content import ContentType, DifficultyLevel
    
    # Create a sample content item
    content_item = ContentItem(
        id="test_content_123",
        type=ContentType.NCERT,
        title="Test Physics Content",
        content_text="Electric current is the flow of electric charge through a conductor. It is measured in amperes (A). The relationship between current (I), voltage (V), and resistance (R) is given by Ohm's law: V = I × R. This fundamental principle helps us understand how electricity works in circuits.",
        subject=Subject.PHYSICS,
        chapter="Current Electricity",
        difficulty=DifficultyLevel.MEDIUM,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    print(f"Content ID: {content_item.id}")
    print(f"Title: {content_item.title}")
    print(f"Subject: {content_item.subject}")
    print(f"Content length: {len(content_item.content_text)} characters")
    print()
    
    # Progress callback
    async def progress_callback(message: str, progress: int):
        print(f"Progress: {progress}% - {message}")
    
    try:
        # Test indexing
        print("Starting indexing...")
        result = await content_indexer.index_content_item(
            content_item,
            update_progress_callback=progress_callback
        )
        
        print("\nIndexing Result:")
        print(f"Success: {result.get('success', False)}")
        print(f"Message: {result.get('message', 'No message')}")
        print(f"Chunks created: {result.get('chunks_created', 0)}")
        print(f"Documents indexed: {result.get('documents_indexed', 0)}")
        
        if result.get('error'):
            print(f"Error: {result['error']}")
        
        if result.get('success'):
            print("✅ Content indexing test passed!")
        else:
            print("❌ Content indexing test failed!")
            
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_content_indexing())