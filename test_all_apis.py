#!/usr/bin/env python3
"""
Comprehensive API Testing Script for Class 12 Learning Platform
Tests all available endpoints systematically
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any

BASE_URL = "http://127.0.0.1:8000"

class APITester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.results = []
        
    def test_endpoint(self, method: str, endpoint: str, data: Dict = None, params: Dict = None, description: str = ""):
        """Test a single endpoint and record results"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url, params=params)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data, params=params)
            elif method.upper() == "PUT":
                response = self.session.put(url, json=data, params=params)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, params=params)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            result = {
                "endpoint": endpoint,
                "method": method.upper(),
                "status_code": response.status_code,
                "success": 200 <= response.status_code < 300,
                "description": description,
                "response_time": response.elapsed.total_seconds(),
                "timestamp": datetime.now().isoformat()
            }
            
            # Try to parse JSON response
            try:
                result["response"] = response.json()
            except:
                result["response"] = response.text[:500] if response.text else "No response body"
            
            self.results.append(result)
            
            # Print result
            status_icon = "✅" if result["success"] else "❌"
            print(f"{status_icon} {method.upper()} {endpoint} - {response.status_code} ({response.elapsed.total_seconds():.3f}s)")
            if description:
                print(f"   📝 {description}")
            
            return result
            
        except Exception as e:
            result = {
                "endpoint": endpoint,
                "method": method.upper(),
                "status_code": 0,
                "success": False,
                "description": description,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            self.results.append(result)
            print(f"❌ {method.upper()} {endpoint} - ERROR: {str(e)}")
            return result
    
    def run_basic_tests(self):
        """Test basic endpoints"""
        print("\n🔍 Testing Basic Endpoints...")
        
        self.test_endpoint("GET", "/", description="Root endpoint")
        self.test_endpoint("GET", "/ready", description="Readiness probe")
        self.test_endpoint("GET", "/info", description="API info")
        self.test_endpoint("GET", "/api/health", description="Health check")
        self.test_endpoint("GET", "/api/health/config", description="Health config")
    
    def run_rag_tests(self):
        """Test RAG endpoints"""
        print("\n🔍 Testing RAG Endpoints...")
        
        # Test RAG query
        rag_query = {
            "query": "What is photosynthesis?",
            "user_id": "test_user_123",
            "subject": "biology",
            "grade": 12
        }
        
        self.test_endpoint("POST", "/api/rag/query", data=rag_query, description="RAG query")
        self.test_endpoint("GET", "/api/rag/initialize", description="RAG initialize")
        self.test_endpoint("POST", "/api/rag/evaluate", data={"query": "test", "response": "test"}, description="RAG evaluate")
    
    def run_ai_tutoring_tests(self):
        """Test AI Tutoring endpoints"""
        print("\n🔍 Testing AI Tutoring Endpoints...")
        
        # Test sessions
        self.test_endpoint("GET", "/api/ai-tutoring/sessions", params={"user_id": "test_user_123"}, description="Get AI tutoring sessions")
        
        # Test session creation
        session_data = {
            "user_id": "test_user_123",
            "subject": "mathematics",
            "topic": "calculus",
            "grade": 12
        }
        self.test_endpoint("POST", "/api/ai-tutoring/sessions", data=session_data, description="Create AI tutoring session")
        
        # Test other AI tutoring endpoints
        self.test_endpoint("GET", "/api/ai-tutoring/health", description="AI tutoring health")
        self.test_endpoint("POST", "/api/ai-tutoring/answer", data={"question": "What is derivative?", "user_id": "test_user_123"}, description="AI tutoring answer")
        
        # Test lesson plans
        self.test_endpoint("GET", "/api/ai-tutoring/lesson-plans", params={"subject": "mathematics"}, description="Get lesson plans")
        lesson_plan_data = {
            "subject": "mathematics",
            "topic": "derivatives",
            "grade": 12,
            "duration": 60
        }
        self.test_endpoint("POST", "/api/ai-tutoring/lesson-plans/generate", data=lesson_plan_data, description="Generate lesson plan")
    
    def run_doubt_tests(self):
        """Test Doubt Solver endpoints"""
        print("\n🔍 Testing Doubt Solver Endpoints...")
        
        # Test text doubt
        text_doubt = {
            "question": "Explain Newton's laws of motion",
            "user_id": "test_user_123",
            "subject": "physics"
        }
        self.test_endpoint("POST", "/api/doubt/text", data=text_doubt, description="Text doubt solver")
        
        # Test Wolfram Alpha
        self.test_endpoint("POST", "/api/doubt/wolfram/chat", params={"query": "solve x^2 + 5x + 6 = 0"}, description="Wolfram Alpha chat")
        
        # Test doubt history
        self.test_endpoint("GET", "/api/doubt/history", params={"user_id": "test_user_123"}, description="Doubt history")
    
    def run_quiz_tests(self):
        """Test Quiz endpoints"""
        print("\n🔍 Testing Quiz Endpoints...")
        
        # Start quiz
        quiz_start = {
            "user_id": "test_user_123",
            "subject": "mathematics",
            "topic": "algebra",
            "difficulty": "medium"
        }
        self.test_endpoint("POST", "/api/quiz/start", data=quiz_start, description="Start quiz")
        
        # Answer quiz (assuming session_id from previous call)
        quiz_answer = {
            "session_id": "test_session_123",
            "question_id": "q1",
            "answer": "A",
            "user_id": "test_user_123"
        }
        self.test_endpoint("POST", "/api/quiz/answer", data=quiz_answer, description="Answer quiz question")
    
    def run_exam_tests(self):
        """Test Exam endpoints"""
        print("\n🔍 Testing Exam Endpoints...")
        
        self.test_endpoint("GET", "/api/exam/sets", description="Get exam sets")
        
        # Start exam
        exam_start = {
            "user_id": "test_user_123",
            "exam_set_id": "test_exam_set",
            "subject": "physics"
        }
        self.test_endpoint("POST", "/api/exam/start", data=exam_start, description="Start exam")
    
    def run_progress_tests(self):
        """Test Progress endpoints"""
        print("\n🔍 Testing Progress Endpoints...")
        
        self.test_endpoint("GET", "/api/progress", params={"user_id": "test_user_123"}, description="Get progress")
        self.test_endpoint("GET", "/api/progress/test_user_123", description="Get user progress")
        self.test_endpoint("GET", "/api/progress/test_user_123/summary", description="Get progress summary")
        self.test_endpoint("GET", "/api/progress/test_user_123/achievements", description="Get achievements")
    
    def run_admin_tests(self):
        """Test Admin endpoints"""
        print("\n🔍 Testing Admin Endpoints...")
        
        self.test_endpoint("GET", "/api/admin/dashboard", description="Admin dashboard")
        self.test_endpoint("GET", "/api/admin/users", description="Get all users")
        self.test_endpoint("GET", "/api/admin/students", description="Get all students")
        self.test_endpoint("GET", "/api/admin/teachers", description="Get all teachers")
        self.test_endpoint("GET", "/api/admin/schools", description="Get all schools")
    
    def run_analytics_tests(self):
        """Test Analytics endpoints"""
        print("\n🔍 Testing Analytics Endpoints...")
        
        self.test_endpoint("GET", "/api/analytics/dashboard", description="Analytics dashboard")
        self.test_endpoint("GET", "/api/analytics/trends", description="Analytics trends")
        self.test_endpoint("GET", "/api/analytics/student/test_user_123", description="Student analytics")
        
        # Test event tracking
        event_data = {
            "user_id": "test_user_123",
            "event_type": "quiz_completed",
            "metadata": {"score": 85, "subject": "mathematics"}
        }
        self.test_endpoint("POST", "/api/analytics/event", data=event_data, description="Track analytics event")
    
    def run_homework_tests(self):
        """Test Homework endpoints"""
        print("\n🔍 Testing Homework Endpoints...")
        
        # Start homework session
        homework_start = {
            "user_id": "test_user_123",
            "subject": "mathematics",
            "topic": "trigonometry"
        }
        self.test_endpoint("POST", "/api/homework/start", data=homework_start, description="Start homework session")
        
        self.test_endpoint("GET", "/api/homework/sessions", params={"user_id": "test_user_123"}, description="Get homework sessions")
    
    def run_microplan_tests(self):
        """Test Microplan endpoints"""
        print("\n🔍 Testing Microplan Endpoints...")
        
        # Generate microplan
        microplan_data = {
            "user_id": "test_user_123",
            "subject": "chemistry",
            "available_time": 60,
            "difficulty_preference": "medium"
        }
        self.test_endpoint("POST", "/api/microplan/generate", data=microplan_data, description="Generate microplan")
        
        self.test_endpoint("GET", "/api/microplan/today", params={"user_id": "test_user_123"}, description="Get today's microplan")
    
    def run_memory_tests(self):
        """Test Memory Intelligence endpoints"""
        print("\n🔍 Testing Memory Intelligence Endpoints...")
        
        # Store session
        session_data = {
            "user_id": "test_user_123",
            "session_type": "quiz",
            "content": "Mathematics quiz on derivatives",
            "performance_score": 85,
            "topics": ["calculus", "derivatives"]
        }
        self.test_endpoint("POST", "/api/memory/store-session", data=session_data, description="Store memory session")
        
        self.test_endpoint("GET", "/api/memory/learning-history/test_user_123", description="Get learning history")
        self.test_endpoint("GET", "/api/memory/learning-patterns/test_user_123", description="Get learning patterns")
        self.test_endpoint("GET", "/api/memory/stats", description="Get memory stats")
    
    def run_notification_tests(self):
        """Test Notification endpoints"""
        print("\n🔍 Testing Notification Endpoints...")
        
        self.test_endpoint("GET", "/api/notifications", params={"user_id": "test_user_123"}, description="Get notifications")
        self.test_endpoint("GET", "/api/notifications/unread-count", params={"user_id": "test_user_123"}, description="Get unread count")
        self.test_endpoint("GET", "/api/notifications/test_user_123", description="Get user notifications")
    
    def run_teacher_tests(self):
        """Test Teacher endpoints"""
        print("\n🔍 Testing Teacher Endpoints...")
        
        self.test_endpoint("GET", "/api/teacher/dashboard", params={"teacher_id": "test_teacher_123"}, description="Teacher dashboard")
        self.test_endpoint("GET", "/api/teacher/students", params={"teacher_id": "test_teacher_123"}, description="Get teacher students")
        self.test_endpoint("GET", "/api/teacher/quizzes", params={"teacher_id": "test_teacher_123"}, description="Get teacher quizzes")
    
    def run_translation_tests(self):
        """Test Translation endpoints"""
        print("\n🔍 Testing Translation Endpoints...")
        
        self.test_endpoint("GET", "/api/translation/languages", description="Get supported languages")
        
        # Test translation
        translation_data = {
            "text": "Hello, how are you?",
            "target_language": "es",
            "source_language": "en"
        }
        self.test_endpoint("POST", "/api/translation/translate", data=translation_data, description="Translate text")
        
        # Test language detection
        detect_data = {"text": "Bonjour, comment allez-vous?"}
        self.test_endpoint("POST", "/api/translation/detect", data=detect_data, description="Detect language")
    
    def run_wellbeing_tests(self):
        """Test Wellbeing endpoints"""
        print("\n🔍 Testing Wellbeing Endpoints...")
        
        # Start focus session
        focus_data = {
            "user_id": "test_user_123",
            "duration": 25,
            "activity": "study"
        }
        self.test_endpoint("POST", "/api/wellbeing/focus/start", data=focus_data, description="Start focus session")
        
        self.test_endpoint("GET", "/api/wellbeing/motivation/test_user_123", description="Get motivation content")
        self.test_endpoint("GET", "/api/wellbeing/distraction-guard/test_user_123", description="Get distraction guard")
    
    def run_videos_tests(self):
        """Test Videos endpoints"""
        print("\n🔍 Testing Videos Endpoints...")
        
        self.test_endpoint("GET", "/api/videos/subject/mathematics", description="Get videos by subject")
        
        # Search YouTube videos
        search_params = {"query": "calculus tutorial", "max_results": 5}
        self.test_endpoint("GET", "/api/videos/search/youtube", params=search_params, description="Search YouTube videos")
    
    def run_hots_tests(self):
        """Test HOTS (Higher Order Thinking Skills) endpoints"""
        print("\n🔍 Testing HOTS Endpoints...")
        
        # Generate HOTS question
        hots_data = {
            "subject": "physics",
            "topic": "mechanics",
            "difficulty": "hard",
            "user_id": "test_user_123"
        }
        self.test_endpoint("POST", "/api/hots/generate", data=hots_data, description="Generate HOTS question")
        
        self.test_endpoint("GET", "/api/hots/performance/test_user_123", description="Get HOTS performance")
    
    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting Comprehensive API Testing...")
        print(f"📍 Base URL: {self.base_url}")
        print(f"⏰ Started at: {datetime.now().isoformat()}")
        
        start_time = time.time()
        
        # Run all test categories
        self.run_basic_tests()
        self.run_rag_tests()
        self.run_ai_tutoring_tests()
        self.run_doubt_tests()
        self.run_quiz_tests()
        self.run_exam_tests()
        self.run_progress_tests()
        self.run_admin_tests()
        self.run_analytics_tests()
        self.run_homework_tests()
        self.run_microplan_tests()
        self.run_memory_tests()
        self.run_notification_tests()
        self.run_teacher_tests()
        self.run_translation_tests()
        self.run_wellbeing_tests()
        self.run_videos_tests()
        self.run_hots_tests()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Generate summary
        self.generate_summary(total_time)
    
    def generate_summary(self, total_time: float):
        """Generate test summary"""
        total_tests = len(self.results)
        successful_tests = len([r for r in self.results if r["success"]])
        failed_tests = total_tests - successful_tests
        
        print(f"\n📊 Test Summary")
        print(f"=" * 50)
        print(f"Total Tests: {total_tests}")
        print(f"✅ Successful: {successful_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📈 Success Rate: {(successful_tests/total_tests)*100:.1f}%")
        print(f"⏱️  Total Time: {total_time:.2f} seconds")
        print(f"⚡ Average Response Time: {sum(r.get('response_time', 0) for r in self.results)/total_tests:.3f}s")
        
        # Show failed tests
        if failed_tests > 0:
            print(f"\n❌ Failed Tests:")
            for result in self.results:
                if not result["success"]:
                    print(f"   • {result['method']} {result['endpoint']} - {result.get('status_code', 'ERROR')}")
                    if 'error' in result:
                        print(f"     Error: {result['error']}")
        
        # Save detailed results to file
        with open('api_test_results.json', 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n💾 Detailed results saved to: api_test_results.json")

if __name__ == "__main__":
    tester = APITester(BASE_URL)
    tester.run_all_tests()