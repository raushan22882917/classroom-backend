#!/usr/bin/env python3
"""
Modern Supabase RAG Implementation

Uses the latest Google GenAI library and gemini-2.5-flash model for better performance.
"""

import asyncio
import logging
import sys
import os
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from supabase import create_client, Client
import numpy as np
from sentence_transformers import SentenceTransformer

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ModernSupabaseRAG:
    """Modern RAG system using latest Google GenAI and Supabase"""
    
    def __init__(self):
        self.supabase: Optional[Client] = None
        self.embedding_model = None
        self.content_chunks = []
        self.content_embeddings = []
        self.genai_client = None
        
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
            
            # Setup Google GenAI
            await self.setup_genai()
            
            # Load and process content
            await self.load_content()
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize RAG system: {e}")
            raise
    
    async def setup_genai(self):
        """Setup Google GenAI client"""
        try:
            if not settings.gemini_api_key:
                logger.warning("⚠️ Gemini API key not found, will use simple text-based answers")
                return
            
            # Try the newer google-genai library first
            try:
                import google.genai as genai
                self.genai_client = genai.Client(api_key=settings.gemini_api_key)
                logger.info("✅ Google GenAI client initialized (new library)")
                return
            except ImportError:
                pass
            
            # Fallback to google.generativeai
            try:
                import google.generativeai as genai
                genai.configure(api_key=settings.gemini_api_key)
                self.genai_client = genai
                logger.info("✅ Google GenerativeAI configured (legacy library)")
                return
            except ImportError:
                pass
            
            logger.warning("⚠️ No Google AI library available, using simple answers")
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to setup GenAI: {e}")
    
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
            
            # Smart chunking - split by sections and paragraphs
            chunks = self.smart_chunk_text(content_text, content_item)
            
            for chunk in chunks:
                # Create embedding
                embedding = self.embedding_model.encode(chunk["text"])
                
                self.content_chunks.append(chunk)
                self.content_embeddings.append(embedding)
            
        except Exception as e:
            logger.error(f"Error processing content item {content_item.get('id')}: {e}")
    
    def smart_chunk_text(self, text: str, content_item: Dict, chunk_size: int = 600) -> List[Dict]:
        """Smart chunking that preserves context"""
        chunks = []
        
        # Split by common physics section markers
        section_markers = [
            '\n\nChapter', '\n\nSection', '\n\nExample', '\n\nProblem',
            '\n\nDefinition', '\n\nTheorem', '\n\nLaw', '\n\nFormula'
        ]
        
        # First try to split by sections
        sections = [text]
        for marker in section_markers:
            new_sections = []
            for section in sections:
                new_sections.extend(section.split(marker))
            sections = [s.strip() for s in new_sections if s.strip()]
        
        # Now chunk each section
        chunk_index = 0
        for section in sections:
            if len(section) <= chunk_size:
                # Section is small enough, use as is
                if len(section.strip()) > 50:  # Only if meaningful content
                    chunks.append({
                        "text": section.strip(),
                        "content_id": content_item["id"],
                        "title": content_item.get("title", ""),
                        "chapter": content_item.get("chapter", ""),
                        "subject": content_item.get("subject", ""),
                        "chunk_index": chunk_index,
                        "metadata": content_item.get("metadata", {})
                    })
                    chunk_index += 1
            else:
                # Section is too large, split by paragraphs
                paragraphs = [p.strip() for p in section.split('\n\n') if p.strip()]
                current_chunk = ""
                
                for paragraph in paragraphs:
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
                
                # Add remaining content
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
                    chunk_index += 1
        
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
    
    async def generate_ai_answer(self, query: str, context_chunks: List[Dict]) -> str:
        """Generate AI answer using Gemini 2.5 Flash"""
        try:
            if not self.genai_client or not context_chunks:
                return self.generate_simple_answer(query, context_chunks)
            
            # Build context from chunks
            context_parts = []
            for i, chunk in enumerate(context_chunks, 1):
                context_parts.append(f"[Context {i}] {chunk['title']}\n{chunk['text']}")
            
            context_text = "\n\n".join(context_parts)
            
            # Create prompt
            prompt = f"""You are a physics tutor for Class 12 students in India. Use the provided context from the physics textbook to answer the student's question clearly and accurately.

Context from Physics Textbook:
{context_text}

Student's Question: {query}

Instructions:
1. Answer using the information from the context above
2. Explain concepts clearly for Class 12 level
3. Include relevant formulas and examples from the context
4. If the context doesn't fully answer the question, mention what information is available
5. Be concise but thorough

Answer:"""

            # Try new Google GenAI library first
            if hasattr(self.genai_client, 'models'):
                try:
                    model = self.genai_client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=prompt
                    )
                    return model.text if hasattr(model, 'text') else str(model)
                except Exception as e:
                    logger.debug(f"New GenAI library failed: {e}")
            
            # Fallback to legacy library
            if hasattr(self.genai_client, 'GenerativeModel'):
                try:
                    # Try different model names
                    model_names = ['gemini-2.5-flash', 'gemini-1.5-flash', 'gemini-pro']
                    
                    for model_name in model_names:
                        try:
                            model = self.genai_client.GenerativeModel(model_name)
                            response = model.generate_content(prompt)
                            
                            if hasattr(response, 'text') and response.text:
                                logger.info(f"✅ Generated answer using {model_name}")
                                return response.text
                        except Exception as e:
                            logger.debug(f"Model {model_name} failed: {e}")
                            continue
                
                except Exception as e:
                    logger.debug(f"Legacy GenAI library failed: {e}")
            
            # If all AI methods fail, use simple answer
            return self.generate_simple_answer(query, context_chunks)
            
        except Exception as e:
            logger.error(f"Error generating AI answer: {e}")
            return self.generate_simple_answer(query, context_chunks)
    
    def generate_simple_answer(self, query: str, context_chunks: List[Dict]) -> str:
        """Generate a simple answer by combining relevant context"""
        if not context_chunks:
            return "I couldn't find relevant information in the physics content to answer your question."
        
        # Find the most relevant chunk
        best_chunk = max(context_chunks, key=lambda x: x["similarity"])
        
        # Create a structured answer
        answer_parts = [
            f"Based on the physics textbook content, here's information about '{query}':",
            "",
            f"📖 From '{best_chunk['title']}':",
            best_chunk["text"][:600] + ("..." if len(best_chunk["text"]) > 600 else ""),
        ]
        
        # Add additional context if available and relevant
        if len(context_chunks) > 1:
            high_similarity_chunks = [c for c in context_chunks[1:] if c["similarity"] > 0.3]
            
            if high_similarity_chunks:
                answer_parts.extend([
                    "",
                    "📚 Additional relevant information:",
                ])
                
                for i, chunk in enumerate(high_similarity_chunks[:2], 1):
                    preview = chunk["text"][:300] + ("..." if len(chunk["text"]) > 300 else "")
                    answer_parts.append(f"{i}. {preview}")
        
        return "\n".join(answer_parts)
    
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
            
            # Generate answer (AI or simple)
            answer = await self.generate_ai_answer(question, relevant_chunks)
            
            # Calculate confidence based on similarity scores
            avg_similarity = sum(chunk["similarity"] for chunk in relevant_chunks) / len(relevant_chunks)
            confidence = min(avg_similarity * 1.3, 1.0)  # Scale and cap at 1.0
            
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
                "chunks_found": len(relevant_chunks),
                "ai_generated": self.genai_client is not None
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
        logger.info("📤 Checking physics PDF in Supabase...")
        
        # Setup Supabase
        supabase = create_client(settings.supabase_url, settings.supabase_service_key)
        
        # Check if content already exists
        existing = supabase.table("content").select("id, title").eq("subject", "physics").execute()
        if existing.data:
            logger.info(f"✅ Physics content already exists: {len(existing.data)} items")
            for item in existing.data:
                logger.info(f"   - {item.get('title', 'Untitled')} (ID: {item['id']})")
            return existing.data[0]["id"]
        
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
        for page_num, page in enumerate(pdf_reader.pages):
            page_text = page.extract_text()
            if page_text.strip():  # Only add non-empty pages
                text_parts.append(f"[Page {page_num + 1}]\n{page_text}")
        
        content_text = "\n\n".join(text_parts)
        logger.info(f"📝 Extracted {len(content_text)} characters from {len(text_parts)} pages")
        
        # Prepare content data with correct enum values
        content_data = {
            "type": "document",  # Use a valid enum value
            "subject": "physics",
            "chapter": "Physics Concepts and Laws",
            "difficulty": "medium",
            "title": "Physics Textbook - Comprehensive Guide",
            "content_text": content_text,
            "metadata": {
                "source": "physics_textbook",
                "filename": "leph104.pdf",
                "file_size": len(pdf_content),
                "processed_at": datetime.now().isoformat(),
                "page_count": len(pdf_reader.pages),
                "extraction_method": "PyPDF2"
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


async def test_modern_rag():
    """Test the modern RAG system"""
    try:
        print("🚀 Testing Modern Supabase RAG System with Gemini 2.5 Flash")
        print("="*70)
        
        # Upload PDF if needed
        content_id = await upload_physics_pdf()
        
        # Initialize RAG system
        logger.info("🔧 Initializing modern RAG system...")
        rag_system = ModernSupabaseRAG()
        await rag_system.initialize()
        
        if not rag_system.content_chunks:
            print("❌ No content chunks loaded. Please check your database.")
            return
        
        print(f"\n📚 Content chunks loaded: {len(rag_system.content_chunks)}")
        print(f"🤖 AI Generation: {'✅ Enabled' if rag_system.genai_client else '❌ Disabled (using simple answers)'}")
        print("="*70)
        
        # Test questions
        test_questions = [
            "What is Newton's first law of motion?",
            "Explain electromagnetic induction and Faraday's law",
            "What is kinetic energy and its formula?",
            "Define acceleration and its units",
            "What are Maxwell's equations in electromagnetism?"
        ]
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n📝 Question {i}: {question}")
            print("-" * 60)
            
            result = await rag_system.query(question)
            
            print(f"🤖 Answer:\n{result['answer']}")
            print(f"\n🎯 Confidence: {result['confidence']:.2f}")
            print(f"📚 Sources: {result['chunks_found']} chunks found")
            print(f"🧠 AI Generated: {'Yes' if result.get('ai_generated') else 'No'}")
            
            if result['sources']:
                print(f"📖 Best match similarity: {result['sources'][0]['similarity']:.3f}")
                print(f"📄 Source: {result['sources'][0]['title']}")
        
        # Interactive mode
        print(f"\n{'='*70}")
        print("💬 Interactive Mode - Ask your physics questions!")
        print("Type 'quit' to exit, 'stats' for statistics")
        print("="*70)
        
        query_count = 0
        while True:
            try:
                question = input("\n🤔 Your question: ").strip()
                
                if question.lower() in ['quit', 'exit', 'q']:
                    break
                
                if question.lower() == 'stats':
                    print(f"\n📊 Session Statistics:")
                    print(f"   Queries processed: {query_count}")
                    print(f"   Content chunks: {len(rag_system.content_chunks)}")
                    print(f"   AI enabled: {'Yes' if rag_system.genai_client else 'No'}")
                    continue
                
                if not question:
                    continue
                
                query_count += 1
                result = await rag_system.query(question)
                
                print(f"\n🤖 Answer:\n{result['answer']}")
                print(f"\n🎯 Confidence: {result['confidence']:.2f}")
                print(f"📚 Sources: {result['chunks_found']} chunks found")
                
                # Show top source details
                if result['sources']:
                    top_source = result['sources'][0]
                    print(f"\n📖 Top Source:")
                    print(f"   Similarity: {top_source['similarity']:.3f}")
                    print(f"   Title: {top_source['title']}")
                    print(f"   Preview: {top_source['text_preview'][:150]}...")
                
            except KeyboardInterrupt:
                break
        
        print(f"\n👋 Goodbye! Processed {query_count} queries in this session.")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")


async def main():
    """Main function"""
    try:
        await test_modern_rag()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())