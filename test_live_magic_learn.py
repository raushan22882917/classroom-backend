"""
Comprehensive test suite for Magic Learn API endpoints
Tests the live deployed backend at: https://classroom-backend-821372121985.us-central1.run.app
"""

import requests
import base64
import json
import time
from datetime import datetime
import io
from PIL import Image, ImageDraw

# Backend URL
BASE_URL = "https://classroom-backend-821372121985.us-central1.run.app/api/magic-learn"

def create_test_image():
    """Create a simple test image with mathematical content"""
    # Create a white image
    img = Image.new('RGB', (400, 200), color='white')
    draw = ImageDraw.Draw(img)
    
    # Draw some mathematical content
    draw.text((50, 50), "x² + 5x + 6 = 0", fill='black')
    draw.text((50, 100), "Solution: x = -2, x = -3", fill='blue')
    
    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    img_bytes = buffer.getvalue()
    img_base64 = base64.b64encode(img_bytes).decode('utf-8')
    
    return f"data:image/png;base64,{img_base64}"

def test_health_check():
    """Test the health check endpoint"""
    print("🏥 Testing Health Check...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Health Check: {data.get('status', 'unknown')}")
            print(f"   Services: {list(data.get('services', {}).keys())}")
            return True
        else:
            print(f"   ❌ Health Check Failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Health Check Error: {str(e)}")
        return False

def test_cors():
    """Test CORS configuration"""
    print("\n🌐 Testing CORS Configuration...")
    try:
        # Test preflight request
        headers = {
            'Origin': 'http://localhost:8080',
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'Content-Type'
        }
        
        response = requests.options(f"{BASE_URL}/cors-test", headers=headers, timeout=10)
        print(f"   Preflight Status: {response.status_code}")
        
        # Check CORS headers
        cors_headers = {
            'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
            'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
            'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
        }
        
        print(f"   CORS Headers: {cors_headers}")
        
        # Test actual request
        test_response = requests.get(f"{BASE_URL}/cors-test", headers={'Origin': 'http://localhost:8080'}, timeout=10)
        if test_response.status_code == 200:
            print("   ✅ CORS Test Passed")
            return True
        else:
            print(f"   ❌ CORS Test Failed: {test_response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ CORS Test Error: {str(e)}")
        return False

def test_image_reader():
    """Test Image Reader functionality"""
    print("\n🖼️  Testing Image Reader...")
    
    # Test 1: Base64 image analysis
    print("   Testing base64 image analysis...")
    try:
        test_image = create_test_image()
        
        payload = {
            "image_data": test_image.split(',')[1],  # Remove data URL prefix
            "analysis_type": "mathematical",
            "custom_instructions": "Solve this quadratic equation step by step",
            "user_id": "test_user"
        }
        
        response = requests.post(
            f"{BASE_URL}/image-reader/analyze",
            json=payload,
            timeout=30
        )
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Analysis Success: {data.get('success', False)}")
            print(f"   Confidence: {data.get('confidence_score', 0):.2f}")
            print(f"   Processing Time: {data.get('processing_time', 0):.2f}s")
            print(f"   Detected Elements: {data.get('detected_elements', [])}")
            print(f"   Analysis Preview: {data.get('analysis', '')[:100]}...")
            return True
        else:
            print(f"   ❌ Image Analysis Failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Image Reader Error: {str(e)}")
        return False

def test_image_reader_upload():
    """Test Image Reader file upload"""
    print("\n📤 Testing Image Reader File Upload...")
    try:
        # Create test image file
        img = Image.new('RGB', (300, 150), color='white')
        draw = ImageDraw.Draw(img)
        draw.text((50, 50), "2x + 3 = 7", fill='black')
        
        # Save to bytes
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        # Prepare multipart form data
        files = {
            'file': ('test_equation.png', img_buffer, 'image/png')
        }
        
        data = {
            'analysis_type': 'mathematical',
            'custom_instructions': 'Solve this linear equation',
            'user_id': 'test_user'
        }
        
        response = requests.post(
            f"{BASE_URL}/image-reader/upload",
            files=files,
            data=data,
            timeout=30
        )
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Upload Analysis Success: {result.get('success', False)}")
            print(f"   Analysis Preview: {result.get('analysis', '')[:100]}...")
            return True
        else:
            print(f"   ❌ Upload Analysis Failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Image Upload Error: {str(e)}")
        return False

