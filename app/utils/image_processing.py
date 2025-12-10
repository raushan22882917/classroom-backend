"""Image processing utilities for Magic Learn"""

import io
import base64
from typing import Tuple, Optional
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np


class ImageProcessor:
    """Utility class for image processing operations"""
    
    @staticmethod
    def resize_image(image: Image.Image, max_size: Tuple[int, int] = (1024, 1024)) -> Image.Image:
        """Resize image while maintaining aspect ratio"""
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
        return image
    
    @staticmethod
    def enhance_image_for_analysis(image: Image.Image) -> Image.Image:
        """Enhance image quality for better AI analysis"""
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Enhance contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.2)
        
        # Enhance sharpness
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(1.1)
        
        # Reduce noise
        image = image.filter(ImageFilter.MedianFilter(size=3))
        
        return image
    
    @staticmethod
    def extract_image_metadata(image: Image.Image) -> dict:
        """Extract metadata from image"""
        return {
            "format": image.format,
            "mode": image.mode,
            "size": image.size,
            "width": image.width,
            "height": image.height,
            "has_transparency": image.mode in ('RGBA', 'LA') or 'transparency' in image.info
        }
    
    @staticmethod
    def image_to_base64(image: Image.Image, format: str = "PNG") -> str:
        """Convert PIL Image to base64 string"""
        buffer = io.BytesIO()
        image.save(buffer, format=format)
        img_str = base64.b64encode(buffer.getvalue()).decode()
        return img_str
    
    @staticmethod
    def base64_to_image(base64_string: str) -> Image.Image:
        """Convert base64 string to PIL Image"""
        # Remove data URL prefix if present
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]
        
        image_data = base64.b64decode(base64_string)
        image = Image.open(io.BytesIO(image_data))
        return image
    
    @staticmethod
    def detect_image_type(image: Image.Image) -> str:
        """Detect the type of content in the image"""
        # This is a simplified version - in production, you'd use ML models
        width, height = image.size
        aspect_ratio = width / height
        
        # Convert to grayscale for analysis
        gray = image.convert('L')
        pixels = np.array(gray)
        
        # Calculate image statistics
        mean_brightness = np.mean(pixels)
        contrast = np.std(pixels)
        
        # Simple heuristics for content type detection
        if contrast > 50 and mean_brightness < 200:
            if aspect_ratio > 1.5:
                return "diagram"
            elif 0.7 < aspect_ratio < 1.3:
                return "mathematical"
            else:
                return "sketch"
        elif mean_brightness > 200:
            return "whiteboard"
        else:
            return "general"
    
    @staticmethod
    def preprocess_for_ocr(image: Image.Image) -> Image.Image:
        """Preprocess image for better OCR results"""
        # Convert to grayscale
        image = image.convert('L')
        
        # Increase contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)
        
        # Apply threshold to create binary image
        pixels = np.array(image)
        threshold = np.mean(pixels)
        binary = (pixels > threshold) * 255
        
        # Convert back to PIL Image
        image = Image.fromarray(binary.astype(np.uint8), mode='L')
        
        return image
    
    @staticmethod
    def extract_dominant_colors(image: Image.Image, num_colors: int = 5) -> list:
        """Extract dominant colors from image"""
        # Resize for faster processing
        image = image.resize((150, 150))
        
        # Convert to RGB
        image = image.convert('RGB')
        
        # Get pixel data
        pixels = np.array(image).reshape(-1, 3)
        
        # Simple color clustering (in production, use k-means)
        unique_colors = np.unique(pixels, axis=0)
        
        # Return top colors (simplified)
        return unique_colors[:num_colors].tolist()


