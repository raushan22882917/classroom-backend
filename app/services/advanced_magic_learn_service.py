"""Advanced Magic Learn service with enhanced AI capabilities and real-time features"""

import asyncio
import base64
import io
import json
import time
import uuid
from typing import List, Dict, Any, Optional, AsyncGenerator
from datetime import datetime, timedelta
import numpy as np
from PIL import Image
import cv2
import google.generativeai as genai
from concurrent.futures import ThreadPoolExecutor
import os

from app.models.magic_learn import (
    BatchAnalysisRequest, BatchAnalysisResponse,
    RealTimeAnalysisRequest, RealTimeAnalysisResponse,
    CollaborativeSessionRequest, CollaborativeSessionResponse,
    LearningPathRequest, LearningPathResponse,
    AITutorRequest, AITutorResponse,
    AssessmentRequest, AssessmentResponse,
    ProgressTrackingRequest, ProgressTrackingResponse,
    ContentGenerationRequest, ContentGenerationResponse,
    ImageAnalysisRequest, ImageAnalysisResponse,
    AnalysisType, DifficultyLevel, LanguageCode
)

# Configure Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


class AdvancedImageAnalysisService:
    """Enhanced image analysis with advanced AI capabilities"""
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.analysis_cache = {}
        self.batch_queue = asyncio.Queue()
        
    async def analyze_batch(self, request: BatchAnalysisRequest) -> BatchAnalysisResponse:
        """Analyze multiple images in batch with parallel processing"""
        batch_id = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            # Process images in parallel
            tasks = []
            for i, image_data in enumerate(request.images):
                analysis_request = ImageAnalysisRequest(
                    image_data=image_data.get('data', ''),
                    analysis_type=request.analysis_type,
                    user_id=request.user_id,
                    custom_instructions=image_data.get('instructions')
                )
                task = self._analyze_single_image(analysis_request, f"{batch_id}_{i}")
                tasks.append(task)
            
            # Wait for all analyses to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results and handle exceptions
            successful_results = []
            failed_count = 0
            
            for result in results:
                if isinstance(result, Exception):
                    failed_count += 1
                    # Create error response
                    error_response = ImageAnalysisResponse(
                        success=False,
                        analysis="Analysis failed",
                        detected_elements=[],
                        confidence_score=0.0,
                        processing_time=0.0,
                        analysis_type=request.analysis_type,
                        error=str(result)
                    )
                    successful_results.append(error_response)
                else:
                    successful_results.append(result)
            
            # Generate batch summary
            summary = await self._generate_batch_summary(successful_results, request.analysis_type)
            
            total_time = time.time() - start_time
            
            return BatchAnalysisResponse(
                success=failed_count < len(results),
                batch_id=batch_id,
                results=successful_results,
                summary=summary,
                total_processing_time=total_time,
                error=f"{failed_count} analyses failed" if failed_count > 0 else None
            )
            
        except Exception as e:
            return BatchAnalysisResponse(
                success=False,
                batch_id=batch_id,
                results=[],
                summary="Batch analysis failed",
                total_processing_time=time.time() - start_time,
                error=str(e)
            )
    
    async def _analyze_single_image(self, request: ImageAnalysisRequest, session_id: str) -> ImageAnalysisResponse:
        """Analyze a single image with enhanced features"""
        from app.services.magic_learn_service import image_reader_service
        
        # Use existing service but enhance the response
        basic_response = await image_reader_service.analyze_image(request)
        
        if basic_response.success:
            # Enhance with additional analysis
            enhanced_content = await self._enhance_analysis(
                basic_response.analysis, 
                request.analysis_type,
                request.difficulty_level,
                request.language
            )
            
            # Add structured content
            structured_content = await self._create_structured_content(
                basic_response.analysis,
                basic_response.detected_elements
            )
            
            # Generate interactive elements
            interactive_elements = await self._generate_interactive_elements(
                basic_response.analysis,
                request.analysis_type
            )
            
            # Update response with enhancements
            basic_response.analysis = enhanced_content
            basic_response.session_id = session_id
            basic_response.structured_content = structured_content
            basic_response.interactive_elements = interactive_elements
            basic_response.key_concepts = await self._extract_key_concepts(enhanced_content)
            basic_response.difficulty_assessment = await self._assess_difficulty(enhanced_content)
            basic_response.suggested_next_steps = await self._generate_next_steps(enhanced_content)
            basic_response.related_topics = await self._find_related_topics(enhanced_content)
        
        return basic_response
    
    async def _enhance_analysis(self, analysis: str, analysis_type: AnalysisType, 
                              difficulty: DifficultyLevel, language: LanguageCode) -> str:
        """Enhance analysis with difficulty-appropriate explanations and language"""
        
        if not GEMINI_API_KEY:
            return analysis
        
        try:
            model = genai.GenerativeModel('gemini-2.5-flash-lite')
            
            prompt = f"""Enhance the following educational analysis:

Original Analysis:
{analysis}

Enhancement Requirements:
- Adjust explanation for {difficulty.value} level students
- Provide response in {language.value} language
- Add more detailed explanations where appropriate
- Include practical applications and real-world examples
- Ensure mathematical notation is properly formatted
- Add learning tips and memory aids

Enhanced Analysis:"""

            response = model.generate_content([prompt])
            return response.text
            
        except Exception as e:
            print(f"Enhancement error: {e}")
            return analysis
    
    async def _create_structured_content(self, analysis: str, detected_elements: List[str]) -> Dict[str, Any]:
        """Create structured content for better frontend integration"""
        
        return {
            "sections": await self._extract_sections(analysis),
            "key_points": await self._extract_key_points(analysis),
            "formulas": await self._extract_formulas(analysis),
            "examples": await self._extract_examples(analysis),
            "definitions": await self._extract_definitions(analysis),
            "detected_elements": detected_elements,
            "content_type": await self._classify_content_type(analysis)
        }
    
    async def _generate_interactive_elements(self, analysis: str, analysis_type: AnalysisType) -> List[Dict[str, Any]]:
        """Generate interactive learning elements based on analysis"""
        
        elements = []
        
        # Quiz questions
        if "equation" in analysis.lower() or analysis_type == AnalysisType.MATHEMATICAL:
            elements.append({
                "type": "quiz",
                "title": "Quick Check",
                "questions": await self._generate_quiz_questions(analysis)
            })
        
        # Interactive calculator
        if any(term in analysis.lower() for term in ["calculate", "solve", "equation"]):
            elements.append({
                "type": "calculator",
                "title": "Interactive Calculator",
                "formulas": await self._extract_formulas(analysis)
            })
        
        # Practice problems
        elements.append({
            "type": "practice",
            "title": "Practice Problems",
            "problems": await self._generate_practice_problems(analysis, analysis_type)
        })
        
        # Visualization
        if analysis_type in [AnalysisType.GEOMETRY, AnalysisType.PHYSICS]:
            elements.append({
                "type": "visualization",
                "title": "Interactive Visualization",
                "config": await self._create_visualization_config(analysis)
            })
        
        return elements
    
    async def _generate_batch_summary(self, results: List[ImageAnalysisResponse], 
                                    analysis_type: AnalysisType) -> str:
        """Generate a comprehensive summary of batch analysis results"""
        
        if not GEMINI_API_KEY:
            return f"Analyzed {len(results)} images of type {analysis_type.value}"
        
        try:
            # Combine all analyses
            combined_analysis = "\n\n".join([r.analysis for r in results if r.success])
            
            model = genai.GenerativeModel('gemini-2.5-flash-lite')
            
            prompt = f"""Create a comprehensive summary of the following batch analysis results:

Analysis Type: {analysis_type.value}
Number of Images: {len(results)}
Successful Analyses: {sum(1 for r in results if r.success)}

Combined Analysis Content:
{combined_analysis[:5000]}  # Limit to avoid token limits

Please provide:
1. Overall themes and patterns identified
2. Common concepts across all images
3. Key learning objectives covered
4. Suggested learning path based on the content
5. Areas that might need additional focus

Summary:"""

            response = model.generate_content([prompt])
            return response.text
            
        except Exception as e:
            print(f"Summary generation error: {e}")
            return f"Batch analysis completed: {len(results)} images processed"
    
    # Helper methods for content extraction and analysis
    async def _extract_sections(self, analysis: str) -> List[Dict[str, str]]:
        """Extract sections from analysis"""
        sections = []
        lines = analysis.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            if line.startswith('#'):
                if current_section:
                    sections.append({
                        "title": current_section,
                        "content": '\n'.join(current_content)
                    })
                current_section = line.strip('#').strip()
                current_content = []
            else:
                current_content.append(line)
        
        if current_section:
            sections.append({
                "title": current_section,
                "content": '\n'.join(current_content)
            })
        
        return sections
    
    async def _extract_key_points(self, analysis: str) -> List[str]:
        """Extract key points from analysis"""
        key_points = []
        lines = analysis.split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith('- ') or line.startswith('* '):
                key_points.append(line[2:])
            elif line.startswith(('1.', '2.', '3.', '4.', '5.')):
                key_points.append(line[3:])
        
        return key_points[:10]  # Limit to top 10
    
    async def _extract_formulas(self, analysis: str) -> List[str]:
        """Extract mathematical formulas from analysis"""
        import re
        
        # Look for LaTeX-style formulas
        latex_pattern = r'\$([^$]+)\$'
        formulas = re.findall(latex_pattern, analysis)
        
        # Look for common mathematical expressions
        math_pattern = r'([a-zA-Z]\s*=\s*[^,\n]+)'
        math_expressions = re.findall(math_pattern, analysis)
        
        return list(set(formulas + math_expressions))
    
    async def _extract_examples(self, analysis: str) -> List[str]:
        """Extract examples from analysis"""
        examples = []
        lines = analysis.split('\n')
        
        for i, line in enumerate(lines):
            if 'example' in line.lower():
                # Get the next few lines as the example
                example_lines = []
                for j in range(i, min(i + 5, len(lines))):
                    if lines[j].strip():
                        example_lines.append(lines[j])
                    else:
                        break
                if example_lines:
                    examples.append('\n'.join(example_lines))
        
        return examples[:3]  # Limit to 3 examples
    
    async def _extract_definitions(self, analysis: str) -> List[Dict[str, str]]:
        """Extract definitions from analysis"""
        definitions = []
        lines = analysis.split('\n')
        
        for line in lines:
            if ':' in line and len(line.split(':')) == 2:
                term, definition = line.split(':', 1)
                term = term.strip('*').strip()
                definition = definition.strip()
                if len(term) < 50 and len(definition) > 10:
                    definitions.append({
                        "term": term,
                        "definition": definition
                    })
        
        return definitions[:5]  # Limit to 5 definitions
    
    async def _classify_content_type(self, analysis: str) -> str:
        """Classify the type of content in the analysis"""
        analysis_lower = analysis.lower()
        
        if any(term in analysis_lower for term in ['equation', 'formula', 'solve']):
            return "mathematical_problem"
        elif any(term in analysis_lower for term in ['diagram', 'chart', 'graph']):
            return "visual_explanation"
        elif any(term in analysis_lower for term in ['definition', 'concept', 'theory']):
            return "conceptual_explanation"
        elif any(term in analysis_lower for term in ['step', 'procedure', 'method']):
            return "procedural_guide"
        else:
            return "general_analysis"
    
    async def _extract_key_concepts(self, analysis: str) -> List[str]:
        """Extract key educational concepts"""
        # This would use NLP to identify key concepts
        # For now, use simple keyword extraction
        concepts = []
        analysis_lower = analysis.lower()
        
        # Mathematical concepts
        math_concepts = ['algebra', 'geometry', 'calculus', 'trigonometry', 'statistics', 'probability']
        for concept in math_concepts:
            if concept in analysis_lower:
                concepts.append(concept.title())
        
        # Scientific concepts
        science_concepts = ['physics', 'chemistry', 'biology', 'energy', 'force', 'molecule', 'cell']
        for concept in science_concepts:
            if concept in analysis_lower:
                concepts.append(concept.title())
        
        return list(set(concepts))[:5]
    
    async def _assess_difficulty(self, analysis: str) -> DifficultyLevel:
        """Assess the difficulty level of the content"""
        analysis_lower = analysis.lower()
        
        # Count complexity indicators
        advanced_terms = ['derivative', 'integral', 'matrix', 'quantum', 'molecular', 'advanced']
        intermediate_terms = ['equation', 'formula', 'calculate', 'analyze', 'compare']
        beginner_terms = ['basic', 'simple', 'introduction', 'fundamental', 'elementary']
        
        advanced_count = sum(1 for term in advanced_terms if term in analysis_lower)
        intermediate_count = sum(1 for term in intermediate_terms if term in analysis_lower)
        beginner_count = sum(1 for term in beginner_terms if term in analysis_lower)
        
        if advanced_count > intermediate_count and advanced_count > beginner_count:
            return DifficultyLevel.ADVANCED
        elif beginner_count > intermediate_count:
            return DifficultyLevel.BEGINNER
        else:
            return DifficultyLevel.INTERMEDIATE
    
    async def _generate_next_steps(self, analysis: str) -> List[str]:
        """Generate suggested next learning steps"""
        steps = [
            "Practice similar problems to reinforce understanding",
            "Explore related concepts and applications",
            "Create your own examples using the same principles",
            "Discuss the concepts with peers or teachers",
            "Apply the knowledge to real-world scenarios"
        ]
        
        # Customize based on content type
        if "equation" in analysis.lower():
            steps.insert(0, "Solve additional equations of the same type")
        if "diagram" in analysis.lower():
            steps.insert(0, "Create your own diagrams to illustrate the concepts")
        
        return steps[:5]
    
    async def _find_related_topics(self, analysis: str) -> List[str]:
        """Find related educational topics"""
        topics = []
        analysis_lower = analysis.lower()
        
        # Topic mapping based on content
        topic_map = {
            'algebra': ['Linear Equations', 'Quadratic Functions', 'Polynomials'],
            'geometry': ['Trigonometry', 'Coordinate Geometry', 'Solid Geometry'],
            'calculus': ['Limits', 'Derivatives', 'Integrals'],
            'physics': ['Mechanics', 'Thermodynamics', 'Electromagnetism'],
            'chemistry': ['Organic Chemistry', 'Inorganic Chemistry', 'Physical Chemistry'],
            'biology': ['Cell Biology', 'Genetics', 'Ecology']
        }
        
        for key, related in topic_map.items():
            if key in analysis_lower:
                topics.extend(related)
        
        return list(set(topics))[:5]
    
    async def _generate_quiz_questions(self, analysis: str) -> List[Dict[str, Any]]:
        """Generate quiz questions based on analysis"""
        # This would use AI to generate contextual questions
        # For now, return template questions
        return [
            {
                "question": "What is the main concept explained in this analysis?",
                "type": "multiple_choice",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "correct": 0
            },
            {
                "question": "Explain the key steps in your own words.",
                "type": "open_ended"
            }
        ]
    
    async def _generate_practice_problems(self, analysis: str, analysis_type: AnalysisType) -> List[Dict[str, Any]]:
        """Generate practice problems based on analysis"""
        problems = []
        
        if analysis_type == AnalysisType.MATHEMATICAL:
            problems.append({
                "problem": "Solve a similar equation with different values",
                "difficulty": "medium",
                "hints": ["Start with the same approach", "Check your algebra"]
            })
        
        return problems
    
    async def _create_visualization_config(self, analysis: str) -> Dict[str, Any]:
        """Create configuration for interactive visualizations"""
        return {
            "type": "graph",
            "data": [],
            "options": {
                "interactive": True,
                "zoomable": True,
                "annotations": True
            }
        }