def test_draw_in_air():
    """Test DrawInAir functionality"""
    print("\n✋ Testing DrawInAir...")
    
    # Test 1: Start session
    print("   Testing DrawInAir session start...")
    try:
        response = requests.post(f"{BASE_URL}/draw-in-air/start", json={}, timeout=10)
        print(f"   Start Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Session Started: {data.get('success', False)}")
            print(f"   Canvas Size: {data.get('canvas_size', {})}")
        else:
            print(f"   ❌ Session Start Failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ DrawInAir Start Error: {str(e)}")
        return False
    
    # Test 2: Analyze drawing
    print("   Testing drawing analysis...")
    try:
        # Create a simple drawing (circle)
        img = Image.new('RGB', (400, 300), color='black')
        draw = ImageDraw.Draw(img)
        draw.ellipse([100, 100, 200, 200], outline='magenta', width=3)
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        payload = {
            "image": f"data:image/png;base64,{img_base64}",
            "user_id": "test_user"
        }
        
        response = requests.post(
            f"{BASE_URL}/draw-in-air/analyze",
            json=payload,
            timeout=30
        )
        
        print(f"   Analysis Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Drawing Analysis: {data.get('success', False)}")
            print(f"   Result Preview: {data.get('result', '')[:100]}...")
            return True
        else:
            print(f"   ❌ Drawing Analysis Failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Drawing Analysis Error: {str(e)}")
        return False

def test_draw_in_air_controls():
    """Test DrawInAir control endpoints"""
    print("\n🎮 Testing DrawInAir Controls...")
    
    # Test clear canvas
    try:
        response = requests.post(f"{BASE_URL}/draw-in-air/clear", json={}, timeout=10)
        print(f"   Clear Canvas Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Canvas Cleared: {data.get('success', False)}")
        else:
            print(f"   ❌ Clear Failed: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Clear Canvas Error: {str(e)}")
    
    # Test get current gesture
    try:
        response = requests.get(f"{BASE_URL}/draw-in-air/gesture", timeout=10)
        print(f"   Get Gesture Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Current Gesture: {data.get('gesture', 'None')}")
        else:
            print(f"   ❌ Get Gesture Failed: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Get Gesture Error: {str(e)}")
    
    # Test stop session
    try:
        response = requests.post(f"{BASE_URL}/draw-in-air/stop", json={}, timeout=10)
        print(f"   Stop Session Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Session Stopped: {data.get('success', False)}")
            return True
        else:
            print(f"   ❌ Stop Failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Stop Session Error: {str(e)}")
        return False

