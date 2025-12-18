#!/usr/bin/env python3
"""
Supabase RAG Implementation

This creates a proper RAG system that actually retrieves content from your Supabase database
and uses it to answer questions about the physics PDF.
"""

import asyncio
import logging
import sys
import os
import uuid
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from supabase import create_client, Client
import numpy as np
from sentence_transformers import SentenceTransformer
import google.generativeai as genai

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SupabaseRAGSystem:
    """RAG system that actually uses Supabase content"""
    
    def __init__(self):
        self.supabase: Optional[Client] = None
        self.embedding_model = None
        self.content_chunks = []
        self.content_embeddings = []
        
    async def initialize(self):
        """Initialize the RAG system"""
        try:
            # Setup Supabase
            if not settings.supabase_url or not settings.supabase_service_key:
                raise Exception("Supabase configuration missing")
            
            self.supabase = create_client(settings.supabase_url, settings.supabase_service_key)
            logger.info("✅ Connected to Supabase")
            
            # Initialize embedding model
            logger.info("🔧 Loading embedding model...")
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("✅ Embedding model loaded")
            
            # Setup Gemini
            if settings.gemini_api_key:
                genai.configure(api_key=settings.gemini_api_key)
                logger.info("✅ Gemini API configured")
            
            # Load and process content
            await self.load_content()
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize RAG system: {e}")
            raise
    
    async def load_content(self):
        """Load content from Supabase and create embeddings"""
        try:
            logger.info("📚 Loading content from Supabase...")
            
            # Get all physics content
            response = self.supabase.table("content").select("*").eq("subject", "physics").execute()
            
            if not response.data:
                logger.warning("⚠️ No physics content found in database")
                return
            
            logger.info(f"📖 Found {len(response.data)} physics content items")
            
            # Process each content item
            for content_item in response.data:
                await self.process_content_item(content_item)
            
            logger.info(f"✅ Processed {len(self.content_chunks)} content chunks")
            
        except Exception as e:
            logger.error(f"❌ Error loading content: {e}")
    
    async def process_content_item(self, content_item: Dict):
        """Process a single content item into chunks"""
        try:
            content_text = content_item.get("content_text", "")
            if not content_text or len(content_text.strip()) < 50:
                return
            
            # Simple chunking - split into paragraphs and sentences
            chunks = self.chunk_text(content_text, content_item)
            
            for chunk in chunks:
                # Create embedding
                embedding = self.embedding_model.encode(chunk["text"])
                
                self.content_chunks.append(chunk)
                self.content_embeddings.append(embedding)
            
        except Exception as e:
            logger.error(f"Error processing content item {content_item.get('id')}: {e}")
    
    def chunk_text(self, text: str, content_item: Dict, chunk_size: int = 500) -> List[Dict]:
        """Chunk text into smaller pieces"""
        chunks = []
        
        # Split by paragraphs first
        paragraphs = text.split('\n\n')
        
        current_chunk = ""
        chunk_index = 0
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            # If adding this paragraph would exceed chunk size, save current chunk
            if len(current_chunk) + len(paragraph) > chunk_size and current_chunk:
                chunks.append({
                    "text": current_chunk.strip(),
                    "content_id": content_item["id"],
                    "title": content_item.get("title", ""),
                    "chapter": content_item.get("chapter", ""),
                    "subject": content_item.get("subject", ""),
                    "chunk_index": chunk_index,
                    "metadata": content_item.get("metadata", {})
                })
                current_chunk = ""
                chunk_index += 1
            
            current_chunk += paragraph + "\n\n"
        
        # Add the last chunk
        if current_chunk.strip():
            chunks.append({
                "text": current_chunk.strip(),
                "content_id": content_item["id"],
                "title": content_item.get("title", ""),
                "chapter": content_item.get("chapter", ""),
                "subject": content_item.get("subject", ""),
                "chunk_index": chunk_index,
                "metadata": content_item.get("metadata", {})
            })
        
        return chunks
    
    async def search_content(self, query: str, top_k: int = 5) -> List[Dict]:
        """Search for relevant content chunks"""
        try:
            if not self.content_chunks:
                logger.warning("No content chunks available for search")
                return []
            
            # Create query embedding
            query_embedding = self.embedding_model.encode(query)
            
            # Calculate similarities
            similarities = []
            for i, chunk_embedding in enumerate(self.content_embeddings):
                similarity = np.dot(query_embedding, chunk_embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(chunk_embedding)
                )
                similarities.append((similarity, i))
            
            # Sort by similarity and get top results
            similarities.sort(reverse=True)
            top_results = similarities[:top_k]
            
            # Return relevant chunks
            results = []
            for similarity, idx in top_results:
                chunk = self.content_chunks[idx].copy()
                chunk["similarity"] = float(similarity)
                results.append(chunk)
            
            logger.info(f"🔍 Found {len(results)} relevant chunks for query")
            return results
            
        except Exception as e:
            logger.error(f"Error searching content: {e}")
            return []
    
    async def generate_answer(self, query: str, context_chunks: List[Dict]) -> str:
        """Generate answer using Gemini with context"""
        try:
            if not context_chunks:
                return "I couldn't find relevant information in the physics content to answer your question."
            
            # Build context from chunks
            context_parts = []
            for i, chunk in enumerate(context_chunks, 1):
                context_parts.append(f"[Context {i}] {chunk['title']}\n{chunk['text']}")
            
            context_text = "\n\n".join(context_parts)
            
            # Create prompt
            prompt = f"""You are a physics tutor for Class 12 students. Use the provided context from the physics textbook to answer the student's question.

Context from Physics Textbook:
{context_text}

Student's Question: {query}

Instructions:
1. Answer using ONLY the information from the context above
2. If the context doesn't contain enough information, say so clearly
3. Explain concepts clearly for Class 12 level
4. Include relevant formulas and examples from the context
5. Be concise but thorough

Answer:"""

            # Generate with Gemini - try multiple model names starting with 2.5-flash
            model_names = ['gemini-2.5-flash', 'gemini-2.0-flash-exp', 'gemini-1.5-flash', 'gemini-pro']
            model = None
            
            for model_name in model_names:
                try:
                    model = genai.GenerativeModel(model_name)
                    logger.info(f"Using Gemini model: {model_name}")
                    break
                except Exception as e:
                    logger.debug(f"Model {model_name} not available: {e}")
                    continue
            
            if model is None:
                return "Error: No available Gemini model found. Please check your API configuration."
            
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=500,
                    candidate_count=1
                )
            )
            
            if hasattr(response, 'text') and response.text:
                return response.text
            else:
                return "I couldn't generate a proper response. Please try rephrasing your question."
                
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            return f"Error generating answer: {str(e)}"
    
    async def query(self, question: str) -> Dict[str, Any]:
        """Main query method"""
        try:
            logger.info(f"🔍 Processing query: {question[:50]}...")
            
            # Search for relevant content
            relevant_chunks = await self.search_content(question, top_k=5)
            
            if not relevant_chunks:
                return {
                    "question": question,
                    "answer": "I couldn't find relevant information in the physics content to answer your question.",
                    "sources": [],
                    "confidence": 0.0
                }
            
            # Generate answer
            answer = await self.generate_answer(question, relevant_chunks)
            
            # Calculate confidence based on similarity scores
            avg_similarity = sum(chunk["similarity"] for chunk in relevant_chunks) / len(relevant_chunks)
            confidence = min(avg_similarity * 1.2, 1.0)  # Scale and cap at 1.0
            
            # Prepare sources
            sources = []
            for chunk in relevant_chunks:
                sources.append({
                    "content_id": chunk["content_id"],
                    "title": chunk["title"],
                    "chapter": chunk["chapter"],
                    "similarity": chunk["similarity"],
                    "text_preview": chunk["text"][:200] + "..." if len(chunk["text"]) > 200 else chunk["text"]
                })
            
            result = {
                "question": question,
                "answer": answer,
                "sources": sources,
                "confidence": confidence,
                "chunks_found": len(relevant_chunks)
            }
            
            logger.info(f"✅ Generated answer with {len(sources)} sources")
            return result
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                "question": question,
                "answer": f"Error processing query: {str(e)}",
                "sources": [],
                "confidence": 0.0
            }


