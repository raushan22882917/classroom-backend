#!/usr/bin/env python3
"""
Supabase RAG Testing Script

Test the RAG functionality with physics content using your existing Supabase database.
This script will:
1. Connect to Supabase
2. Process the physics PDF
3. Store content in the database
4. Test RAG queries
5. Track user interactions
"""

import asyncio
import logging
import sys
import os
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from supabase import create_client, Client

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.rag_service import rag_service
from app.models.content import Subject
from app.models.rag import RAGQuery
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SupabaseRAGTester:
    """Test RAG functionality with Supabase integration"""
    
    def __init__(self, user_email: Optional[str] = None):
        self.user_email = user_email or "physics_test_user@example.com"
        self.user_id = None
        self.supabase: Optional[Client] = None
        self.content_id = None
        
    async def setup_supabase(self):
        """Setup Supabase connection"""
        try:
            if not settings.supabase_url or not settings.supabase_service_key:
                raise Exception("Supabase configuration missing")
            
            self.supabase = create_client(settings.supabase_url, settings.supabase_service_key)
            logger.info("✅ Connected to Supabase")
            
            # Setup test user
            await self.setup_test_user()
            
        except Exception as e:
            logger.error(f"❌ Failed to setup Supabase: {e}")
            raise
    
    async def setup_test_user(self):
        """Setup or get test user"""
        try:
            # Check if user exists
            response = self.supabase.table("users").select("*").eq("email", self.user_email).execute()
            
            if response.data:
                self.user_id = response.data[0]["id"]
                logger.info(f"✅ Found existing user: {self.user_email}")
            else:
                # Create test user
                user_data = {
                    "id": str(uuid.uuid4()),
                    "email": self.user_email,
                    "name": "Physics Test User",
                    "role": "student",
                    "class_grade": 12,
                    "subjects": ["physics"],
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
                
                response = self.supabase.table("users").insert(user_data).execute()
                
                if response.data:
                    self.user_id = response.data[0]["id"]
                    logger.info(f"✅ Created test user: {self.user_email}")
                else:
                    logger.warning("Failed to create user, continuing without user context")
                    
        except Exception as e:
            logger.warning(f"Error setting up user: {e}")
    
    async def process_physics_pdf(self):
        """Process the physics PDF and store in Supabase"""
        try:
            logger.info("📖 Processing physics PDF...")
            
            # Check if PDF exists
            pdf_path = "leph104.pdf"
            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"PDF file not found: {pdf_path}")
            
            # Read PDF content
            with open(pdf_path, 'rb') as f:
                pdf_content = f.read()
            
            logger.info(f"📄 Read PDF: {len(pdf_content)} bytes")
            
            # Extract text from PDF (simple extraction for testing)
            import PyPDF2
            from io import BytesIO
            
            pdf_file = BytesIO(pdf_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text_parts = []
            for page in pdf_reader.pages:
                text_parts.append(page.extract_text())
            
            content_text = "\n\n".join(text_parts)
            logger.info(f"📝 Extracted text: {len(content_text)} characters")
            
            # Store content in Supabase
            content_data = {
                "id": str(uuid.uuid4()),
                "type": "pdf",
                "subject": "physics",
                "chapter": "Physics Concepts",
                "difficulty": "medium",
                "title": "Physics Textbook - leph104.pdf",
                "content_text": content_text,
                "metadata": {
                    "source": "physics_textbook",
                    "filename": "leph104.pdf",
                    "file_size": len(pdf_content),
                    "uploaded_by": self.user_id,
                    "processed_at": datetime.now().isoformat()
                },
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            response = self.supabase.table("content").insert(content_data).execute()
            
            if response.data:
                self.content_id = response.data[0]["id"]
                logger.info(f"✅ Content stored in Supabase: {self.content_id}")
                return True
            else:
                logger.error("❌ Failed to store content in Supabase")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error processing PDF: {e}")
            return False
    
    async def test_rag_queries(self):
        """Test RAG queries with physics questions"""
        try:
            logger.info("🧪 Testing RAG queries...")
            
            # Initialize RAG service
            await rag_service.initialize()
            
            # Physics test questions
            test_questions = [
                "What is Newton's first law of motion?",
                "Explain electromagnetic induction",
                "What is the formula for kinetic energy?",
                "Define acceleration and its units",
                "What are the laws of thermodynamics?",
                "Explain the concept of electric field",
                "What is Ohm's law?",
                "Define momentum and its conservation",
                "What is the speed of light?",
                "Explain the photoelectric effect"
            ]
            
            results = {
                "total_questions": len(test_questions),
                "successful_queries": 0,
                "failed_queries": 0,
                "results": []
            }
            
            print("\n" + "="*80)
            print("🧪 PHYSICS RAG TESTING")
            print("="*80)
            
            for i, question in enumerate(test_questions, 1):
                try:
                    print(f"\n📝 Question {i}/{len(test_questions)}: {question}")
                    print("-" * 60)
                    
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
                        
                        results["successful_queries"] += 1
                        results["results"].append({
                            "question": question,
                            "answer": response.generated_text,
                            "confidence": response.confidence,
                            "sources_count": len(response.sources),
                            "success": True
                        })
                        
                        # Log query to Supabase
                        await self.log_query_result(question, response, True)
                        
                    else:
                        print("❌ No answer generated")
                        results["failed_queries"] += 1
                        results["results"].append({
                            "question": question,
                            "success": False,
                            "error": "No response generated"
                        })
                        
                        await self.log_query_result(question, None, False)
                        
                except Exception as e:
                    print(f"❌ Error: {e}")
                    results["failed_queries"] += 1
                    results["results"].append({
                        "question": question,
                        "success": False,
                        "error": str(e)
                    })
                    
                    await self.log_query_result(question, None, False, str(e))
            
            # Print summary
            print("\n" + "="*80)
            print(f"📊 RESULTS: {results['successful_queries']}/{results['total_questions']} successful")
            print(f"Success Rate: {(results['successful_queries'] / results['total_questions']) * 100:.1f}%")
            print("="*80)
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Error testing RAG queries: {e}")
            return {"total_questions": 0, "successful_queries": 0, "failed_queries": 0, "results": []}
    
    async def log_query_result(self, question: str, response: Any, success: bool, error: str = None):
        """Log query result to Supabase"""
        try:
            if not self.supabase or not self.user_id:
                return
            
            query_data = {
                "id": str(uuid.uuid4()),
                "user_id": self.user_id,
                "content_id": self.content_id,
                "question": question,
                "success": success,
                "created_at": datetime.now().isoformat()
            }
            
            if success and response:
                query_data.update({
                    "answer": response.generated_text,
                    "confidence": response.confidence,
                    "sources_count": len(response.sources),
                    "response_metadata": {
                        "sources": [{"id": s.get("id", ""), "type": s.get("type", "")} for s in response.sources],
                        "contexts_count": len(response.contexts)
                    }
                })
            
            if error:
                query_data["error_message"] = error
            
            # Try to insert into query_logs table (create if doesn't exist)
            try:
                self.supabase.table("query_logs").insert(query_data).execute()
            except Exception:
                # Table might not exist, just log locally
                logger.debug(f"Query logged locally: {question} - Success: {success}")
                
        except Exception as e:
            logger.debug(f"Failed to log query result: {e}")
    
    async def interactive_chat(self):
        """Interactive physics Q&A session"""
        try:
            print("\n" + "="*80)
            print("💬 INTERACTIVE PHYSICS CHAT")
            print("="*80)
            print("Ask physics questions! Type 'quit' to exit.")
            
            if self.user_id:
                print(f"👤 User: {self.user_email}")
            
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
                        
                        # Log interactive query
                        await self.log_query_result(question, response, True)
                    else:
                        print("❌ Sorry, I couldn't find an answer to that question.")
                        await self.log_query_result(question, None, False)
                        
                except KeyboardInterrupt:
                    print("\n👋 Goodbye!")
                    break
                except Exception as e:
                    print(f"❌ Error: {e}")
                    
        except Exception as e:
            logger.error(f"Error in interactive chat: {e}")
    
    async def get_query_statistics(self):
        """Get query statistics from Supabase"""
        try:
            if not self.supabase:
                return
            
            print("\n" + "="*80)
            print("📊 QUERY STATISTICS")
            print("="*80)
            
            # Try to get statistics from query_logs table
            try:
                # Total queries
                total_response = self.supabase.table("query_logs").select("id").execute()
                total_queries = len(total_response.data) if total_response.data else 0
                
                # Successful queries
                success_response = self.supabase.table("query_logs").select("id").eq("success", True).execute()
                successful_queries = len(success_response.data) if success_response.data else 0
                
                # User queries
                user_response = self.supabase.table("query_logs").select("id").eq("user_id", self.user_id).execute()
                user_queries = len(user_response.data) if user_response.data else 0
                
                print(f"Total Queries: {total_queries}")
                print(f"Successful Queries: {successful_queries}")
                print(f"Success Rate: {(successful_queries / total_queries * 100):.1f}%" if total_queries > 0 else "N/A")
                print(f"Your Queries: {user_queries}")
                
            except Exception:
                print("Query statistics not available (query_logs table not found)")
                
            # Content statistics
            try:
                content_response = self.supabase.table("content").select("id, subject, type").execute()
                if content_response.data:
                    physics_content = [c for c in content_response.data if c.get("subject") == "physics"]
                    print(f"Physics Content Items: {len(physics_content)}")
                    print(f"Total Content Items: {len(content_response.data)}")
                    
            except Exception:
                print("Content statistics not available")
                
            print("="*80)
            
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")


async def main():
    """Main function"""
    try:
        # Get user email from command line argument
        user_email = None
        if len(sys.argv) > 1:
            user_email = sys.argv[1]
        
        print("🚀 Supabase RAG Testing Tool")
        print(f"User: {user_email or 'Test User'}")
        
        # Initialize tester
        tester = SupabaseRAGTester(user_email)
        
        # Setup Supabase
        await tester.setup_supabase()
        
        # Process physics PDF
        pdf_processed = await tester.process_physics_pdf()
        
        if not pdf_processed:
            print("⚠️ PDF processing failed, but continuing with RAG tests...")
        
        # Choose test mode
        print("\nChoose test mode:")
        print("1. Automated RAG testing")
        print("2. Interactive chat")
        print("3. Both")
        print("4. Statistics only")
        
        choice = input("\nEnter choice (1/2/3/4): ").strip()
        
        if choice in ['1', '3']:
            await tester.test_rag_queries()
        
        if choice in ['2', '3']:
            await tester.interactive_chat()
        
        if choice in ['4']:
            await tester.get_query_statistics()
        
        if choice not in ['1', '2', '3', '4']:
            print("Invalid choice. Running automated tests...")
            await tester.test_rag_queries()
        
        # Show final statistics
        await tester.get_query_statistics()
        
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.error(f"Main error: {e}")


if __name__ == "__main__":
    asyncio.run(main())