def test_plot_crafter():
    """Test Plot Crafter functionality"""
    print("\n📚 Testing Plot Crafter...")
    
    # Test story generation
    print("   Testing story generation...")
    try:
        payload = {
            "story_prompt": "A student discovers the golden ratio while studying sunflower patterns in their school garden",
            "educational_topic": "Mathematics - Golden Ratio and Fibonacci Sequence",
            "target_age_group": "12-18",
            "story_length": "medium",
            "user_id": "test_user"
        }
        
        response = requests.post(
            f"{BASE_URL}/plot-crafter/generate",
            json=payload,
            timeout=60  # Longer timeout for story generation
        )
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Story Generation: {data.get('success', False)}")
            
            if data.get('success') and data.get('story'):
                story = data['story']
                print(f"   Story Title: {story.get('title', 'No title')}")
                print(f"   Characters: {len(story.get('characters', []))}")
                print(f"   Educational Elements: {len(story.get('educational_elements', []))}")
                print(f"   Learning Objectives: {len(story.get('learning_objectives', []))}")
                print(f"   Visualization Prompts: {len(data.get('visualization_prompts', []))}")
                print(f"   Interactive Elements: {len(data.get('interactive_elements', []))}")
                print(f"   Content Preview: {story.get('content', '')[:150]}...")
                return True
            else:
                print(f"   ❌ Story Generation Failed: {data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"   ❌ Plot Crafter Failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Plot Crafter Error: {str(e)}")
        return False

def test_plot_crafter_simple():
    """Test Plot Crafter simple explanation"""
    print("\n📝 Testing Plot Crafter Simple Explanation...")
    try:
        payload = {
            "theme": "Photosynthesis",
            "user_id": "test_user"
        }
        
        response = requests.post(
            f"{BASE_URL}/plot-crafter/generate-simple",
            json=payload,
            timeout=30
        )
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Simple Explanation: {data.get('success', False)}")
            print(f"   Result Preview: {data.get('result', '')[:150]}...")
            return True
        else:
            print(f"   ❌ Simple Explanation Failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Simple Explanation Error: {str(e)}")
        return False

def test_analytics():
    """Test analytics endpoint"""
    print("\n📊 Testing Analytics...")
    try:
        response = requests.get(f"{BASE_URL}/analytics", timeout=10)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Analytics Retrieved")
            print(f"   Total Sessions: {data.get('total_sessions', 0)}")
            print(f"   Image Reader Usage: {data.get('image_reader_usage', 0)}")
            print(f"   DrawInAir Usage: {data.get('draw_in_air_usage', 0)}")
            print(f"   Plot Crafter Usage: {data.get('plot_crafter_usage', 0)}")
            print(f"   Success Rate: {data.get('success_rate', 0)}%")
            return True
        else:
            print(f"   ❌ Analytics Failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Analytics Error: {str(e)}")
        return False

def test_utility_endpoints():
    """Test utility endpoints"""
    print("\n🔧 Testing Utility Endpoints...")
    
    # Test analysis types
    try:
        response = requests.get(f"{BASE_URL}/analysis-types", timeout=10)
        print(f"   Analysis Types Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Analysis Types: {len(data.get('analysis_types', []))} types")
        else:
            print(f"   ❌ Analysis Types Failed: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Analysis Types Error: {str(e)}")
    
    # Test examples
    try:
        response = requests.get(f"{BASE_URL}/examples", timeout=10)
        print(f"   Examples Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Examples Retrieved")
            print(f"   Image Reader Examples: {len(data.get('image_reader_examples', []))}")
            print(f"   DrawInAir Examples: {len(data.get('draw_in_air_examples', []))}")
            print(f"   Plot Crafter Examples: {len(data.get('plot_crafter_examples', []))}")
            return True
        else:
            print(f"   ❌ Examples Failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Examples Error: {str(e)}")
        return False

def test_feedback():
    """Test feedback submission"""
    print("\n💬 Testing Feedback Submission...")
    try:
        payload = {
            "session_id": "test-session-123",
            "rating": 5,
            "feedback_text": "Great AI analysis!",
            "user_id": "test_user"
        }
        
        response = requests.post(
            f"{BASE_URL}/feedback",
            json=payload,
            timeout=10
        )
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Feedback Submitted: {data.get('success', False)}")
            return True
        else:
            print(f"   ❌ Feedback Failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Feedback Error: {str(e)}")
        return False

def run_comprehensive_test():
    """Run all tests and provide summary"""
    print("🚀 Magic Learn Comprehensive Test Suite")
    print("=" * 60)
    print(f"Testing Backend: {BASE_URL}")
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    test_results = {}
    
    # Run all tests
    test_results['health'] = test_health_check()
    test_results['cors'] = test_cors()
    test_results['image_reader'] = test_image_reader()
    test_results['image_upload'] = test_image_reader_upload()
    test_results['draw_in_air'] = test_draw_in_air()
    test_results['draw_controls'] = test_draw_in_air_controls()
    test_results['plot_crafter'] = test_plot_crafter()
    test_results['plot_simple'] = test_plot_crafter_simple()
    test_results['analytics'] = test_analytics()
    test_results['utilities'] = test_utility_endpoints()
    test_results['feedback'] = test_feedback()
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for result in test_results.values() if result)
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name.replace('_', ' ').title():<25} {status}")
    
    print("-" * 60)
    print(f"   Overall Result: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Magic Learn is fully functional!")
        print("\n🚀 Ready for frontend integration:")
        print("   1. Use the HTML examples from MAGIC_LEARN_INTEGRATION_GUIDE.md")
        print("   2. Serve frontend from http://localhost:8080")
        print("   3. All three tools (Image Reader, DrawInAir, Plot Crafter) are working")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check the errors above.")
        print("   - Verify backend deployment")
        print("   - Check API keys configuration")
        print("   - Ensure all dependencies are installed")
    
    return passed == total

if __name__ == "__main__":
    success = run_comprehensive_test()
    exit(0 if success else 1)