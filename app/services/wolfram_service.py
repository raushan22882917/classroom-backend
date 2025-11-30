"""Wolfram Alpha service for mathematical verification"""

import re
import asyncio
from typing import Optional, List, Dict
import wolframalpha
import xmltodict
from redis import Redis
import json
import hashlib
import httpx
from httpcore import ReadTimeout as HttpcoreReadTimeout
from httpx import ReadTimeout as HttpxReadTimeout

from app.config import settings
from app.models.doubt import WolframStep
from app.utils.exceptions import APIException


class WolframService:
    """Service for Wolfram Alpha API integration"""
    
    def __init__(self):
        """Initialize Wolfram service"""
        self._client: Optional[wolframalpha.Client] = None
        self._redis_client: Optional[Redis] = None
        self._cache_enabled = True
        self._cache_ttl = 86400  # 24 hours
        
        # Patterns for detecting numerical/mathematical questions
        self.math_patterns = [
            r'\d+\s*[\+\-\*/\^]\s*\d+',  # Basic arithmetic
            r'solve|calculate|compute|evaluate|find\s+the\s+value',  # Calculation keywords
            r'equation|integral|derivative|limit|summation',  # Calculus operations
            r'=\s*\?|\?\s*=',  # Equation with unknown
            r'\d+\s*x\s*\d+',  # Multiplication notation
            r'sin|cos|tan|log|ln|exp|sqrt',  # Mathematical functions
            r'd/dx|∫|∑|∏|lim',  # Mathematical symbols
            r'matrix|determinant|eigenvalue',  # Linear algebra
            r'differentiate|integrate',  # Calculus verbs
            r'plot|graph|visualize|draw',  # Graph/plot keywords
            r'x\^2|x\^3|y\s*=',  # Equations that might need graphs
        ]
    
    def _get_client(self) -> Optional[wolframalpha.Client]:
        """Get or create Wolfram Alpha client"""
        if self._client is None:
            try:
                if not settings.wolfram_app_id or settings.wolfram_app_id.strip() == "":
                    print("Warning: WOLFRAM_APP_ID is not set")
                    return None
                self._client = wolframalpha.Client(settings.wolfram_app_id)
                print(f"Wolfram Alpha client initialized with AppID: {settings.wolfram_app_id[:10]}...")
            except Exception as e:
                print(f"Error initializing Wolfram Alpha client: {e}")
                return None
        return self._client
    
    async def _query_direct_api(self, query: str, retry_count: int = 0):
        """Fallback method to query Wolfram Alpha API directly, bypassing library Content-Type issue"""
        import httpx
        
        url = "https://api.wolframalpha.com/v2/query"
        params = {
            "input": query,
            "appid": settings.wolfram_app_id,
            "format": "plaintext"
        }
        
        # Configure timeouts properly
        # httpx.Timeout requires either a default or all four parameters
        connect_timeout = getattr(settings, 'wolfram_connect_timeout', 10)
        read_timeout = getattr(settings, 'wolfram_read_timeout', 60)
        # Set all timeout parameters explicitly
        timeout_config = httpx.Timeout(
            connect=connect_timeout,
            read=read_timeout,
            write=read_timeout,  # Same as read timeout
            pool=connect_timeout  # Same as connect timeout
        )
        
        try:
            async with httpx.AsyncClient(timeout=timeout_config, follow_redirects=True) as client:
                response = await client.get(url, params=params)
                
                if response.status_code == 200:
                    # Parse XML response manually
                    doc = xmltodict.parse(response.content)
                    query_result = doc.get('queryresult', {})
                    
                    # Convert dict response to object-like structure for compatibility
                    class DictWrapper:
                        def __init__(self, data):
                            self._data = data
                            
                        def __getattr__(self, name):
                            if name == 'pods':
                                pods_data = self._data.get('pod', [])
                                if not isinstance(pods_data, list):
                                    pods_data = [pods_data]
                                return [PodWrapper(p) for p in pods_data]
                            elif name == 'success':
                                return self._data.get('@success', 'false') == 'true'
                            elif name == 'error':
                                return self._data.get('@error', 'false') == 'true'
                            return getattr(self._data, name, None)
                    
                    class PodWrapper:
                        def __init__(self, data):
                            self._data = data
                            self.title = data.get('@title', '')
                            self.primary = data.get('@primary', 'false') == 'true'
                            
                        @property
                        def subpods(self):
                            subpods_data = self._data.get('subpod', [])
                            if not isinstance(subpods_data, list):
                                subpods_data = [subpods_data]
                            return [SubpodWrapper(s) for s in subpods_data]
                    
                    class SubpodWrapper:
                        def __init__(self, data):
                            self._data = data
                            self.plaintext = data.get('plaintext', '')
                            self.text = self.plaintext
                            self.title = data.get('@title', '')
                            
                        @property
                        def img(self):
                            img_data = self._data.get('img', {})
                            if not img_data:
                                return None
                            class ImgWrapper:
                                def __init__(self, data):
                                    self.src = data.get('@src', '')
                                    self.url = self.src
                            return ImgWrapper(img_data) if img_data else None
                    
                    return DictWrapper(query_result)
                else:
                    raise Exception(f"API returned status code {response.status_code}")
        except (httpx.ReadTimeout, httpx.ConnectTimeout, HttpcoreReadTimeout, HttpxReadTimeout) as timeout_error:
            # Retry on timeout if we haven't exceeded max retries
            max_retries = getattr(settings, 'wolfram_max_retries', 2)
            if retry_count < max_retries:
                wait_time = (retry_count + 1) * 2  # Exponential backoff: 2s, 4s
                print(f"Wolfram Alpha timeout, retrying ({retry_count + 1}/{max_retries}) after {wait_time}s...")
                await asyncio.sleep(wait_time)
                return await self._query_direct_api(query, retry_count + 1)
            else:
                raise timeout_error
        except Exception as e:
            # Retry on other errors if we haven't exceeded max retries
            max_retries = getattr(settings, 'wolfram_max_retries', 2)
            if retry_count < max_retries and "timeout" in str(e).lower():
                wait_time = (retry_count + 1) * 2
                print(f"Wolfram Alpha error, retrying ({retry_count + 1}/{max_retries}) after {wait_time}s...")
                await asyncio.sleep(wait_time)
                return await self._query_direct_api(query, retry_count + 1)
            else:
                raise
    
    def _get_redis_client(self) -> Optional[Redis]:
        """Get or create Redis client for caching"""
        if not self._cache_enabled:
            return None
        
        if self._redis_client is None:
            try:
                self._redis_client = Redis(
                    host=settings.redis_host,
                    port=settings.redis_port,
                    password=settings.redis_password if settings.redis_password else None,
                    decode_responses=True,
                    socket_connect_timeout=2
                )
                # Test connection
                self._redis_client.ping()
            except Exception as e:
                print(f"Redis connection failed: {e}")
                self._cache_enabled = False
                return None
        
        return self._redis_client
    
    def _get_cache_key(self, query: str) -> str:
        """Generate cache key for query"""
        # Create hash of query for cache key
        query_hash = hashlib.md5(query.lower().strip().encode()).hexdigest()
        return f"wolfram:{query_hash}"
    
    def _get_cached_result(self, query: str) -> Optional[Dict]:
        """Get cached result for query"""
        try:
            redis_client = self._get_redis_client()
            if redis_client is None:
                return None
            
            cache_key = self._get_cache_key(query)
            cached = redis_client.get(cache_key)
            
            if cached:
                return json.loads(cached)
            
            return None
        except Exception as e:
            print(f"Cache retrieval error: {e}")
            return None
    
    def _cache_result(self, query: str, result: Dict):
        """Cache result for query"""
        try:
            redis_client = self._get_redis_client()
            if redis_client is None:
                return
            
            cache_key = self._get_cache_key(query)
            redis_client.setex(
                cache_key,
                self._cache_ttl,
                json.dumps(result)
            )
        except Exception as e:
            print(f"Cache storage error: {e}")
    
    def is_numerical_question(self, text: str) -> bool:
        """
        Detect if the question is numerical/mathematical
        
        Args:
            text: Question text
            
        Returns:
            True if numerical, False otherwise
        """
        text_lower = text.lower()
        
        for pattern in self.math_patterns:
            if re.search(pattern, text_lower):
                return True
        
        return False
    
    async def solve_math_problem(
        self,
        query: str,
        include_steps: bool = True
    ) -> Optional[Dict]:
        """
        Solve a math problem using Wolfram Alpha
        
        Args:
            query: Mathematical query
            include_steps: Whether to include step-by-step solution
            
        Returns:
            Dictionary with solution, steps, and metadata, or None if failed
        """
        try:
            # Check cache first
            cached_result = self._get_cached_result(query)
            if cached_result:
                return cached_result
            
            # Get Wolfram client
            client = self._get_client()
            if not client:
                print("Warning: Wolfram Alpha client not initialized")
                return None
            
            # Query Wolfram Alpha using async method (since we're in async context)
            # Use direct API call first since library has Content-Type issues
            try:
                # Try direct API call first (more reliable, handles Content-Type issue)
                res = await self._query_direct_api(query)
            except (asyncio.TimeoutError, HttpcoreReadTimeout, HttpxReadTimeout, httpx.ReadTimeout, httpx.ConnectTimeout) as timeout_error:
                # Handle timeout errors specifically
                read_timeout = getattr(settings, 'wolfram_read_timeout', 60)
                error_details = f"Request timed out after {read_timeout} seconds. The Wolfram Alpha API may be slow or unavailable. Please try rephrasing your query or try again later."
                print(f"Wolfram Alpha timeout error: {error_details}")
                return {
                    "answer": None,
                    "error": error_details,
                    "steps": [],
                    "input_interpretation": None,
                    "plots": [],
                    "metadata": {
                        "error": str(timeout_error),
                        "error_type": "TimeoutError",
                        "timeout_seconds": read_timeout
                    }
                }
            except AssertionError as assert_error:
                # Handle Content-Type assertion errors from the library
                error_details = f"API response format error: {str(assert_error)}. This may indicate an invalid AppID or API issue."
                print(f"Wolfram Alpha assertion error: {error_details}")
                return {
                    "answer": None,
                    "error": error_details,
                    "steps": [],
                    "input_interpretation": None,
                    "plots": [],
                    "metadata": {"error": str(assert_error), "error_type": "AssertionError"}
                }
            except Exception as query_error:
                import traceback
                error_details = str(query_error) or f"{type(query_error).__name__}"
                error_type = type(query_error).__name__
                print(f"Wolfram Alpha query error ({error_type}): {error_details}")
                print(f"Traceback: {traceback.format_exc()}")
                
                # Return error information instead of None
                return {
                    "answer": None,
                    "error": f"Query failed: {error_details}",
                    "steps": [],
                    "input_interpretation": None,
                    "plots": [],
                    "metadata": {"error": error_details, "error_type": error_type}
                }
            
            # Parse response
            result = self._parse_wolfram_response(res, include_steps)
            
            if result:
                # Cache the result
                self._cache_result(query, result)
            
            return result
            
        except Exception as e:
            import traceback
            print(f"Wolfram Alpha error: {e}")
            print(f"Traceback: {traceback.format_exc()}")
            return None
    
    def _parse_wolfram_response(
        self,
        response,
        include_steps: bool = True
    ) -> Optional[Dict]:
        """
        Parse Wolfram Alpha response
        
        Args:
            response: Wolfram Alpha response object
            include_steps: Whether to include step-by-step solution
            
        Returns:
            Parsed result dictionary or None
        """
        try:
            # Check if response has success/error attributes
            if hasattr(response, 'success') and not response.success:
                error_msg = "Query failed"
                # Check if there's an actual error (error is a boolean)
                if hasattr(response, 'error') and response.error:
                    # Try to get error message from response data
                    if hasattr(response, '_data') and isinstance(response._data, dict):
                        error_data = response._data.get('error', {})
                        if isinstance(error_data, dict):
                            error_msg = error_data.get('msg', 'Query failed')
                        elif isinstance(error_data, str):
                            error_msg = error_data
                    elif hasattr(response, 'error_msg'):
                        error_msg = str(response.error_msg)
                    else:
                        error_msg = "Query failed - please try rephrasing your question"
                print(f"Wolfram Alpha query failed: {error_msg}")
                return {
                    "answer": None,
                    "error": error_msg,
                    "steps": [],
                    "input_interpretation": None,
                    "plots": [],
                    "metadata": {}
                }
            
            # Also check if error attribute is True (even if success is True)
            # Only treat as error if error is explicitly True (not False)
            if hasattr(response, 'error') and response.error is True:
                error_msg = "Query failed - please try rephrasing your question"
                if hasattr(response, '_data') and isinstance(response._data, dict):
                    error_data = response._data.get('error', {})
                    if isinstance(error_data, dict):
                        error_msg = error_data.get('msg', error_msg)
                    elif isinstance(error_data, str) and error_data:
                        error_msg = error_data
                print(f"Wolfram Alpha query error: {error_msg}")
                return {
                    "answer": None,
                    "error": error_msg,
                    "steps": [],
                    "input_interpretation": None,
                    "plots": [],
                    "metadata": {}
                }
            
            result = {
                "answer": None,
                "solution": None,  # Alias for answer
                "steps": [],
                "input_interpretation": None,
                "plots": [],
                "metadata": {}
            }
            
            # Track primary pod (has primary="true" attribute)
            primary_pod = None
            
            # First pass: Find primary pod and input interpretation
            for pod in response.pods:
                pod_title = pod.title.lower()
                
                # Check if this is the primary result pod
                if hasattr(pod, 'primary') and pod.primary:
                    primary_pod = pod
                
                # Input interpretation
                if "input" in pod_title or "interpretation" in pod_title:
                    result["input_interpretation"] = self._extract_pod_text(pod)
            
            # Extract answer from primary pod first (most reliable)
            if primary_pod:
                answer_text = self._extract_pod_text(primary_pod)
                if answer_text:
                    result["answer"] = answer_text
                    result["solution"] = answer_text  # Set alias
            
            # Second pass: Extract all other information
            for pod in response.pods:
                pod_title = pod.title.lower()
                
                # Skip if already processed as primary
                if pod == primary_pod:
                    continue
                
                # Result/Answer (if not already found from primary)
                if result["answer"] is None:
                    if any(keyword in pod_title for keyword in ["result", "solution", "answer", "value"]):
                        answer_text = self._extract_pod_text(pod)
                        if answer_text:
                            result["answer"] = answer_text
                            result["solution"] = answer_text
                
                # Step-by-step solution
                if include_steps:
                    if any(keyword in pod_title for keyword in ["step", "solution", "possible intermediate", "derivative", "integral", "limit"]):
                        steps_text = self._extract_pod_text(pod)
                        if steps_text:
                            result["steps"].append({
                                "title": pod.title,
                                "content": steps_text
                            })
                
                # Extract ALL images/visualizations from ALL pods (comprehensive extraction)
                # Wolfram Alpha returns images in various pod types: plots, graphs, 3D graphics, tables, etc.
                for subpod in pod.subpods:
                    if hasattr(subpod, 'img') and subpod.img:
                        img_url = None
                        img_width = None
                        img_height = None
                        img_alt = None
                        
                        # Extract image URL from various possible attributes
                        if hasattr(subpod.img, 'src'):
                            img_url = subpod.img.src
                        elif hasattr(subpod.img, 'url'):
                            img_url = subpod.img.url
                        elif isinstance(subpod.img, dict):
                            img_url = subpod.img.get('src') or subpod.img.get('url')
                        
                        # Extract image dimensions if available
                        if hasattr(subpod.img, 'width'):
                            img_width = subpod.img.width
                        elif isinstance(subpod.img, dict):
                            img_width = subpod.img.get('width')
                        
                        if hasattr(subpod.img, 'height'):
                            img_height = subpod.img.height
                        elif isinstance(subpod.img, dict):
                            img_height = subpod.img.get('height')
                        
                        # Extract alt text/description
                        if hasattr(subpod, 'plaintext') and subpod.plaintext:
                            img_alt = subpod.plaintext.strip()
                        elif hasattr(subpod, 'title') and subpod.title:
                            img_alt = subpod.title.strip()
                        
                        if img_url:
                            # Determine visualization type
                            viz_type = "plot"
                            if "3d" in pod_title or "three-dimensional" in pod_title:
                                viz_type = "3d_plot"
                            elif "contour" in pod_title:
                                viz_type = "contour_plot"
                            elif "surface" in pod_title:
                                viz_type = "surface_plot"
                            elif "table" in pod_title or "data" in pod_title:
                                viz_type = "table"
                            elif "graph" in pod_title:
                                viz_type = "graph"
                            elif "geometry" in pod_title or "geometric" in pod_title:
                                viz_type = "geometry"
                            elif "vector" in pod_title:
                                viz_type = "vector_field"
                            elif "polar" in pod_title:
                                viz_type = "polar_plot"
                            
                            # Add to plots if not already added (avoid duplicates by URL)
                            existing_urls = [p.get("url") for p in result["plots"] if p.get("url")]
                            if img_url not in existing_urls:
                                result["plots"].append({
                                    "title": pod.title if hasattr(pod, 'title') else f"Visualization {len(result['plots']) + 1}",
                                    "url": img_url,
                                    "description": img_alt or self._extract_pod_text(pod) or (pod.title if hasattr(pod, 'title') else ""),
                                    "type": viz_type,
                                    "width": img_width,
                                    "height": img_height
                                })
            
            # Third pass: Extract ALL remaining images from ALL pods (comprehensive - catch anything we missed)
            # This ensures we don't miss any visualizations
            for pod_idx, pod in enumerate(response.pods):
                if not hasattr(pod, 'subpods'):
                    continue
                    
                pod_title_lower = (pod.title.lower() if hasattr(pod, 'title') else "")
                
                for subpod in pod.subpods:
                    if hasattr(subpod, 'img') and subpod.img:
                        img_url = None
                        
                        if hasattr(subpod.img, 'src'):
                            img_url = subpod.img.src
                        elif hasattr(subpod.img, 'url'):
                            img_url = subpod.img.url
                        elif isinstance(subpod.img, dict):
                            img_url = subpod.img.get('src') or subpod.img.get('url')
                        
                        if img_url:
                            # Check if already added (avoid duplicates)
                            existing_urls = [p.get("url") for p in result["plots"] if p.get("url")]
                            if img_url not in existing_urls:
                                # Determine type
                                viz_type = "visualization"
                                if "3d" in pod_title_lower or "three-dimensional" in pod_title_lower:
                                    viz_type = "3d_plot"
                                elif "contour" in pod_title_lower:
                                    viz_type = "contour_plot"
                                elif "surface" in pod_title_lower:
                                    viz_type = "surface_plot"
                                elif "table" in pod_title_lower:
                                    viz_type = "table"
                                elif "plot" in pod_title_lower:
                                    viz_type = "plot"
                                
                                result["plots"].append({
                                    "title": pod.title if hasattr(pod, 'title') else f"Visualization {len(result['plots']) + 1}",
                                    "url": img_url,
                                    "description": self._extract_pod_text(pod) or (pod.title if hasattr(pod, 'title') else ""),
                                    "type": viz_type
                                })
            
            # If still no answer, try to get any text from first pod
            if result["answer"] is None and len(response.pods) > 0:
                first_pod_text = self._extract_pod_text(response.pods[0])
                if first_pod_text:
                    result["answer"] = first_pod_text
                    result["solution"] = first_pod_text
            
            # Add metadata
            result["metadata"] = {
                "numpods": len(response.pods) if hasattr(response, 'pods') else 0,
                "success": getattr(response, 'success', True),
                "error": getattr(response, 'error', False),
            }
            
            # Return result even if no answer (might have steps or plots)
            return result
            
        except Exception as e:
            import traceback
            print(f"Response parsing error: {e}")
            print(f"Traceback: {traceback.format_exc()}")
            return {
                "answer": None,
                "error": f"Parsing error: {str(e)}",
                "steps": [],
                "input_interpretation": None,
                "plots": [],
                "metadata": {}
            }
    
    def _extract_pod_text(self, pod) -> Optional[str]:
        """Extract text from a Wolfram pod"""
        try:
            texts = []
            for subpod in pod.subpods:
                # Try plaintext first (most common)
                if hasattr(subpod, 'plaintext') and subpod.plaintext:
                    texts.append(subpod.plaintext.strip())
                # Fallback to other text attributes
                elif hasattr(subpod, 'text') and subpod.text:
                    texts.append(subpod.text.strip())
                # Try to get from title if available
                elif hasattr(subpod, 'title') and subpod.title:
                    texts.append(subpod.title.strip())
            
            # Join all texts, filtering out empty strings
            result = "\n".join([t for t in texts if t])
            return result if result else None
        except Exception as e:
            print(f"Error extracting pod text: {e}")
            return None
    
    def format_steps_for_response(self, wolfram_result: Dict) -> List[WolframStep]:
        """
        Format Wolfram steps for DoubtResponse
        
        Args:
            wolfram_result: Parsed Wolfram result
            
        Returns:
            List of WolframStep objects
        """
        steps = []
        
        # Add input interpretation as first step
        if wolfram_result.get("input_interpretation"):
            steps.append(WolframStep(
                step_number=1,
                description="Problem Understanding",
                expression=wolfram_result["input_interpretation"],
                explanation="This is how Wolfram Alpha interpreted your question."
            ))
        
        # Add solution steps
        step_offset = len(steps)
        for idx, step_data in enumerate(wolfram_result.get("steps", [])):
            steps.append(WolframStep(
                step_number=step_offset + idx + 1,
                description=step_data.get("title", f"Step {idx + 1}"),
                expression=step_data.get("content", ""),
                explanation=None
            ))
        
        # Add final answer
        if wolfram_result.get("answer"):
            steps.append(WolframStep(
                step_number=len(steps) + 1,
                description="Final Answer",
                expression=wolfram_result["answer"],
                explanation="This is the final result."
            ))
        
        return steps
    
    async def verify_numerical_answer(
        self,
        question: str,
        student_answer: str,
        tolerance: float = 0.01
    ) -> Dict:
        """
        Verify a student's numerical answer
        
        Args:
            question: The math question
            student_answer: Student's answer
            tolerance: Acceptable error tolerance (default: 0.01)
            
        Returns:
            Dictionary with verification result
        """
        try:
            # Get Wolfram solution
            wolfram_result = await self.solve_math_problem(question, include_steps=False)
            
            if not wolfram_result or not wolfram_result.get("answer"):
                return {
                    "verified": False,
                    "correct": None,
                    "expected_answer": None,
                    "message": "Could not verify answer with Wolfram Alpha"
                }
            
            expected_answer = wolfram_result["answer"]
            
            # Try to extract numerical values for comparison
            try:
                # Extract numbers from both answers
                student_nums = re.findall(r'-?\d+\.?\d*', student_answer)
                expected_nums = re.findall(r'-?\d+\.?\d*', expected_answer)
                
                if student_nums and expected_nums:
                    student_val = float(student_nums[0])
                    expected_val = float(expected_nums[0])
                    
                    # Check if within tolerance
                    is_correct = abs(student_val - expected_val) <= tolerance
                    
                    return {
                        "verified": True,
                        "correct": is_correct,
                        "expected_answer": expected_answer,
                        "student_value": student_val,
                        "expected_value": expected_val,
                        "message": "Answer verified" if is_correct else "Answer is incorrect"
                    }
            except (ValueError, IndexError):
                pass
            
            # Fallback to string comparison
            is_correct = student_answer.strip().lower() == expected_answer.strip().lower()
            
            return {
                "verified": True,
                "correct": is_correct,
                "expected_answer": expected_answer,
                "message": "Answer verified" if is_correct else "Answer is incorrect"
            }
            
        except Exception as e:
            return {
                "verified": False,
                "correct": None,
                "expected_answer": None,
                "message": f"Verification failed: {str(e)}"
            }
    
    async def verify_answer(
        self,
        question: str,
        student_answer: str,
        expected_answer: Optional[str] = None,
        tolerance: float = 0.01
    ) -> Optional[Dict]:
        """
        Verify a student's answer against expected answer or Wolfram solution
        
        Args:
            question: The math question
            student_answer: Student's submitted answer
            expected_answer: Optional expected answer for comparison
            tolerance: Acceptable error tolerance (default: 0.01 = 1%)
            
        Returns:
            Dictionary with is_correct, feedback, and explanation, or None if verification fails
        """
        try:
            # If expected answer provided, compare directly
            if expected_answer:
                # Try numerical comparison
                try:
                    student_nums = re.findall(r'-?\d+\.?\d*', student_answer)
                    expected_nums = re.findall(r'-?\d+\.?\d*', expected_answer)
                    
                    if student_nums and expected_nums:
                        student_val = float(student_nums[0])
                        expected_val = float(expected_nums[0])
                        
                        # Check if within tolerance (percentage-based)
                        if expected_val != 0:
                            error_percent = abs((student_val - expected_val) / expected_val)
                            is_correct = error_percent <= tolerance
                        else:
                            is_correct = abs(student_val - expected_val) <= tolerance
                        
                        if is_correct:
                            return {
                                "is_correct": True,
                                "feedback": "Great job! Your answer is correct.",
                                "explanation": f"Your answer ({student_val}) matches the expected answer ({expected_val})."
                            }
                        else:
                            return {
                                "is_correct": False,
                                "feedback": "Your answer is close but not quite right. Check your calculations.",
                                "explanation": f"Your answer ({student_val}) differs from the expected answer ({expected_val})."
                            }
                except (ValueError, IndexError):
                    # Fallback to string comparison
                    is_correct = student_answer.strip().lower() == expected_answer.strip().lower()
                    
                    if is_correct:
                        return {
                            "is_correct": True,
                            "feedback": "Correct! Well done.",
                            "explanation": "Your answer matches the expected answer."
                        }
                    else:
                        return {
                            "is_correct": False,
                            "feedback": "Your answer doesn't match the expected answer. Review your work.",
                            "explanation": f"Expected: {expected_answer}, Got: {student_answer}"
                        }
            
            # Otherwise, use Wolfram to verify
            verification = await self.verify_numerical_answer(question, student_answer, tolerance)
            
            if verification.get("verified"):
                is_correct = verification.get("correct", False)
                
                if is_correct:
                    return {
                        "is_correct": True,
                        "feedback": "Excellent! Your answer is verified as correct by Wolfram Alpha.",
                        "explanation": f"Your answer matches the computed solution: {verification.get('expected_answer')}"
                    }
                else:
                    return {
                        "is_correct": False,
                        "feedback": "Your answer doesn't match the computed solution. Try again.",
                        "explanation": f"Expected: {verification.get('expected_answer')}, Got: {student_answer}"
                    }
            
            return None
            
        except Exception as e:
            print(f"Answer verification error: {e}")
            return None


# Global instance
wolfram_service = WolframService()