async def upload_physics_pdf():
    """Upload physics PDF to Supabase with correct format"""
    try:
        logger.info("📤 Uploading physics PDF to Supabase...")
        
        # Setup Supabase
        supabase = create_client(settings.supabase_url, settings.supabase_service_key)
        
        # Check if PDF exists
        pdf_path = "leph104.pdf"
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        # Extract text from PDF
        import PyPDF2
        from io import BytesIO
        
        with open(pdf_path, 'rb') as f:
            pdf_content = f.read()
        
        pdf_file = BytesIO(pdf_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        text_parts = []
        for page in pdf_reader.pages:
            text_parts.append(page.extract_text())
        
        content_text = "\n\n".join(text_parts)
        logger.info(f"📝 Extracted {len(content_text)} characters from PDF")
        
        # Check what content types are available
        try:
            # Try to get existing content to see the schema
            existing = supabase.table("content").select("type").limit(1).execute()
            logger.info("✅ Content table accessible")
        except Exception as e:
            logger.error(f"Content table error: {e}")
        
        # Prepare content data with correct enum values
        content_data = {
            "type": "document",  # Use a valid enum value
            "subject": "physics",
            "chapter": "Physics Concepts",
            "difficulty": "medium",
            "title": "Physics Textbook - Chapter 104",
            "content_text": content_text,
            "metadata": {
                "source": "physics_textbook",
                "filename": "leph104.pdf",
                "file_size": len(pdf_content),
                "processed_at": datetime.now().isoformat(),
                "page_count": len(pdf_reader.pages)
            }
        }
        
        # Insert content
        response = supabase.table("content").insert(content_data).execute()
        
        if response.data:
            content_id = response.data[0]["id"]
            logger.info(f"✅ Content uploaded successfully: {content_id}")
            return content_id
        else:
            logger.error("❌ Failed to upload content")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error uploading PDF: {e}")
        return None


async def test_rag_system():
    """Test the RAG system"""
    try:
        print("🚀 Testing Supabase RAG System")
        print("="*60)
        
        # Upload PDF if needed
        content_id = await upload_physics_pdf()
        
        # Initialize RAG system
        logger.info("🔧 Initializing RAG system...")
        rag_system = SupabaseRAGSystem()
        await rag_system.initialize()
        
        # Test questions
        test_questions = [
            "What is Newton's first law of motion?",
            "Explain electromagnetic induction",
            "What is the formula for kinetic energy?",
            "Define acceleration and its units",
            "What are Maxwell's equations?"
        ]
        
        print(f"\n📚 Content chunks loaded: {len(rag_system.content_chunks)}")
        print("="*60)
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n📝 Question {i}: {question}")
            print("-" * 50)
            
            result = await rag_system.query(question)
            
            print(f"🤖 Answer: {result['answer']}")
            print(f"🎯 Confidence: {result['confidence']:.2f}")
            print(f"📚 Sources: {result['chunks_found']} chunks found")
            
            if result['sources']:
                print("📖 Top source:")
                top_source = result['sources'][0]
                print(f"   Title: {top_source['title']}")
                print(f"   Similarity: {top_source['similarity']:.3f}")
                print(f"   Preview: {top_source['text_preview']}")
        
        # Interactive mode
        print(f"\n{'='*60}")
        print("💬 Interactive Mode - Ask your physics questions!")
        print("Type 'quit' to exit")
        print("="*60)
        
        while True:
            try:
                question = input("\n🤔 Your question: ").strip()
                
                if question.lower() in ['quit', 'exit', 'q']:
                    break
                
                if not question:
                    continue
                
                result = await rag_system.query(question)
                
                print(f"\n🤖 Answer: {result['answer']}")
                print(f"🎯 Confidence: {result['confidence']:.2f}")
                print(f"📚 Sources: {result['chunks_found']} chunks found")
                
            except KeyboardInterrupt:
                break
        
        print("\n👋 Goodbye!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")


async def main():
    """Main function"""
    try:
        await test_rag_system()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())