class RealTimeAnalysisService:
    """Service for real-time analysis streaming"""
    
    def __init__(self):
        self.active_streams = {}
        self.frame_buffer = {}
    
    async def start_stream(self, stream_id: str) -> Dict[str, Any]:
        """Start a real-time analysis stream"""
        self.active_streams[stream_id] = {
            "start_time": datetime.utcnow(),
            "frame_count": 0,
            "last_analysis": None
        }
        self.frame_buffer[stream_id] = []
        
        return {
            "success": True,
            "stream_id": stream_id,
            "message": "Real-time analysis stream started"
        }
    
    async def process_frame(self, request: RealTimeAnalysisRequest) -> RealTimeAnalysisResponse:
        """Process a single frame in real-time"""
        if request.stream_id not in self.active_streams:
            await self.start_stream(request.stream_id)
        
        stream_info = self.active_streams[request.stream_id]
        stream_info["frame_count"] += 1
        
        try:
            # Quick analysis for real-time processing
            analysis_result = await self._quick_frame_analysis(
                request.frame_data, 
                request.analysis_type
            )
            
            # Update stream info
            stream_info["last_analysis"] = analysis_result
            
            return RealTimeAnalysisResponse(
                success=True,
                stream_id=request.stream_id,
                frame_number=stream_info["frame_count"],
                analysis=analysis_result["analysis"],
                confidence=analysis_result["confidence"],
                detected_objects=analysis_result["objects"],
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            return RealTimeAnalysisResponse(
                success=False,
                stream_id=request.stream_id,
                frame_number=stream_info["frame_count"],
                analysis=f"Analysis failed: {str(e)}",
                confidence=0.0,
                detected_objects=[],
                timestamp=datetime.utcnow()
            )
    
    async def _quick_frame_analysis(self, frame_data: str, analysis_type: AnalysisType) -> Dict[str, Any]:
        """Perform quick analysis optimized for real-time processing"""
        
        # Decode frame
        if ',' in frame_data:
            frame_data = frame_data.split(',')[1]
        
        image_bytes = base64.b64decode(frame_data)
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Quick object detection using OpenCV
        detected_objects = await self._detect_objects_opencv(img)
        
        # Generate quick analysis
        if detected_objects:
            analysis = f"Detected: {', '.join(detected_objects)}"
            confidence = 0.8
        else:
            analysis = "No clear objects detected in frame"
            confidence = 0.3
        
        return {
            "analysis": analysis,
            "confidence": confidence,
            "objects": detected_objects
        }
    
    async def _detect_objects_opencv(self, img: np.ndarray) -> List[str]:
        """Quick object detection using OpenCV"""
        objects = []
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Detect edges
        edges = cv2.Canny(gray, 50, 150)
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Analyze contours
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 1000:  # Filter small contours
                # Approximate contour shape
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)
                
                # Classify based on number of vertices
                if len(approx) == 3:
                    objects.append("triangle")
                elif len(approx) == 4:
                    objects.append("rectangle")
                elif len(approx) > 8:
                    objects.append("circle")
                else:
                    objects.append("polygon")
        
        return list(set(objects))[:5]  # Return unique objects, max 5
    
    async def stop_stream(self, stream_id: str) -> Dict[str, Any]:
        """Stop a real-time analysis stream"""
        if stream_id in self.active_streams:
            del self.active_streams[stream_id]
        if stream_id in self.frame_buffer:
            del self.frame_buffer[stream_id]
        
        return {
            "success": True,
            "message": "Stream stopped successfully"
        }


# Service instances
advanced_image_service = AdvancedImageAnalysisService()
realtime_service = RealTimeAnalysisService()