class GestureProcessor:
    """Utility class for processing gesture data"""
    
    @staticmethod
    def smooth_gesture_points(points: list, window_size: int = 3) -> list:
        """Smooth gesture points using moving average"""
        if len(points) < window_size:
            return points
        
        smoothed = []
        for i in range(len(points)):
            start = max(0, i - window_size // 2)
            end = min(len(points), i + window_size // 2 + 1)
            
            avg_x = sum(p.x for p in points[start:end]) / (end - start)
            avg_y = sum(p.y for p in points[start:end]) / (end - start)
            
            # Create new point with smoothed coordinates
            smoothed_point = type(points[i])(
                x=avg_x,
                y=avg_y,
                timestamp=points[i].timestamp
            )
            smoothed.append(smoothed_point)
        
        return smoothed
    
    @staticmethod
    def calculate_gesture_velocity(points: list) -> list:
        """Calculate velocity at each point in the gesture"""
        if len(points) < 2:
            return [0.0] * len(points)
        
        velocities = [0.0]  # First point has zero velocity
        
        for i in range(1, len(points)):
            dx = points[i].x - points[i-1].x
            dy = points[i].y - points[i-1].y
            dt = (points[i].timestamp - points[i-1].timestamp).total_seconds()
            
            if dt > 0:
                velocity = np.sqrt(dx**2 + dy**2) / dt
            else:
                velocity = 0.0
            
            velocities.append(velocity)
        
        return velocities
    
    @staticmethod
    def detect_gesture_pauses(points: list, velocity_threshold: float = 10.0) -> list:
        """Detect pauses in gesture based on velocity"""
        velocities = GestureProcessor.calculate_gesture_velocity(points)
        
        pauses = []
        for i, velocity in enumerate(velocities):
            if velocity < velocity_threshold:
                pauses.append(i)
        
        return pauses
    
    @staticmethod
    def normalize_gesture_coordinates(points: list, canvas_width: int, canvas_height: int) -> list:
        """Normalize gesture coordinates to 0-1 range"""
        normalized = []
        
        for point in points:
            normalized_point = type(point)(
                x=point.x / canvas_width,
                y=point.y / canvas_height,
                timestamp=point.timestamp
            )
            normalized.append(normalized_point)
        
        return normalized
    
    @staticmethod
    def calculate_bounding_box(points: list) -> dict:
        """Calculate bounding box for gesture points"""
        if not points:
            return {"min_x": 0, "min_y": 0, "max_x": 0, "max_y": 0, "width": 0, "height": 0}
        
        x_coords = [p.x for p in points]
        y_coords = [p.y for p in points]
        
        min_x, max_x = min(x_coords), max(x_coords)
        min_y, max_y = min(y_coords), max(y_coords)
        
        return {
            "min_x": min_x,
            "min_y": min_y,
            "max_x": max_x,
            "max_y": max_y,
            "width": max_x - min_x,
            "height": max_y - min_y
        }


class StoryProcessor:
    """Utility class for processing story content"""
    
    @staticmethod
    def extract_story_keywords(content: str) -> list:
        """Extract keywords from story content"""
        # Simple keyword extraction (in production, use NLP libraries)
        import re
        
        # Remove markdown formatting
        text = re.sub(r'[#*_`]', '', content)
        
        # Split into words and filter
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
        
        # Remove common words
        stop_words = {'this', 'that', 'with', 'have', 'will', 'from', 'they', 'been', 'were', 'said', 'each', 'which', 'their', 'time', 'about'}
        keywords = [word for word in words if word not in stop_words]
        
        # Return most frequent keywords
        from collections import Counter
        return [word for word, count in Counter(keywords).most_common(10)]
    
    @staticmethod
    def estimate_reading_time(content: str, words_per_minute: int = 200) -> int:
        """Estimate reading time in minutes"""
        word_count = len(content.split())
        return max(1, round(word_count / words_per_minute))
    
    @staticmethod
    def extract_educational_concepts(content: str) -> list:
        """Extract educational concepts from story content"""
        # Simple concept extraction based on patterns
        import re
        
        concepts = []
        
        # Mathematical concepts
        math_patterns = [
            r'\b(equation|formula|theorem|proof|calculation)\b',
            r'\b(algebra|geometry|calculus|trigonometry)\b',
            r'\b(ratio|proportion|percentage|fraction)\b'
        ]
        
        # Scientific concepts
        science_patterns = [
            r'\b(molecule|atom|cell|DNA|protein)\b',
            r'\b(energy|force|velocity|acceleration)\b',
            r'\b(reaction|experiment|hypothesis|theory)\b'
        ]
        
        all_patterns = math_patterns + science_patterns
        
        for pattern in all_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            concepts.extend(matches)
        
        return list(set(concepts))  # Remove duplicates
    
    @staticmethod
    def generate_story_summary(content: str, max_length: int = 200) -> str:
        """Generate a brief summary of the story"""
        # Simple summarization (in production, use advanced NLP)
        sentences = content.split('.')
        
        # Take first few sentences up to max_length
        summary = ""
        for sentence in sentences:
            if len(summary + sentence) < max_length:
                summary += sentence + "."
            else:
                break
        
        return summary.strip()


# Export utility classes
__all__ = ['ImageProcessor', 'GestureProcessor', 'StoryProcessor']