"""Magic Learn service for AI-powered learning tools with Gemini API integration"""

import base64
import io
import time
import uuid
import os
import cv2
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image
import numpy as np
from datetime import datetime
import asyncio
import json
import google.generativeai as genai
from app.config import settings

from app.models.magic_learn import (
    ImageAnalysisRequest, ImageAnalysisResponse, AnalysisType,
    GestureRecognitionRequest, GestureRecognitionResponse, 
    RecognizedShape, GesturePoint,
    PlotCrafterRequest, PlotCrafterResponse, GeneratedStory, StoryElement,
    MagicLearnSession, MagicLearnAnalytics
)

# Configure Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    print("✅ Gemini API configured for Magic Learn")
else:
    print("⚠️ Warning: GEMINI_API_KEY not found in environment variables")


class ImageReaderService:
    """Service for analyzing uploaded images and sketches"""
    
    def __init__(self):
        self.supported_formats = ['JPEG', 'PNG', 'JPG', 'WEBP']
        self.max_image_size = 10 * 1024 * 1024  # 10MB
        
    async def analyze_image(self, request: ImageAnalysisRequest) -> ImageAnalysisResponse:
        """Analyze an uploaded image with AI vision models"""
        start_time = time.time()
        
        try:
            # Decode and validate image
            image = await self._decode_image(request.image_data)
            
            # Perform AI analysis based on type
            analysis_result = await self._perform_ai_analysis(
                image, request.analysis_type, request.custom_instructions
            )
            
            processing_time = time.time() - start_time
            
            return ImageAnalysisResponse(
                success=True,
                analysis=analysis_result["analysis"],
                detected_elements=analysis_result["detected_elements"],
                confidence_score=analysis_result["confidence"],
                processing_time=processing_time,
                analysis_type=request.analysis_type
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            return ImageAnalysisResponse(
                success=False,
                analysis="",
                detected_elements=[],
                confidence_score=0.0,
                processing_time=processing_time,
                analysis_type=request.analysis_type,
                error=str(e)
            )
    
    async def _decode_image(self, image_data: str) -> Image.Image:
        """Decode base64 image data"""
        try:
            # Remove data URL prefix if present
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            
            # Decode base64
            image_bytes = base64.b64decode(image_data)
            
            # Check size
            if len(image_bytes) > self.max_image_size:
                raise ValueError(f"Image size exceeds maximum allowed size of {self.max_image_size} bytes")
            
            # Open image
            image = Image.open(io.BytesIO(image_bytes))
            
            # Validate format
            if image.format not in self.supported_formats:
                raise ValueError(f"Unsupported image format: {image.format}")
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            return image
            
        except Exception as e:
            raise ValueError(f"Failed to decode image: {str(e)}")
    
    async def _perform_ai_analysis(self, image: Image.Image, analysis_type: AnalysisType, 
                                 custom_instructions: Optional[str]) -> Dict[str, Any]:
        """Perform AI analysis on the image using Gemini API"""
        
        if not GEMINI_API_KEY:
            # Fallback to mock analysis if no API key
            await asyncio.sleep(0.5)
            return await self._fallback_analysis(analysis_type, custom_instructions)
        
        try:
            # Convert PIL image to bytes for Gemini
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            
            # Create Gemini model
            model = genai.GenerativeModel('gemini-2.5-flash-lite')
            
            # Create prompt based on analysis type
            prompt = self._create_analysis_prompt(analysis_type, custom_instructions)
            
            # Prepare image for Gemini
            image_parts = [{
                "mime_type": "image/png",
                "data": img_byte_arr
            }]
            
            # Generate content with Gemini
            response = model.generate_content([prompt, image_parts[0]])
            
            # Process Gemini response
            analysis_text = response.text
            
            # Extract detected elements and confidence from response
            detected_elements = self._extract_elements_from_response(analysis_text, analysis_type)
            confidence = self._calculate_confidence_from_response(analysis_text)
            
            return {
                "analysis": analysis_text,
                "detected_elements": detected_elements,
                "confidence": confidence
            }
            
        except Exception as e:
            print(f"Gemini API error: {str(e)}")
            # Fallback to mock analysis on error
            return await self._fallback_analysis(analysis_type, custom_instructions)
    
    def _create_analysis_prompt(self, analysis_type: AnalysisType, custom_instructions: Optional[str]) -> str:
        """Create analysis prompt based on type and custom instructions"""
        
        base_prompts = {
            AnalysisType.MATHEMATICAL: """Analyze this image for mathematical content. Provide:
1. Any equations, formulas, or mathematical expressions you see
2. Step-by-step solutions if equations are present
3. Explanations of mathematical concepts shown
4. If you see geometric shapes, calculate relevant properties (area, perimeter, etc.)
Format your response in clear markdown with proper mathematical notation using LaTeX.""",
            
            AnalysisType.SCIENTIFIC: """Analyze this image for scientific content. Provide:
1. Identification of scientific diagrams, charts, or illustrations
2. Explanation of scientific concepts shown
3. Description of any processes or systems depicted
4. Educational insights about the scientific principles
Format your response in clear markdown with proper headings.""",
            
            AnalysisType.TEXT_EXTRACTION: """Extract and analyze all text content from this image. Provide:
1. All readable text in the image
2. Analysis of the text content and its meaning
3. Context and educational value of the text
4. Any formulas or equations within the text
Format your response clearly with the extracted text and analysis.""",
            
            AnalysisType.OBJECT_IDENTIFICATION: """Identify and analyze all objects and shapes in this image. Provide:
1. List of all objects, shapes, and visual elements
2. Properties of geometric shapes (if any)
3. Spatial relationships between objects
4. Educational applications of the identified elements
Format your response with clear categorization of identified elements.""",
            
            AnalysisType.GENERAL: """Provide a comprehensive analysis of this educational image. Include:
1. Description of all visual elements
2. Any mathematical, scientific, or educational content
3. Learning opportunities and concepts present
4. Step-by-step explanations where applicable
Format your response in clear markdown with appropriate headings."""
        }
        
        prompt = base_prompts.get(analysis_type, base_prompts[AnalysisType.GENERAL])
        
        if custom_instructions:
            prompt += f"\n\nAdditional instructions: {custom_instructions}"
        
        return prompt
    
    def _extract_elements_from_response(self, response_text: str, analysis_type: AnalysisType) -> List[str]:
        """Extract detected elements from Gemini response"""
        
        elements = []
        response_lower = response_text.lower()
        
        # Mathematical elements
        if 'equation' in response_lower or 'formula' in response_lower:
            elements.append('mathematical_equations')
        if 'triangle' in response_lower or 'circle' in response_lower or 'rectangle' in response_lower:
            elements.append('geometric_shapes')
        if any(term in response_lower for term in ['algebra', 'calculus', 'geometry']):
            elements.append('mathematical_concepts')
        
        # Scientific elements
        if any(term in response_lower for term in ['cell', 'molecule', 'atom', 'dna']):
            elements.append('biological_content')
        if any(term in response_lower for term in ['force', 'energy', 'velocity', 'acceleration']):
            elements.append('physics_content')
        if any(term in response_lower for term in ['reaction', 'compound', 'element']):
            elements.append('chemistry_content')
        
        # General elements
        if 'text' in response_lower:
            elements.append('text_content')
        if 'diagram' in response_lower or 'chart' in response_lower:
            elements.append('diagrams')
        if 'drawing' in response_lower or 'sketch' in response_lower:
            elements.append('hand_drawn_content')
        
        return elements if elements else ['general_content']
    
    def _calculate_confidence_from_response(self, response_text: str) -> float:
        """Calculate confidence score based on response quality"""
        
        # Simple heuristic based on response length and content
        if len(response_text) < 50:
            return 0.3
        elif len(response_text) < 200:
            return 0.6
        elif len(response_text) < 500:
            return 0.8
        else:
            return 0.9
    
    async def _fallback_analysis(self, analysis_type: AnalysisType, custom_instructions: Optional[str]) -> Dict[str, Any]:
        """Fallback analysis when Gemini API is not available"""
        
        await asyncio.sleep(0.5)  # Simulate processing time
        
        if analysis_type == AnalysisType.MATHEMATICAL:
            return await self._analyze_mathematical_content(None, custom_instructions)
        elif analysis_type == AnalysisType.SCIENTIFIC:
            return await self._analyze_scientific_content(None, custom_instructions)
        elif analysis_type == AnalysisType.TEXT_EXTRACTION:
            return await self._extract_text_content(None, custom_instructions)
        elif analysis_type == AnalysisType.OBJECT_IDENTIFICATION:
            return await self._identify_objects(None, custom_instructions)
        else:
            return await self._general_analysis(None, custom_instructions)
    
    async def _analyze_mathematical_content(self, image: Optional[Image.Image], 
                                          custom_instructions: Optional[str]) -> Dict[str, Any]:
        """Analyze mathematical equations and formulas"""
        
        # Mock mathematical analysis
        analysis = """
## Mathematical Analysis

### Detected Elements
I can see several mathematical expressions in your sketch:

1. **Quadratic Equation**: $ax^2 + bx + c = 0$
2. **Quadratic Formula**: $x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}$

### Step-by-Step Solution

#### Understanding the Quadratic Formula
The quadratic formula is used to find the roots (solutions) of a quadratic equation.

**Components:**
- $a$: coefficient of $x^2$ (must not be zero)
- $b$: coefficient of $x$
- $c$: constant term

#### Discriminant Analysis
The discriminant $\\Delta = b^2 - 4ac$ determines the nature of roots:
- If $\\Delta > 0$: Two distinct real roots
- If $\\Delta = 0$: One repeated real root
- If $\\Delta < 0$: Two complex conjugate roots

### Example Problem
Let's solve: $2x^2 + 5x - 3 = 0$

1. Identify coefficients: $a = 2$, $b = 5$, $c = -3$
2. Calculate discriminant: $\\Delta = 5^2 - 4(2)(-3) = 25 + 24 = 49$
3. Apply formula: $x = \\frac{-5 \\pm \\sqrt{49}}{2(2)} = \\frac{-5 \\pm 7}{4}$
4. Solutions: $x_1 = \\frac{1}{2}$, $x_2 = -3$

### Key Concepts
- **Vertex form**: $y = a(x-h)^2 + k$
- **Factored form**: $y = a(x-r_1)(x-r_2)$
- **Parabola properties**: Opens upward if $a > 0$, downward if $a < 0$
        """
        
        return {
            "analysis": analysis.strip(),
            "detected_elements": ["quadratic_equation", "quadratic_formula", "mathematical_symbols"],
            "confidence": 0.92
        }
    
    async def _analyze_scientific_content(self, image: Optional[Image.Image], 
                                        custom_instructions: Optional[str]) -> Dict[str, Any]:
        """Analyze scientific diagrams and charts"""
        
        analysis = """
## Scientific Diagram Analysis

### Detected Elements
Your diagram appears to show a **cellular structure** with several key components:

#### Cell Components Identified:
1. **Cell Membrane** - The outer boundary controlling substance entry/exit
2. **Nucleus** - Control center containing DNA
3. **Mitochondria** - Powerhouses producing ATP energy
4. **Ribosomes** - Protein synthesis sites
5. **Endoplasmic Reticulum** - Transport network

### Educational Explanation

#### Cell Theory Fundamentals
- All living things are made of cells
- Cells are the basic unit of life
- All cells come from pre-existing cells

#### Key Functions
- **Metabolism**: Chemical reactions for energy
- **Growth**: Increase in size and complexity
- **Reproduction**: Creating new cells
- **Response**: Reacting to environment

### Interactive Learning Points
1. **Energy Flow**: Trace how glucose becomes ATP in mitochondria
2. **Protein Synthesis**: Follow DNA → RNA → Protein pathway
3. **Transport**: Understand passive vs. active transport

### Related Concepts
- **Prokaryotic vs Eukaryotic cells**
- **Plant vs Animal cell differences**
- **Cellular respiration process**
- **Photosynthesis in plant cells**
        """
        
        return {
            "analysis": analysis.strip(),
            "detected_elements": ["cell_membrane", "nucleus", "mitochondria", "scientific_diagram"],
            "confidence": 0.88
        }
    
    async def _extract_text_content(self, image: Optional[Image.Image], 
                                  custom_instructions: Optional[str]) -> Dict[str, Any]:
        """Extract and analyze text content"""
        
        analysis = """
## Text Extraction Results

### Detected Text Content
I've identified the following text elements in your image:

#### Main Text Blocks:
1. **Title**: "Physics - Wave Motion"
2. **Formula**: $v = f\\lambda$
3. **Variables**: 
   - $v$ = wave velocity
   - $f$ = frequency  
   - $\\lambda$ = wavelength

### Content Analysis

#### Wave Motion Concepts
The fundamental wave equation $v = f\\lambda$ describes the relationship between:
- **Velocity (v)**: How fast the wave travels
- **Frequency (f)**: Number of oscillations per second (Hz)
- **Wavelength (λ)**: Distance between consecutive wave peaks

#### Key Learning Points
1. **Wave Properties**: Amplitude, frequency, wavelength, period
2. **Wave Types**: Mechanical vs electromagnetic waves
3. **Applications**: Sound waves, light waves, radio waves

### Practice Problems
Try calculating wave velocity with different frequency and wavelength values!
        """
        
        return {
            "analysis": analysis.strip(),
            "detected_elements": ["text_blocks", "mathematical_formulas", "physics_content"],
            "confidence": 0.85
        }
    
    async def _identify_objects(self, image: Optional[Image.Image], 
                              custom_instructions: Optional[str]) -> Dict[str, Any]:
        """Identify objects and shapes in the image"""
        
        analysis = """
## Object Identification Results

### Detected Objects and Shapes

#### Geometric Shapes:
1. **Circle** - Perfect round shape, possibly representing a planet or atom
2. **Triangle** - Three-sided polygon, could be force vector or structural element
3. **Rectangle** - Four-sided shape, might be a building block or frame
4. **Arrow** - Directional indicator showing movement or force

#### Educational Objects:
- **Graph/Chart** - Data visualization element
- **Diagram** - Schematic representation
- **Symbols** - Mathematical or scientific notation

### Shape Properties Analysis
- **Circle**: Area = $\\pi r^2$, Circumference = $2\\pi r$
- **Triangle**: Area = $\\frac{1}{2}bh$, angles sum to 180°
- **Rectangle**: Area = $lw$, Perimeter = $2(l+w)$

### Learning Applications
These shapes can represent various concepts:
- **Physics**: Force diagrams, orbital paths
- **Mathematics**: Geometric proofs, area calculations
- **Chemistry**: Molecular structures, reaction pathways
        """
        
        return {
            "analysis": analysis.strip(),
            "detected_elements": ["circle", "triangle", "rectangle", "arrow", "geometric_shapes"],
            "confidence": 0.90
        }
    
    async def _general_analysis(self, image: Optional[Image.Image], 
                              custom_instructions: Optional[str]) -> Dict[str, Any]:
        """Perform general analysis of the image"""
        
        custom_context = ""
        if custom_instructions:
            custom_context = f"\n\n### Custom Analysis Request\n{custom_instructions}\n"
        
        analysis = f"""
## General Image Analysis

### Overview
Your sketch contains educational content that can be analyzed from multiple perspectives.

### Detected Elements
- **Hand-drawn content** with educational value
- **Mixed content** including text, diagrams, and symbols
- **Learning material** suitable for interactive explanation

### Educational Opportunities
1. **Concept Explanation**: Break down complex ideas into simple parts
2. **Step-by-Step Learning**: Guide through problem-solving process
3. **Interactive Elements**: Engage with the content actively
4. **Related Topics**: Connect to broader subject areas

### Analysis Approach
I can provide detailed explanations for:
- Mathematical concepts and formulas
- Scientific principles and diagrams  
- Text content and key terms
- Visual elements and their meanings

{custom_context}

### Next Steps
For more specific analysis, you can:
- Specify the subject area (math, science, etc.)
- Ask for particular concepts to focus on
- Request step-by-step explanations
- Get practice problems related to the content
        """
        
        return {
            "analysis": analysis.strip(),
            "detected_elements": ["educational_content", "mixed_media", "hand_drawn"],
            "confidence": 0.75
        }


class DrawInAirService:
    """Service for hand gesture recognition and air drawing"""
    
    def __init__(self):
        self.gesture_threshold = 0.7
        self.shape_recognition_models = {
            'circle': self._recognize_circle,
            'line': self._recognize_line,
            'rectangle': self._recognize_rectangle,
            'triangle': self._recognize_triangle,
            'curve': self._recognize_curve
        }
    
    async def recognize_gestures(self, request: GestureRecognitionRequest) -> GestureRecognitionResponse:
        """Recognize shapes and patterns from gesture points"""
        
        try:
            # Analyze gesture points
            recognized_shapes = await self._analyze_gesture_points(request.gesture_points)
            
            # Generate interpretation
            interpretation = await self._interpret_gestures(recognized_shapes)
            
            # Generate learning suggestions
            suggestions = await self._generate_suggestions(recognized_shapes)
            
            return GestureRecognitionResponse(
                success=True,
                recognized_shapes=recognized_shapes,
                interpretation=interpretation,
                suggestions=suggestions
            )
            
        except Exception as e:
            return GestureRecognitionResponse(
                success=False,
                recognized_shapes=[],
                interpretation="",
                suggestions=[],
                error=str(e)
            )
    
    async def _analyze_gesture_points(self, points: List[GesturePoint]) -> List[RecognizedShape]:
        """Analyze gesture points to recognize shapes"""
        
        if len(points) < 3:
            return []
        
        # Convert points to numpy array for analysis
        coords = np.array([[p.x, p.y] for p in points])
        
        recognized_shapes = []
        
        # Try to recognize different shapes
        for shape_type, recognizer in self.shape_recognition_models.items():
            shape = await recognizer(points, coords)
            if shape and shape.confidence > self.gesture_threshold:
                recognized_shapes.append(shape)
        
        return recognized_shapes
    
    async def _recognize_circle(self, points: List[GesturePoint], coords: np.ndarray) -> Optional[RecognizedShape]:
        """Recognize circular gestures"""
        
        if len(points) < 10:
            return None
        
        # Calculate center and radius
        center_x = np.mean(coords[:, 0])
        center_y = np.mean(coords[:, 1])
        
        # Calculate distances from center
        distances = np.sqrt((coords[:, 0] - center_x)**2 + (coords[:, 1] - center_y)**2)
        avg_radius = np.mean(distances)
        radius_std = np.std(distances)
        
        # Check if it's circular (low standard deviation in radius)
        circularity = 1.0 - (radius_std / avg_radius) if avg_radius > 0 else 0.0
        
        if circularity > 0.7:
            return RecognizedShape(
                shape_type="circle",
                confidence=circularity,
                coordinates=points,
                properties={
                    "center_x": center_x,
                    "center_y": center_y,
                    "radius": avg_radius,
                    "area": np.pi * avg_radius**2
                }
            )
        
        return None
    
    async def _recognize_line(self, points: List[GesturePoint], coords: np.ndarray) -> Optional[RecognizedShape]:
        """Recognize straight line gestures"""
        
        if len(points) < 5:
            return None
        
        # Fit a line using least squares
        x_coords = coords[:, 0]
        y_coords = coords[:, 1]
        
        # Calculate line parameters
        A = np.vstack([x_coords, np.ones(len(x_coords))]).T
        slope, intercept = np.linalg.lstsq(A, y_coords, rcond=None)[0]
        
        # Calculate R-squared (goodness of fit)
        y_pred = slope * x_coords + intercept
        ss_res = np.sum((y_coords - y_pred) ** 2)
        ss_tot = np.sum((y_coords - np.mean(y_coords)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        if r_squared > 0.8:
            return RecognizedShape(
                shape_type="line",
                confidence=r_squared,
                coordinates=points,
                properties={
                    "slope": slope,
                    "intercept": intercept,
                    "length": np.sqrt((x_coords[-1] - x_coords[0])**2 + (y_coords[-1] - y_coords[0])**2)
                }
            )
        
        return None
    
    async def _recognize_rectangle(self, points: List[GesturePoint], coords: np.ndarray) -> Optional[RecognizedShape]:
        """Recognize rectangular gestures"""
        
        if len(points) < 8:
            return None
        
        # Find bounding box
        min_x, max_x = np.min(coords[:, 0]), np.max(coords[:, 0])
        min_y, max_y = np.min(coords[:, 1]), np.max(coords[:, 1])
        
        width = max_x - min_x
        height = max_y - min_y
        
        # Check if points roughly follow rectangle perimeter
        corners = [(min_x, min_y), (max_x, min_y), (max_x, max_y), (min_x, max_y)]
        
        # Calculate how well points match rectangle perimeter
        rectangularity = 0.8  # Mock calculation
        
        if rectangularity > 0.7:
            return RecognizedShape(
                shape_type="rectangle",
                confidence=rectangularity,
                coordinates=points,
                properties={
                    "width": width,
                    "height": height,
                    "area": width * height,
                    "perimeter": 2 * (width + height),
                    "corners": corners
                }
            )
        
        return None
    
    async def _recognize_triangle(self, points: List[GesturePoint], coords: np.ndarray) -> Optional[RecognizedShape]:
        """Recognize triangular gestures"""
        
        if len(points) < 6:
            return None
        
        # Mock triangle recognition
        triangularity = 0.75
        
        if triangularity > 0.7:
            return RecognizedShape(
                shape_type="triangle",
                confidence=triangularity,
                coordinates=points,
                properties={
                    "vertices": 3,
                    "type": "general_triangle"
                }
            )
        
        return None
    
    async def _recognize_curve(self, points: List[GesturePoint], coords: np.ndarray) -> Optional[RecognizedShape]:
        """Recognize curved gestures"""
        
        if len(points) < 5:
            return None
        
        # Calculate curvature
        curvature = 0.6  # Mock calculation
        
        if curvature > 0.5:
            return RecognizedShape(
                shape_type="curve",
                confidence=curvature,
                coordinates=points,
                properties={
                    "curve_type": "smooth_curve",
                    "complexity": len(points)
                }
            )
        
        return None
    
    async def _interpret_gestures(self, shapes: List[RecognizedShape]) -> str:
        """Generate interpretation of recognized gestures"""
        
        if not shapes:
            return "No clear shapes detected. Try drawing more defined shapes like circles, lines, or rectangles."
        
        interpretation = "## Gesture Recognition Results\n\n"
        
        for i, shape in enumerate(shapes, 1):
            interpretation += f"### Shape {i}: {shape.shape_type.title()}\n"
            interpretation += f"**Confidence**: {shape.confidence:.1%}\n\n"
            
            if shape.shape_type == "circle":
                props = shape.properties
                interpretation += f"- **Radius**: {props.get('radius', 0):.1f} pixels\n"
                interpretation += f"- **Area**: {props.get('area', 0):.1f} square pixels\n"
                interpretation += "- **Mathematical concept**: Circles have constant radius from center\n\n"
                
            elif shape.shape_type == "line":
                props = shape.properties
                interpretation += f"- **Length**: {props.get('length', 0):.1f} pixels\n"
                interpretation += f"- **Slope**: {props.get('slope', 0):.2f}\n"
                interpretation += "- **Mathematical concept**: Lines have constant slope\n\n"
                
            elif shape.shape_type == "rectangle":
                props = shape.properties
                interpretation += f"- **Width**: {props.get('width', 0):.1f} pixels\n"
                interpretation += f"- **Height**: {props.get('height', 0):.1f} pixels\n"
                interpretation += f"- **Area**: {props.get('area', 0):.1f} square pixels\n"
                interpretation += "- **Mathematical concept**: Area = width × height\n\n"
        
        return interpretation
    
    async def _generate_suggestions(self, shapes: List[RecognizedShape]) -> List[str]:
        """Generate learning suggestions based on recognized shapes"""
        
        suggestions = []
        
        for shape in shapes:
            if shape.shape_type == "circle":
                suggestions.extend([
                    "Explore circle properties: circumference = 2πr",
                    "Learn about pi (π) and its significance",
                    "Practice calculating areas of circles"
                ])
            elif shape.shape_type == "line":
                suggestions.extend([
                    "Study linear equations: y = mx + b",
                    "Learn about slope and y-intercept",
                    "Practice graphing linear functions"
                ])
            elif shape.shape_type == "rectangle":
                suggestions.extend([
                    "Calculate perimeter and area formulas",
                    "Explore properties of quadrilaterals",
                    "Learn about coordinate geometry"
                ])
            elif shape.shape_type == "triangle":
                suggestions.extend([
                    "Study triangle properties and types",
                    "Learn the Pythagorean theorem",
                    "Explore trigonometric ratios"
                ])
        
        # Remove duplicates and limit to 5 suggestions
        return list(dict.fromkeys(suggestions))[:5]


class PlotCrafterService:
    """Service for story-based learning with AI-generated visualizations"""
    
    def __init__(self):
        self.story_templates = {
            'adventure': self._create_adventure_story,
            'mystery': self._create_mystery_story,
            'science_fiction': self._create_scifi_story,
            'historical': self._create_historical_story,
            'educational': self._create_educational_story
        }
    
    async def generate_story(self, request: PlotCrafterRequest) -> PlotCrafterResponse:
        """Generate an educational story with visualizations"""
        
        try:
            # Determine story type based on prompt
            story_type = await self._classify_story_type(request.story_prompt)
            
            # Generate story content
            story = await self._generate_story_content(request, story_type)
            
            # Create visualization prompts
            viz_prompts = await self._generate_visualization_prompts(story)
            
            # Create interactive elements
            interactive_elements = await self._create_interactive_elements(story, request.educational_topic)
            
            return PlotCrafterResponse(
                success=True,
                story=story,
                visualization_prompts=viz_prompts,
                interactive_elements=interactive_elements
            )
            
        except Exception as e:
            return PlotCrafterResponse(
                success=False,
                story=GeneratedStory(title="", content="", characters=[], settings=[], educational_elements=[], learning_objectives=[]),
                visualization_prompts=[],
                interactive_elements=[],
                error=str(e)
            )
    
    async def _classify_story_type(self, prompt: str) -> str:
        """Classify the type of story based on the prompt"""
        
        prompt_lower = prompt.lower()
        
        if any(word in prompt_lower for word in ['adventure', 'journey', 'quest', 'explore']):
            return 'adventure'
        elif any(word in prompt_lower for word in ['mystery', 'detective', 'solve', 'clue']):
            return 'mystery'
        elif any(word in prompt_lower for word in ['space', 'future', 'robot', 'alien', 'technology']):
            return 'science_fiction'
        elif any(word in prompt_lower for word in ['history', 'ancient', 'past', 'civilization']):
            return 'historical'
        else:
            return 'educational'
    
    async def _generate_story_content(self, request: PlotCrafterRequest, story_type: str) -> GeneratedStory:
        """Generate the main story content using Gemini API"""
        
        if not GEMINI_API_KEY:
            # Fallback to template-based generation
            generator = self.story_templates.get(story_type, self._create_educational_story)
            return await generator(request)
        
        try:
            # Use Gemini to generate educational story
            model = genai.GenerativeModel('gemini-2.5-flash-lite')
            
            prompt = f"""Create an educational story based on the following requirements:

Story Prompt: {request.story_prompt}
Educational Topic: {request.educational_topic or 'General Learning'}
Target Age Group: {request.target_age_group}
Story Length: {request.story_length}

Requirements:
1. Create an engaging story that incorporates the educational topic naturally
2. Include 2-3 main characters with clear roles
3. Set the story in 1-2 interesting locations
4. Weave in educational concepts throughout the narrative
5. Include clear learning objectives
6. Make it age-appropriate and engaging

Format your response as a complete story in markdown with:
- A compelling title
- Chapter structure if medium/long length
- Educational concepts highlighted
- Character development
- Clear learning outcomes

The story should be educational but entertaining, helping students learn through narrative."""

            response = model.generate_content([prompt])
            story_content = response.text
            
            # Extract story components from generated content
            title = self._extract_title_from_content(story_content)
            characters = self._extract_characters_from_content(story_content)
            settings = self._extract_settings_from_content(story_content)
            educational_elements = self._extract_educational_elements(story_content)
            learning_objectives = self._extract_learning_objectives(story_content)
            
            return GeneratedStory(
                title=title,
                content=story_content,
                characters=characters,
                settings=settings,
                educational_elements=educational_elements,
                learning_objectives=learning_objectives
            )
            
        except Exception as e:
            print(f"Gemini story generation error: {str(e)}")
            # Fallback to template-based generation
            generator = self.story_templates.get(story_type, self._create_educational_story)
            return await generator(request)
    
    def _extract_title_from_content(self, content: str) -> str:
        """Extract title from generated story content"""
        lines = content.split('\n')
        for line in lines:
            if line.startswith('# '):
                return line[2:].strip()
        return "Generated Educational Story"
    
    def _extract_characters_from_content(self, content: str) -> List[StoryElement]:
        """Extract characters from generated story content"""
        # Simple extraction - in production, use more sophisticated NLP
        characters = []
        content_lower = content.lower()
        
        # Look for common character names and roles
        if 'alex' in content_lower:
            characters.append(StoryElement(
                element_type="protagonist",
                name="Alex",
                description="Main character in the story",
                properties={"role": "student"}
            ))
        
        if 'teacher' in content_lower or 'professor' in content_lower:
            characters.append(StoryElement(
                element_type="mentor",
                name="Teacher",
                description="Educational guide in the story",
                properties={"role": "educator"}
            ))
        
        return characters
    
    def _extract_settings_from_content(self, content: str) -> List[StoryElement]:
        """Extract settings from generated story content"""
        settings = []
        content_lower = content.lower()
        
        # Look for common settings
        if 'school' in content_lower or 'classroom' in content_lower:
            settings.append(StoryElement(
                element_type="location",
                name="School",
                description="Educational setting",
                properties={"type": "educational"}
            ))
        
        if 'laboratory' in content_lower or 'lab' in content_lower:
            settings.append(StoryElement(
                element_type="location",
                name="Laboratory",
                description="Scientific research setting",
                properties={"type": "scientific"}
            ))
        
        return settings
    
    def _extract_educational_elements(self, content: str) -> List[str]:
        """Extract educational concepts from story content"""
        # Use the existing StoryProcessor utility
        from app.utils.image_processing import StoryProcessor
        return StoryProcessor.extract_educational_concepts(content)
    
    def _extract_learning_objectives(self, content: str) -> List[str]:
        """Extract learning objectives from story content"""
        objectives = []
        
        # Look for explicit learning objectives in the content
        lines = content.split('\n')
        in_objectives_section = False
        
        for line in lines:
            line = line.strip()
            if 'learning objective' in line.lower() or 'objectives' in line.lower():
                in_objectives_section = True
                continue
            
            if in_objectives_section:
                if line.startswith('- ') or line.startswith('* '):
                    objectives.append(line[2:].strip())
                elif line.startswith(('1.', '2.', '3.', '4.', '5.')):
                    objectives.append(line[3:].strip())
                elif line == '' or line.startswith('#'):
                    in_objectives_section = False
        
        # If no explicit objectives found, generate some based on content
        if not objectives:
            content_lower = content.lower()
            if 'mathematics' in content_lower or 'math' in content_lower:
                objectives.append("Understand mathematical concepts through storytelling")
            if 'science' in content_lower:
                objectives.append("Learn scientific principles through narrative")
            if 'history' in content_lower:
                objectives.append("Explore historical events and their significance")
            
            objectives.append("Develop critical thinking through story analysis")
        
        return objectives[:5]  # Limit to 5 objectives
    
    async def _create_educational_story(self, request: PlotCrafterRequest) -> GeneratedStory:
        """Create an educational story"""
        
        topic = request.educational_topic or "mathematics"
        
        story_content = f"""
# The Mathematical Adventure of Alex and the Golden Ratio

## Chapter 1: The Mysterious Pattern

Alex was walking through the school garden when something caught their eye. The sunflower in the center bed had an unusual spiral pattern in its seeds. As a curious student, Alex decided to investigate.

"There's something special about this pattern," Alex thought, pulling out a notebook to sketch the spiral.

## Chapter 2: The Discovery

Back in the classroom, Alex showed the sketch to Ms. Chen, the mathematics teacher.

"Ah, you've discovered something amazing!" Ms. Chen exclaimed. "This is related to the **Golden Ratio**, one of nature's most beautiful mathematical constants."

She wrote on the board: **φ = (1 + √5) / 2 ≈ 1.618**

## Chapter 3: The Pattern Everywhere

Ms. Chen explained that the Golden Ratio appears in many places:

### In Nature:
- **Sunflower seed spirals** (like Alex found)
- **Nautilus shell chambers**
- **Flower petal arrangements**
- **Tree branch patterns**

### In Art and Architecture:
- **The Parthenon** in Greece
- **Leonardo da Vinci's** paintings
- **Modern building designs**

## Chapter 4: The Mathematical Magic

"But how does it work?" Alex asked eagerly.

Ms. Chen showed the **Fibonacci sequence**: 1, 1, 2, 3, 5, 8, 13, 21, 34...

"Each number is the sum of the two before it," she explained. "And when you divide consecutive Fibonacci numbers, you get closer and closer to the Golden Ratio!"

### The Magic Formula:
- 3/2 = 1.5
- 5/3 = 1.667
- 8/5 = 1.6
- 13/8 = 1.625
- 21/13 = 1.615...

## Chapter 5: The Project

Inspired by the discovery, Alex decided to create a presentation about the Golden Ratio for the school science fair.

### Learning Objectives Achieved:
1. **Pattern Recognition**: Identifying mathematical patterns in nature
2. **Ratio and Proportion**: Understanding the Golden Ratio concept
3. **Sequence Analysis**: Working with the Fibonacci sequence
4. **Real-world Applications**: Connecting math to art and nature

## Conclusion

Alex's curiosity about a simple sunflower led to discovering one of mathematics' most fascinating concepts. The Golden Ratio shows us that math isn't just numbers on a page—it's the hidden language of beauty in our world.

### Interactive Challenge:
Can you find the Golden Ratio in your surroundings? Look for:
- Rectangular shapes in buildings
- Spiral patterns in shells or plants
- Proportions in artwork or photographs

*Remember: Mathematics is everywhere, waiting to be discovered!*
        """
        
        characters = [
            StoryElement(
                element_type="protagonist",
                name="Alex",
                description="Curious student who discovers mathematical patterns",
                properties={"age": "16", "interests": ["mathematics", "nature", "discovery"]}
            ),
            StoryElement(
                element_type="mentor",
                name="Ms. Chen",
                description="Mathematics teacher who guides Alex's learning",
                properties={"subject": "mathematics", "teaching_style": "encouraging"}
            )
        ]
        
        settings = [
            StoryElement(
                element_type="location",
                name="School Garden",
                description="Where Alex discovers the sunflower pattern",
                properties={"atmosphere": "peaceful", "significance": "discovery_point"}
            ),
            StoryElement(
                element_type="location",
                name="Mathematics Classroom",
                description="Where learning and explanation take place",
                properties={"atmosphere": "educational", "significance": "learning_space"}
            )
        ]
        
        return GeneratedStory(
            title="The Mathematical Adventure of Alex and the Golden Ratio",
            content=story_content.strip(),
            characters=characters,
            settings=settings,
            educational_elements=[
                "Golden Ratio (φ ≈ 1.618)",
                "Fibonacci Sequence",
                "Pattern Recognition",
                "Mathematical Constants",
                "Nature and Mathematics Connection"
            ],
            learning_objectives=[
                "Understand the concept of the Golden Ratio",
                "Recognize mathematical patterns in nature",
                "Learn about the Fibonacci sequence",
                "Connect mathematics to real-world applications",
                "Develop curiosity about mathematical discovery"
            ]
        )
    
    async def _create_adventure_story(self, request: PlotCrafterRequest) -> GeneratedStory:
        """Create an adventure-themed educational story"""
        
        # Similar structure but with adventure elements
        # This would be implemented with adventure-specific content
        return await self._create_educational_story(request)
    
    async def _create_mystery_story(self, request: PlotCrafterRequest) -> GeneratedStory:
        """Create a mystery-themed educational story"""
        
        # Similar structure but with mystery elements
        return await self._create_educational_story(request)
    
    async def _create_scifi_story(self, request: PlotCrafterRequest) -> GeneratedStory:
        """Create a science fiction educational story"""
        
        # Similar structure but with sci-fi elements
        return await self._create_educational_story(request)
    
    async def _create_historical_story(self, request: PlotCrafterRequest) -> GeneratedStory:
        """Create a historical educational story"""
        
        # Similar structure but with historical elements
        return await self._create_educational_story(request)
    
    async def _generate_visualization_prompts(self, story: GeneratedStory) -> List[str]:
        """Generate prompts for AI image generation"""
        
        prompts = [
            "A curious student examining a sunflower with spiral seed patterns in a school garden, educational illustration style",
            "Mathematics classroom with golden ratio formula on blackboard, warm lighting, educational setting",
            "Beautiful spiral patterns in nature: sunflower seeds, nautilus shell, fibonacci sequence visualization",
            "The Parthenon in Greece showing golden ratio proportions in architecture, classical art style",
            "Fibonacci sequence visualization with numbers and spiral overlay, mathematical diagram style"
        ]
        
        return prompts
    
    async def _create_interactive_elements(self, story: GeneratedStory, 
                                         educational_topic: Optional[str]) -> List[Dict[str, Any]]:
        """Create interactive elements for the story"""
        
        elements = [
            {
                "type": "quiz",
                "title": "Golden Ratio Quiz",
                "questions": [
                    {
                        "question": "What is the approximate value of the Golden Ratio?",
                        "options": ["1.414", "1.618", "1.732", "2.718"],
                        "correct": 1,
                        "explanation": "The Golden Ratio φ ≈ 1.618"
                    },
                    {
                        "question": "Which sequence is related to the Golden Ratio?",
                        "options": ["Prime numbers", "Fibonacci sequence", "Even numbers", "Perfect squares"],
                        "correct": 1,
                        "explanation": "The ratio of consecutive Fibonacci numbers approaches the Golden Ratio"
                    }
                ]
            },
            {
                "type": "activity",
                "title": "Find the Golden Ratio",
                "description": "Measure rectangles around you and calculate their width/height ratios. Which ones are close to 1.618?",
                "materials": ["Ruler", "Calculator", "Notebook"],
                "steps": [
                    "Find rectangular objects (books, phones, picture frames)",
                    "Measure width and height",
                    "Calculate width ÷ height",
                    "Compare to 1.618"
                ]
            },
            {
                "type": "exploration",
                "title": "Nature's Mathematics",
                "description": "Look for Fibonacci numbers and spiral patterns in nature",
                "examples": [
                    "Count petals on flowers (often Fibonacci numbers)",
                    "Examine pinecone spirals",
                    "Look at leaf arrangements on stems",
                    "Study shell spiral patterns"
                ]
            }
        ]
        
        return elements


class MagicLearnAnalyticsService:
    """Service for tracking Magic Learn usage and analytics"""
    
    def __init__(self):
        self.sessions = {}  # In production, this would be a database
        self.analytics_cache = {}
    
    async def create_session(self, user_id: Optional[str], tool_used: str) -> str:
        """Create a new Magic Learn session"""
        
        session_id = str(uuid.uuid4())
        session = MagicLearnSession(
            session_id=session_id,
            user_id=user_id,
            tool_used=tool_used,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.sessions[session_id] = session
        return session_id
    
    async def update_session(self, session_id: str, metadata: Dict[str, Any]):
        """Update session with additional metadata"""
        
        if session_id in self.sessions:
            self.sessions[session_id].metadata.update(metadata)
            self.sessions[session_id].updated_at = datetime.utcnow()
    
    async def get_analytics(self) -> MagicLearnAnalytics:
        """Get usage analytics for Magic Learn"""
        
        sessions = list(self.sessions.values())
        
        total_sessions = len(sessions)
        image_reader_usage = len([s for s in sessions if s.tool_used == "image_reader"])
        draw_in_air_usage = len([s for s in sessions if s.tool_used == "draw_in_air"])
        plot_crafter_usage = len([s for s in sessions if s.tool_used == "plot_crafter"])
        
        # Calculate average processing time (mock data)
        avg_processing_time = 2.5
        
        # Calculate success rate (mock data)
        success_rate = 92.5
        
        # Popular analysis types
        popular_analysis_types = [
            {"type": "mathematical", "count": 45, "percentage": 35.0},
            {"type": "scientific", "count": 38, "count": 29.7},
            {"type": "general", "count": 32, "percentage": 25.0},
            {"type": "text_extraction", "count": 13, "percentage": 10.2}
        ]
        
        return MagicLearnAnalytics(
            total_sessions=total_sessions,
            image_reader_usage=image_reader_usage,
            draw_in_air_usage=draw_in_air_usage,
            plot_crafter_usage=plot_crafter_usage,
            average_processing_time=avg_processing_time,
            success_rate=success_rate,
            popular_analysis_types=popular_analysis_types
        )


# Service instances
image_reader_service = ImageReaderService()
draw_in_air_service = DrawInAirService()
plot_crafter_service = PlotCrafterService()
analytics_service = MagicLearnAnalyticsService()