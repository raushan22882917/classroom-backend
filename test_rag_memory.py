#!/usr/bin/env python3
"""
Focused API Testing Script for RAG and Memory Intelligence Endpoints
Tests only RAG and Memory Intelligence services
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any

BASE_URL = "http://127.0.0.1:8000"

class RAGMemoryTester:
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
            
            # Print response preview for successful requests
            if result["success"] and isinstance(result["response"], dict):
                if "message" in result["response"]:
                    print(f"   💬 {result['response']['message']}")
                elif "success" in result["response"]:
                    print(f"   ✨ Success: {result['response']['success']}")
            
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
    
    def run_rag_tests(self):
        """Test RAG endpoints comprehensively"""
        print("\n🔍 Testing RAG Endpoints...")
        
        # Test basic RAG query
        rag_query = {
            "query": "What is photosynthesis and how does it work?",
            "user_id": "test_user_123",
            "subject": "biology",
            "grade": 12
        }
        
        self.test_endpoint("POST", "/api/rag/query", data=rag_query, description="Basic RAG query - photosynthesis")
        
        # Test RAG query with different subjects
        math_query = {
            "query": "Explain the concept of derivatives in calculus",
            "user_id": "test_user_123",
            "subject": "mathematics",
            "grade": 12
        }
        
        self.test_endpoint("POST", "/api/rag/query", data=math_query, description="RAG query - mathematics derivatives")
        
        # Test physics query
        physics_query = {
            "query": "What are Newton's laws of motion?",
            "user_id": "test_user_123",
            "subject": "physics",
            "grade": 12
        }
        
        self.test_endpoint("POST", "/api/rag/query", data=physics_query, description="RAG query - physics Newton's laws")
        
        # Test chemistry query
        chemistry_query = {
            "query": "Explain the periodic table and atomic structure",
            "user_id": "test_user_123",
            "subject": "chemistry",
            "grade": 12
        }
        
        self.test_endpoint("POST", "/api/rag/query", data=chemistry_query, description="RAG query - chemistry periodic table")
        
        # Test direct Gemini query (fallback mode)
        direct_query = {
            "query": "What is the difference between mitosis and meiosis?",
            "user_id": "test_user_123",
            "subject": "biology"
        }
        
        self.test_endpoint("POST", "/api/rag/query-direct", data=direct_query, description="Direct Gemini query - mitosis vs meiosis")
        
        # Test RAG initialization
        self.test_endpoint("POST", "/api/rag/initialize", description="Initialize RAG services")
        
        # Test answer evaluation
        evaluation_data = {
            "question": "What is photosynthesis?",
            "user_answer": "Photosynthesis is the process by which plants make food using sunlight, water, and carbon dioxide.",
            "reference_content": "Photosynthesis is a biological process where plants convert light energy into chemical energy.",
            "subject": "biology"
        }
        
        self.test_endpoint("POST", "/api/rag/evaluate", data=evaluation_data, description="Evaluate student answer")
        
        # Test complex query
        complex_query = {
            "query": "How do enzymes work as biological catalysts and what factors affect their activity?",
            "user_id": "test_user_123",
            "subject": "biology",
            "grade": 12
        }
        
        self.test_endpoint("POST", "/api/rag/query", data=complex_query, description="Complex RAG query - enzymes")
    
    def run_memory_tests(self):
        """Test Memory Intelligence endpoints comprehensively"""
        print("\n🧠 Testing Memory Intelligence Endpoints...")
        
        # Test storing learning session
        session_data = {
            "session_id": "test_session_001",
            "subject": "mathematics",
            "topic": "calculus_derivatives",
            "difficulty_level": 3,
            "learning_objectives": ["understand derivatives", "apply chain rule"],
            "performance_metrics": {
                "accuracy": 0.85,
                "completion_time": 1800,
                "attempts": 3
            },
            "duration": 1800,
            "completion_rate": 0.9
        }
        
        self.test_endpoint("POST", "/api/memory/store-session", 
                          params={"user_id": "test_user_123"}, 
                          data=session_data, 
                          description="Store learning session in memory")
        
        # Test retrieving learning history
        self.test_endpoint("GET", "/api/memory/learning-history/test_user_123", 
                          params={"subject": "mathematics", "days_back": 30, "limit": 10},
                          description="Get learning history")
        
        # Test analyzing learning patterns
        self.test_endpoint("GET", "/api/memory/learning-patterns/test_user_123", 
                          description="Analyze learning patterns")
        
        # Test memory statistics
        self.test_endpoint("GET", "/api/memory/stats", 
                          description="Get memory statistics")
        
        # Test knowledge graph - create concept
        self.test_endpoint("POST", "/api/knowledge-graph/create-concept",
                          params={
                              "name": "derivatives",
                              "concept_type": "mathematical_concept",
                              "difficulty_level": 3
                          },
                          data={"description": "Rate of change of a function"},
                          description="Create concept in knowledge graph")
        
        # Test creating relationship
        self.test_endpoint("POST", "/api/knowledge-graph/create-relationship",
                          params={
                              "source_concept": "derivatives",
                              "target_concept": "calculus",
                              "relationship_type": "part_of",
                              "strength": 0.9
                          },
                          data={"context": "derivatives are part of calculus"},
                          description="Create concept relationship")
        
        # Test finding learning path
        self.test_endpoint("GET", "/api/knowledge-graph/learning-path/test_user_123",
                          params={
                              "target_concept": "integration",
                              "current_knowledge": ["algebra", "functions"]
                          },
                          description="Find learning path")
        
        # Test getting recommendations
        self.test_endpoint("GET", "/api/knowledge-graph/recommendations/test_user_123",
                          params={"limit": 5},
                          description="Get learning recommendations")
        
        # Test updating progress
        progress_data = {
            "performance_score": 0.85,
            "time_spent": 1200,
            "mastery_level": 0.7,
            "attempts": 2
        }
        
        self.test_endpoint("POST", "/api/knowledge-graph/update-progress",
                          params={
                              "user_id": "test_user_123",
                              "concept_name": "derivatives"
                          },
                          data=progress_data,
                          description="Update user progress")
        
        # Test user learning stats
        self.test_endpoint("GET", "/api/knowledge-graph/user-stats/test_user_123",
                          description="Get user learning statistics")
        
        # Test concept relationships
        self.test_endpoint("GET", "/api/knowledge-graph/concept-relationships/derivatives",
                          description="Get concept relationships")
        
        # Test knowledge gaps analysis
        self.test_endpoint("GET", "/api/knowledge-graph/knowledge-gaps/test_user_123",
                          description="Analyze knowledge gaps")
        
        # Test graph statistics
        self.test_endpoint("GET", "/api/knowledge-graph/stats",
                          description="Get knowledge graph statistics")
    
    def run_context_memory_tests(self):
        """Test context memory endpoints"""
        print("\n💭 Testing Context Memory Endpoints...")
        
        # Test remembering context
        context_data = {
            "type": "learning",
            "content": {
                "activity": "quiz_completion",
                "subject": "mathematics",
                "topic": "derivatives",
                "score": 85,
                "performance_data": {
                    "accuracy": 0.85,
                    "time_taken": 600,
                    "difficulty": "medium"
                }
            },
            "subject": "mathematics",
            "topic": "derivatives",
            "importance": 0.8,
            "tags": ["quiz", "mathematics", "derivatives"],
            "source": "quiz_interface",
            "session_id": "session_001"
        }
        
        self.test_endpoint("POST", "/api/context/remember",
                          params={"user_id": "test_user_123"},
                          data=context_data,
                          description="Remember learning context")
        
        # Test recalling context
        self.test_endpoint("GET", "/api/context/recall/test_user_123",
                          params={
                              "context_type": "learning",
                              "subject": "mathematics",
                              "limit": 10,
                              "days_back": 7
                          },
                          description="Recall learning contexts")
        
        # Test smart suggestions
        current_context = {
            "current_subject": "mathematics",
            "current_topic": "integration",
            "time_available": 30,
            "difficulty_preference": "medium"
        }
        
        self.test_endpoint("POST", "/api/context/smart-suggestions/test_user_123",
                          params={"suggestion_type": "next_action"},
                          data=current_context,
                          description="Get smart suggestions")
        
        # Test bulk remember contexts
        bulk_contexts = {
            "contexts": [
                {
                    "type": "interaction",
                    "content": {"component": "calculator", "action": "used"},
                    "subject": "mathematics",
                    "importance": 0.3,
                    "tags": ["tool_usage"],
                    "session_id": "session_001"
                },
                {
                    "type": "preference",
                    "content": {"learning_style": "visual", "pace": "moderate"},
                    "importance": 0.7,
                    "tags": ["user_preference"],
                    "session_id": "session_001"
                }
            ]
        }
        
        self.test_endpoint("POST", "/api/context/bulk-remember",
                          params={"user_id": "test_user_123"},
                          data=bulk_contexts,
                          description="Bulk remember contexts")
        
        # Test user timeline
        self.test_endpoint("GET", "/api/context/user-timeline/test_user_123",
                          params={
                              "days_back": 7,
                              "include_learning": True,
                              "include_interactions": True
                          },
                          description="Get user timeline")
    
    def run_interactive_learning_tests(self):
        """Test interactive learning endpoints"""
        print("\n🎮 Testing Interactive Learning Endpoints...")
        
        # Test creating interactive session
        session_data = {
            "components": ["adaptive_quiz", "concept_mapper", "progress_tracker"],
            "preferences": {
                "difficulty": "medium",
                "learning_style": "visual",
                "time_limit": 1800
            }
        }
        
        self.test_endpoint("POST", "/api/interactive/create-session",
                          params={"user_id": "test_user_123"},
                          data=session_data,
                          description="Create interactive learning session")
        
        # Test component library
        self.test_endpoint("GET", "/api/interactive/component-library",
                          description="Get interactive component library")
        
        # Test creating visualization
        viz_data = {
            "data": {
                "labels": ["Week 1", "Week 2", "Week 3", "Week 4"],
                "scores": [75, 82, 88, 91],
                "subjects": ["Math", "Physics", "Chemistry", "Biology"]
            },
            "title": "Learning Progress Over Time",
            "type": "line_chart"
        }
        
        self.test_endpoint("POST", "/api/interactive/create-visualization",
                          params={"chart_type": "interactive"},
                          data=viz_data,
                          description="Create interactive visualization")
    
    def run_enhanced_ai_tutor_tests(self):
        """Test enhanced AI tutor endpoints"""
        print("\n🤖 Testing Enhanced AI Tutor Endpoints...")
        
        # Test creating enhanced AI tutor session
        self.test_endpoint("POST", "/api/ai-tutor/create-session",
                          params={
                              "user_id": "test_user_123",
                              "session_name": "Calculus Study Session",
                              "subject": "mathematics"
                          },
                          description="Create enhanced AI tutor session")
        
        # Test getting learning insights
        self.test_endpoint("GET", "/api/ai-tutor/learning-insights/test_user_123",
                          description="Get comprehensive learning insights")
        
        # Test creating interactive session from chat
        interactive_data = {
            "component_ids": ["quiz_generator", "concept_explainer"],
            "preferences": {
                "difficulty": "adaptive",
                "focus_areas": ["derivatives", "chain_rule"]
            }
        }
        
        self.test_endpoint("POST", "/api/ai-tutor/create-interactive-session",
                          params={"user_id": "test_user_123"},
                          data=interactive_data,
                          description="Create interactive session from AI tutor")
    
    def run_notification_tests(self):
        """Test notification endpoints"""
        print("\n🔔 Testing Notification Endpoints...")
        
        # Test creating notification
        notification_data = {
            "type": "success",
            "title": "Quiz Completed!",
            "message": "You scored 85% on the Calculus quiz. Great job!",
            "action": {
                "label": "View Results",
                "url": "/quiz/results/123"
            },
            "data": {
                "quiz_id": "123",
                "score": 85,
                "subject": "mathematics"
            },
            "auto_dismiss": False,
            "importance": 0.8
        }
        
        self.test_endpoint("POST", "/api/notifications/test_user_123",
                          data=notification_data,
                          description="Create user notification")
        
        # Test getting notifications
        self.test_endpoint("GET", "/api/notifications/test_user_123",
                          params={"limit": 10, "unread_only": False},
                          description="Get user notifications")
        
        # Test marking all as read
        self.test_endpoint("POST", "/api/notifications/test_user_123/mark-all-read",
                          description="Mark all notifications as read")
    
    def run_notes_tests(self):
        """Test notes endpoints"""
        print("\n📝 Testing Notes Endpoints...")
        
        # Test creating note
        note_data = {
            "title": "Derivatives Study Notes",
            "content": "Key points about derivatives:\n1. Rate of change\n2. Slope of tangent line\n3. Chain rule application",
            "subject": "mathematics",
            "topic": "derivatives",
            "type": "study_note",
            "tags": ["calculus", "important"]
        }
        
        self.test_endpoint("POST", "/api/notes",
                          params={"user_id": "test_user_123"},
                          data=note_data,
                          description="Create user note")
        
        # Test getting notes
        self.test_endpoint("GET", "/api/notes",
                          params={
                              "user_id": "test_user_123",
                              "limit": 20,
                              "subject": "mathematics"
                          },
                          description="Get user notes")
    
    def run_all_tests(self):
        """Run all RAG and Memory Intelligence tests"""
        print("🚀 Starting RAG and Memory Intelligence API Testing...")
        print(f"📍 Base URL: {self.base_url}")
        print(f"⏰ Started at: {datetime.now().isoformat()}")
        
        start_time = time.time()
        
        # Run all test categories
        self.run_rag_tests()
        self.run_memory_tests()
        self.run_context_memory_tests()
        self.run_interactive_learning_tests()
        self.run_enhanced_ai_tutor_tests()
        self.run_notification_tests()
        self.run_notes_tests()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Generate summary
        self.generate_summary(total_time)
    
    def generate_summary(self, total_time: float):
        """Generate test summary"""
        total_tests = len(self.results)
        successful_tests = len([r for r in self.results if r["success"]])
        failed_tests = total_tests - successful_tests
        
        print(f"\n📊 RAG & Memory Intelligence Test Summary")
        print(f"=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"✅ Successful: {successful_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📈 Success Rate: {(successful_tests/total_tests)*100:.1f}%")
        print(f"⏱️  Total Time: {total_time:.2f} seconds")
        print(f"⚡ Average Response Time: {sum(r.get('response_time', 0) for r in self.results)/total_tests:.3f}s")
        
        # Categorize results
        rag_tests = [r for r in self.results if "/rag/" in r["endpoint"]]
        memory_tests = [r for r in self.results if any(x in r["endpoint"] for x in ["/memory/", "/knowledge-graph/", "/context/", "/interactive/", "/ai-tutor/", "/notifications/", "/notes/"])]
        
        rag_success = len([r for r in rag_tests if r["success"]])
        memory_success = len([r for r in memory_tests if r["success"]])
        
        print(f"\n📊 Category Breakdown:")
        print(f"🔍 RAG Tests: {rag_success}/{len(rag_tests)} successful ({(rag_success/len(rag_tests)*100):.1f}%)")
        print(f"🧠 Memory Tests: {memory_success}/{len(memory_tests)} successful ({(memory_success/len(memory_tests)*100):.1f}%)")
        
        # Show failed tests
        if failed_tests > 0:
            print(f"\n❌ Failed Tests:")
            for result in self.results:
                if not result["success"]:
                    print(f"   • {result['method']} {result['endpoint']} - {result.get('status_code', 'ERROR')}")
                    if 'error' in result:
                        print(f"     Error: {result['error']}")
        
        # Show successful highlights
        print(f"\n✅ Key Successful Tests:")
        successful_highlights = [r for r in self.results if r["success"] and any(x in r["endpoint"] for x in ["/rag/query", "/memory/store-session", "/context/remember", "/knowledge-graph/"])]
        for result in successful_highlights[:5]:
            print(f"   • {result['method']} {result['endpoint']} - {result['description']}")
        
        # Save detailed results to file
        with open('rag_memory_test_results.json', 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n💾 Detailed results saved to: rag_memory_test_results.json")

if __name__ == "__main__":
    tester = RAGMemoryTester(BASE_URL)
    tester.run_all_tests()