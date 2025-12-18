#!/usr/bin/env python3
"""
Physics PDF Processing and RAG Setup Script

This script processes the physics PDF (leph104.pdf) and sets up RAG indexing
for real-time search and question answering.
"""

import asyncio
import logging
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional
from supabase import create_client, Client

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.content_service import content_service
from app.services.rag_service import rag_service
from app.models.content import Subject, DifficultyLevel
from app.models.rag import RAGQuery
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PhysicsPDFProcessor:
    """Process physics PDF and set up RAG indexing"""
    
    def __init__(self, user_email: Optional[str] = None):
        self.pdf_path = "leph104.pdf"
        self.content_id = None
        self.user_id = None
        self.user_email = user_email
        self.supabase = None
        
    async def _setup_supabase(self):
        """Setup Supabase client and user authentication"""
        try:
            if not settings.supabase_url or not settings.supabase_key:
                logger.warning("Supabase not configured, proceeding without user authentication")
                return
            
            self.supabase = create_client(settings.supabase_url, settings.supabase_service_key)
            logger.info("✅ Supabase client initialized")
            
            # If user email provided, get or create user
            if self.user_email:
                await self._get_or_create_user()
            else:
                # Create a default test user for PDF processing
                await self._create_test_user()
                
        except Exception as e:
            logger.warning(f"Failed to setup Supabase: {e}")
    
    async def _get_or_create_user(self):
        """Get existing user or create new one"""
        try:
            # Check if user exists
            response = self.supabase.table("users").select("*").eq("email", self.user_email).execute()
            
            if response.data:
                self.user_id = response.data[0]["id"]
                logger.info(f"✅ Found existing user: {self.user_email} (ID: {self.user_id})")
            else:
                # Create new user
                user_data = {
                    "email": self.user_email,
                    "name": self.user_email.split("@")[0],
                    "role": "student",
                    "class_grade": 12,
                    "subjects": ["physics"],
                    "created_at": "now()",
                    "updated_at": "now()"
                }
                
                response = self.supabase.table("users").insert(user_data).execute()
                
                if response.data:
                    self.user_id = response.data[0]["id"]
                    logger.info(f"✅ Created new user: {self.user_email} (ID: {self.user_id})")
                else:
                    logger.error("Failed to create user")
                    
        except Exception as e:
            logger.error(f"Error managing user: {e}")
    
    async def _create_test_user(self):
        """Create a test user for PDF processing"""
        try:
            test_email = "physics_test_user@example.com"
            
            # Check if test user exists
            response = self.supabase.table("users").select("*").eq("email", test_email).execute()
            
            if response.data:
                self.user_id = response.data[0]["id"]
                logger.info(f"✅ Using existing test user: {test_email} (ID: {self.user_id})")
            else:
                # Create test user
                user_data = {
                    "email": test_email,
                    "name": "Physics Test User",
                    "role": "student",
                    "class_grade": 12,
                    "subjects": ["physics"],
                    "created_at": "now()",
                    "updated_at": "now()"
                }
                
                response = self.supabase.table("users").insert(user_data).execute()
                
                if response.data:
                    self.user_id = response.data[0]["id"]
                    logger.info(f"✅ Created test user: {test_email} (ID: {self.user_id})")
                else:
                    logger.warning("Failed to create test user, proceeding without user context")
                    
        except Exception as e:
            logger.warning(f"Error creating test user: {e}")
            logger.info("Proceeding without user context")
        
    async def process_pdf(self) -> Dict[str, Any]:
        """
        Main processing function that:
        1. Extracts text from PDF
        2. Creates content item in database
        3. Indexes content for RAG
        4. Tests RAG functionality
        """
        try:
            logger.info("🚀 Starting Physics PDF Processing")
            
            # Step 1: Setup Supabase and user authentication
            logger.info("🔐 Setting up Supabase authentication...")
            await self._setup_supabase()
            
            # Step 2: Check if PDF exists
            if not os.path.exists(self.pdf_path):
                raise FileNotFoundError(f"PDF file not found: {self.pdf_path}")
            
            logger.info(f"✅ Found PDF file: {self.pdf_path}")
            
            # Step 3: Read PDF content
            with open(self.pdf_path, 'rb') as f:
                pdf_content = f.read()
            
            logger.info(f"📖 Read PDF content: {len(pdf_content)} bytes")
            
            # Step 4: Upload and process PDF
            logger.info("📤 Uploading PDF to content service...")
            
            # Prepare metadata with user information
            metadata = {
                "source": "physics_textbook",
                "chapter": "Physics Concepts",
                "description": "Physics textbook content for Class 12",
                "processed_by": "physics_pdf_processor",
                "uploaded_by_user_id": self.user_id,
                "uploaded_by_email": self.user_email or "physics_test_user@example.com"
            }
            
            upload_response = await content_service.upload_file(
                file_content=pdf_content,
                filename="leph104.pdf",
                file_type="application/pdf",
                subject=Subject.PHYSICS,
                class_grade=12,
                difficulty="medium",
                metadata=metadata
            )
            
            if not upload_response.indexed:
                logger.warning(f"PDF uploaded but not indexed: {upload_response.message}")
            
            self.content_id = upload_response.id
            logger.info(f"✅ PDF uploaded successfully. Content ID: {self.content_id}")
            
            # Step 5: Log content upload activity
            if self.user_id and self.supabase:
                await self._log_user_activity("content_uploaded", {
                    "content_id": self.content_id,
                    "filename": "leph104.pdf",
                    "subject": "physics",
                    "file_size": len(pdf_content)
                })
            
            # Step 6: Wait for processing to complete
            logger.info("⏳ Waiting for content processing to complete...")
            await self._wait_for_processing()
            
            # Step 7: Initialize RAG service
            logger.info("🔧 Initializing RAG service...")
            await rag_service.initialize()
            
            # Step 8: Test RAG functionality
            logger.info("🧪 Testing RAG functionality...")
            test_results = await self._test_rag_functionality()
            
            # Step 9: Generate summary report
            report = self._generate_report(upload_response, test_results)
            
            logger.info("🎉 Physics PDF processing completed successfully!")
            return report
            
        except Exception as e:
            logger.error(f"❌ Error processing physics PDF: {e}")
            raise
    
    async def _wait_for_processing(self, max_wait_time: int = 300):
        """Wait for content processing to complete"""
        import time
        
        start_time = time.time()
        while time.time() - start_time < max_wait_time:
            try:
                # Check processing status
                content_info = await content_service.get_content_by_id(self.content_id)
                
                if content_info and content_info.get("processing_status") == "completed":
                    logger.info("✅ Content processing completed")
                    return
                elif content_info and content_info.get("processing_status") == "failed":
                    raise Exception("Content processing failed")
                
                logger.info(f"⏳ Processing status: {content_info.get('processing_status', 'unknown')}")
                await asyncio.sleep(10)  # Wait 10 seconds before checking again
                
            except Exception as e:
                logger.warning(f"Error checking processing status: {e}")
                await asyncio.sleep(5)
        
        logger.warning("⚠️ Processing timeout reached, continuing anyway...")
    
    async def _log_user_activity(self, activity_type: str, activity_data: Dict[str, Any]):
        """Log user activity to Supabase"""
        try:
            if not self.supabase or not self.user_id:
                return
            
            activity_record = {
                "user_id": self.user_id,
                "activity_type": activity_type,
                "activity_data": activity_data,
                "timestamp": "now()",
                "session_id": f"pdf_processing_{self.content_id}"
            }
            
            # Try to insert into user_activities table if it exists
            try:
                self.supabase.table("user_activities").insert(activity_record).execute()
                logger.info(f"✅ Logged user activity: {activity_type}")
            except Exception:
                # If table doesn't exist, just log locally
                logger.info(f"📝 User activity: {activity_type} - {activity_data}")
                
        except Exception as e:
            logger.warning(f"Failed to log user activity: {e}")
    
    async def _test_rag_functionality(self) -> Dict[str, Any]:
        """Test RAG functionality with physics questions"""
        test_questions = [
            "What is Newton's first law of motion?",
            "Explain the concept of electromagnetic induction",
            "What is the relationship between force and acceleration?",
            "Define kinetic energy and potential energy",
            "What are the laws of thermodynamics?"
        ]
        
        test_results = {
            "total_questions": len(test_questions),
            "successful_queries": 0,
            "failed_queries": 0,
            "results": []
        }
        
        for i, question in enumerate(test_questions, 1):
            try:
                logger.info(f"🔍 Testing question {i}/{len(test_questions)}: {question[:50]}...")
                
                # Create RAG query
                rag_query = RAGQuery(
                    query=question,
                    subject=Subject.PHYSICS,
                    max_tokens=300,
                    top_k=5
                )
                
                # Execute query
                response = await rag_service.query(rag_query)
                
                if response and response.generated_text:
                    test_results["successful_queries"] += 1
                    logger.info(f"✅ Question {i} answered successfully")
                    
                    # Log successful query for user
                    if self.user_id and self.supabase:
                        await self._log_user_activity("rag_query_success", {
                            "question": question,
                            "confidence": response.confidence,
                            "sources_count": len(response.sources),
                            "content_id": self.content_id
                        })
                    
                    test_results["results"].append({
                        "question": question,
                        "answer": response.generated_text[:200] + "..." if len(response.generated_text) > 200 else response.generated_text,
                        "confidence": response.confidence,
                        "sources_count": len(response.sources),
                        "success": True
                    })
                else:
                    test_results["failed_queries"] += 1
                    logger.warning(f"⚠️ Question {i} failed: No response generated")
                    
                    test_results["results"].append({
                        "question": question,
                        "error": "No response generated",
                        "success": False
                    })
                
            except Exception as e:
                test_results["failed_queries"] += 1
                logger.error(f"❌ Question {i} failed: {e}")
                
                test_results["results"].append({
                    "question": question,
                    "error": str(e),
                    "success": False
                })
        
        return test_results
    
    def _generate_report(self, upload_response: Any, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate processing report"""
        return {
            "user_info": {
                "user_id": self.user_id,
                "user_email": self.user_email or "physics_test_user@example.com",
                "supabase_connected": self.supabase is not None
            },
            "pdf_processing": {
                "file_path": self.pdf_path,
                "content_id": self.content_id,
                "upload_success": bool(self.content_id),
                "indexed": upload_response.indexed,
                "message": upload_response.message
            },
            "rag_testing": {
                "total_questions": test_results["total_questions"],
                "successful_queries": test_results["successful_queries"],
                "failed_queries": test_results["failed_queries"],
                "success_rate": f"{(test_results['successful_queries'] / test_results['total_questions']) * 100:.1f}%",
                "sample_results": test_results["results"][:3]  # Show first 3 results
            },
            "status": "completed" if test_results["successful_queries"] > 0 else "failed",
            "recommendations": self._get_recommendations(test_results)
        }
    
    def _get_recommendations(self, test_results: Dict[str, Any]) -> list:
        """Get recommendations based on test results"""
        recommendations = []
        
        success_rate = test_results["successful_queries"] / test_results["total_questions"]
        
        if success_rate == 1.0:
            recommendations.append("✅ RAG system is working perfectly!")
        elif success_rate >= 0.8:
            recommendations.append("✅ RAG system is working well with minor issues")
        elif success_rate >= 0.5:
            recommendations.append("⚠️ RAG system has moderate issues - check configuration")
        else:
            recommendations.append("❌ RAG system has significant issues - needs debugging")
        
        if test_results["failed_queries"] > 0:
            recommendations.append("🔧 Check Google Cloud credentials and API keys")
            recommendations.append("🔧 Verify Vertex AI Search configuration")
            recommendations.append("🔧 Ensure content indexing completed successfully")
        
        recommendations.append("📚 You can now ask physics questions using the RAG API")
        recommendations.append("🔍 Use the /doubt/ask endpoint to query the physics content")
        
        return recommendations


async def main():
    """Main function"""
    try:
        # Check for user email argument
        user_email = None
        if len(sys.argv) > 1:
            user_email = sys.argv[1]
            logger.info(f"Using provided user email: {user_email}")
        else:
            logger.info("No user email provided, will create test user")
        
        processor = PhysicsPDFProcessor(user_email=user_email)
        report = await processor.process_pdf()
        
        print("\n" + "="*80)
        print("📊 PHYSICS PDF PROCESSING REPORT")
        print("="*80)
        
        # User Information
        user_info = report["user_info"]
        print(f"\n👤 User Information:")
        print(f"   User ID: {user_info['user_id']}")
        print(f"   Email: {user_info['user_email']}")
        print(f"   Supabase Connected: {'✅' if user_info['supabase_connected'] else '❌'}")
        
        # PDF Processing Status
        pdf_info = report["pdf_processing"]
        print(f"\n📖 PDF Processing:")
        print(f"   File: {pdf_info['file_path']}")
        print(f"   Content ID: {pdf_info['content_id']}")
        print(f"   Upload Success: {'✅' if pdf_info['upload_success'] else '❌'}")
        print(f"   Indexed: {'✅' if pdf_info['indexed'] else '❌'}")
        print(f"   Message: {pdf_info['message']}")
        
        # RAG Testing Status
        rag_info = report["rag_testing"]
        print(f"\n🧪 RAG Testing:")
        print(f"   Total Questions: {rag_info['total_questions']}")
        print(f"   Successful: {rag_info['successful_queries']}")
        print(f"   Failed: {rag_info['failed_queries']}")
        print(f"   Success Rate: {rag_info['success_rate']}")
        
        # Sample Results
        print(f"\n📝 Sample Results:")
        for i, result in enumerate(rag_info['sample_results'], 1):
            status = "✅" if result['success'] else "❌"
            print(f"   {i}. {status} {result['question']}")
            if result['success']:
                print(f"      Answer: {result['answer']}")
            else:
                print(f"      Error: {result.get('error', 'Unknown error')}")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        for rec in report["recommendations"]:
            print(f"   {rec}")
        
        print("\n" + "="*80)
        print(f"🎯 Overall Status: {report['status'].upper()}")
        print("="*80)
        
        return report
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return {"status": "failed", "error": str(e)}


if __name__ == "__main__":
    # Run the processing
    asyncio.run(main())