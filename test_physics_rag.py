#!/usr/bin/env python3
"""
Physics RAG Testing Script

Test the RAG functionality with physics questions after PDF processing.
"""

import asyncio
import logging
import sys
import os
from typing import Optional
from supabase import create_client, Client

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.rag_service import rag_service
from app.models.content import Subject
from app.models.rag import RAGQuery
from app.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PhysicsRAGTester:
    """Test physics RAG with user context"""
    
    def __init__(self, user_email: Optional[str] = None):
        self.user_email = user_email
        self.user_id = None
        self.supabase = None
        
    async def setup_user_context(self):
        """Setup user context for testing"""
        try:
            if not settings.supabase_url or not settings.supabase_key:
                logger.warning("Supabase not configured, testing without user context")
                return
            
            self.supabase = create_client(settings.supabase_url, settings.supabase_service_key)
            
            if self.user_email:
                # Get user by email
                response = self.supabase.table("users").select("*").eq("email", self.user_email).execute()
                
                if response.data:
                    self.user_id = response.data[0]["id"]
                    logger.info(f"✅ Found user: {self.user_email} (ID: {self.user_id})")
                else:
                    logger.warning(f"User not found: {self.user_email}")
            else:
                # Use test user
                test_email = "physics_test_user@example.com"
                response = self.supabase.table("users").select("*").eq("email", test_email).execute()
                
                if response.data:
                    self.user_id = response.data[0]["id"]
                    self.user_email = test_email
                    logger.info(f"✅ Using test user: {test_email} (ID: {self.user_id})")
                    
        except Exception as e:
            logger.warning(f"Failed to setup user context: {e}")
    
    async def log_query_activity(self, question: str, success: bool, response_data: dict = None):
        """Log query activity for user"""
        try:
            if not self.supabase or not self.user_id:
                return
            
            activity_data = {
                "question": question,
                "success": success,
                "subject": "physics"
            }
            
            if response_data:
                activity_data.update(response_data)
            
            activity_record = {
                "user_id": self.user_id,
                "activity_type": "rag_query_test",
                "activity_data": activity_data,
                "timestamp": "now()"
            }
            
            try:
                self.supabase.table("user_activities").insert(activity_record).execute()
            except Exception:
                # Table might not exist, just log locally
                logger.debug(f"Query activity: {activity_data}")
                
        except Exception as e:
            logger.debug(f"Failed to log query activity: {e}")


async def test_physics_rag(user_email: Optional[str] = None):
    """Test physics RAG with various questions"""
    
    # Setup user context
    tester = PhysicsRAGTester(user_email)
    await tester.setup_user_context()
    
    # Initialize RAG service
    logger.info("Initializing RAG service...")
    await rag_service.initialize()
    
    # Physics questions to test
    physics_questions = [
        "What is Newton's first law of motion?",
        "Explain electromagnetic induction",
        "What is the formula for kinetic energy?",
        "Define acceleration and its units",
        "What are the laws of thermodynamics?",
        "Explain the concept of electric field",
        "What is the relationship between voltage and current?",
        "Define momentum and its conservation",
        "What is the speed of light?",
        "Explain the photoelectric effect"
    ]
    
    print("\n" + "="*60)
    print("🧪 PHYSICS RAG TESTING")
    print("="*60)
    
    successful = 0
    total = len(physics_questions)
    
    for i, question in enumerate(physics_questions, 1):
        try:
            print(f"\n📝 Question {i}/{total}: {question}")
            print("-" * 50)
            
            # Create RAG query
            rag_query = RAGQuery(
                query=question,
                subject=Subject.PHYSICS,
                max_tokens=400,
                top_k=5
            )
            
            # Execute query
            response = await rag_service.query(rag_query)
            
            if response and response.generated_text:
                print(f"✅ Answer: {response.generated_text}")
                print(f"🎯 Confidence: {response.confidence:.2f}")
                print(f"📚 Sources: {len(response.sources)} found")
                successful += 1
                
                # Log successful query
                await tester.log_query_activity(question, True, {
                    "confidence": response.confidence,
                    "sources_count": len(response.sources)
                })
            else:
                print("❌ No answer generated")
                await tester.log_query_activity(question, False)
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "="*60)
    print(f"📊 RESULTS: {successful}/{total} successful ({successful/total*100:.1f}%)")
    print("="*60)
    
    return successful, total


async def interactive_physics_chat(user_email: Optional[str] = None):
    """Interactive physics Q&A session"""
    
    print("\n" + "="*60)
    print("💬 INTERACTIVE PHYSICS CHAT")
    print("="*60)
    print("Ask physics questions! Type 'quit' to exit.")
    
    # Setup user context
    tester = PhysicsRAGTester(user_email)
    await tester.setup_user_context()
    
    if tester.user_id:
        print(f"👤 Logged in as: {tester.user_email}")
    
    # Initialize RAG service
    await rag_service.initialize()
    
    while True:
        try:
            question = input("\n🤔 Your physics question: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if not question:
                continue
            
            print("🔍 Searching for answer...")
            
            # Create RAG query
            rag_query = RAGQuery(
                query=question,
                subject=Subject.PHYSICS,
                max_tokens=500,
                top_k=5
            )
            
            # Execute query
            response = await rag_service.query(rag_query)
            
            if response and response.generated_text:
                print(f"\n🤖 Answer:")
                print(f"{response.generated_text}")
                print(f"\n📊 Confidence: {response.confidence:.2f}")
                print(f"📚 Sources found: {len(response.sources)}")
            else:
                print("❌ Sorry, I couldn't find an answer to that question.")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


async def main():
    """Main function"""
    print("🚀 Physics RAG Testing Tool")
    print("\nChoose an option:")
    print("1. Run automated tests")
    print("2. Interactive chat")
    print("3. Both")
    
    try:
        choice = input("\nEnter choice (1/2/3): ").strip()
        
        if choice in ['1', '3']:
            await test_physics_rag()
        
        if choice in ['2', '3']:
            await interactive_physics_chat()
        
        if choice not in ['1', '2', '3']:
            print("Invalid choice. Running automated tests...")
            await test_physics_rag()
            
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())