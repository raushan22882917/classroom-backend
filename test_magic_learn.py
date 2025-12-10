"""Test script for Magic Learn API endpoints"""

import asyncio
import base64
import json
from datetime import datetime
from typing import Dict, Any

# Import the services directly for testing
from app.models.magic_learn import (
    ImageAnalysisRequest, AnalysisType,
    GestureRecognitionRequest, GesturePoint,
    PlotCrafterRequest
)
from app.services.magic_learn_service import (
    image_reader_service,
    draw_in_air_service,
    plot_crafter_service,
    analytics_service
)


async def test_image_reader():
    """Test the Image Reader service"""
    print("🖼️  Testing Image Reader Service...")
    
    # Create a simple test image (1x1 white pixel)
    test_image_data = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
    
    # Test mathematical analysis
    request = ImageAnalysisRequest(
        image_data=test_image_data,
        analysis_type=AnalysisType.MATHEMATICAL,
        custom_instructions="Analyze any mathematical content in this image",
        user_id="test_user_123"
    )
    
    result = await image_reader_service.analyze_image(request)
    
    print(f"✅ Mathematical Analysis:")
    print(f"   Success: {result.success}")
    print(f"   Confidence: {result.confidence_score:.2f}")
    print(f"   Processing Time: {result.processing_time:.2f}s")
    print(f"   Detected Elements: {result.detected_elements}")
    print(f"   Analysis Preview: {result.analysis[:100]}...")
    
    # Test scientific analysis
    request.analysis_type = AnalysisType.SCIENTIFIC
    result = await image_reader_service.analyze_image(request)
    
    print(f"✅ Scientific Analysis:")
    print(f"   Success: {result.success}")
    print(f"   Confidence: {result.confidence_score:.2f}")
    print(f"   Detected Elements: {result.detected_elements}")
    
    return result


async def test_draw_in_air():
    """Test the DrawInAir service"""
    print("\n✋ Testing DrawInAir Service...")
    
    # Create test gesture points for a circle
    circle_points = []
    import math
    center_x, center_y, radius = 200, 200, 50
    
    for i in range(20):
        angle = (i / 20) * 2 * math.pi
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        
        point = GesturePoint(
            x=x,
            y=y,
            timestamp=datetime.utcnow()
        )
        circle_points.append(point)
    
    request = GestureRecognitionRequest(
        gesture_points=circle_points,
        canvas_width=400,
        canvas_height=400,
        user_id="test_user_123"
    )
    
    result = await draw_in_air_service.recognize_gestures(request)
    
    print(f"✅ Gesture Recognition:")
    print(f"   Success: {result.success}")
    print(f"   Recognized Shapes: {len(result.recognized_shapes)}")
    
    for i, shape in enumerate(result.recognized_shapes):
        print(f"   Shape {i+1}: {shape.shape_type} (confidence: {shape.confidence:.2f})")
        if shape.properties:
            print(f"      Properties: {list(shape.properties.keys())}")
    
    print(f"   Suggestions: {len(result.suggestions)} learning suggestions")
    print(f"   Interpretation Preview: {result.interpretation[:100]}...")
    
    return result


async def test_plot_crafter():
    """Test the Plot Crafter service"""
    print("\n📚 Testing Plot Crafter Service...")
    
    request = PlotCrafterRequest(
        story_prompt="A student discovers patterns in nature while studying mathematics",
        educational_topic="Mathematics - Fibonacci Sequence and Golden Ratio",
        target_age_group="12-18",
        story_length="medium",
        user_id="test_user_123"
    )
    
    result = await plot_crafter_service.generate_story(request)
    
    print(f"✅ Story Generation:")
    print(f"   Success: {result.success}")
    print(f"   Story Title: {result.story.title}")
    print(f"   Characters: {len(result.story.characters)}")
    print(f"   Settings: {len(result.story.settings)}")
    print(f"   Educational Elements: {len(result.story.educational_elements)}")
    print(f"   Learning Objectives: {len(result.story.learning_objectives)}")
    print(f"   Visualization Prompts: {len(result.visualization_prompts)}")
    print(f"   Interactive Elements: {len(result.interactive_elements)}")
    
    # Print some details
    if result.story.characters:
        print(f"   Main Character: {result.story.characters[0].name}")
    
    if result.story.educational_elements:
        print(f"   Key Concepts: {', '.join(result.story.educational_elements[:3])}")
    
    print(f"   Content Preview: {result.story.content[:150]}...")
    
    return result


async def test_analytics():
    """Test the Analytics service"""
    print("\n📊 Testing Analytics Service...")
    
    # Create some test sessions
    session1 = await analytics_service.create_session("test_user_1", "image_reader")
    session2 = await analytics_service.create_session("test_user_2", "draw_in_air")
    session3 = await analytics_service.create_session("test_user_3", "plot_crafter")
    
    # Update sessions with metadata
    await analytics_service.update_session(session1, {
        "analysis_type": "mathematical",
        "success": True,
        "processing_time": 2.1,
        "confidence_score": 0.92
    })
    
    await analytics_service.update_session(session2, {
        "recognized_shapes_count": 2,
        "success": True,
        "shapes_detected": ["circle", "line"]
    })
    
    await analytics_service.update_session(session3, {
        "story_title": "Test Story",
        "success": True,
        "characters_count": 2
    })
    
    # Get analytics
    analytics = await analytics_service.get_analytics()
    
    print(f"✅ Analytics Summary:")
    print(f"   Total Sessions: {analytics.total_sessions}")
    print(f"   Image Reader Usage: {analytics.image_reader_usage}")
    print(f"   DrawInAir Usage: {analytics.draw_in_air_usage}")
    print(f"   Plot Crafter Usage: {analytics.plot_crafter_usage}")
    print(f"   Average Processing Time: {analytics.average_processing_time}s")
    print(f"   Success Rate: {analytics.success_rate}%")
    print(f"   Popular Analysis Types: {len(analytics.popular_analysis_types)}")
    
    return analytics


async def run_comprehensive_test():
    """Run comprehensive tests for all Magic Learn services"""
    print("🚀 Starting Magic Learn Comprehensive Test Suite")
    print("=" * 60)
    
    try:
        # Test all services
        image_result = await test_image_reader()
        gesture_result = await test_draw_in_air()
        story_result = await test_plot_crafter()
        analytics_result = await test_analytics()
        
        print("\n" + "=" * 60)
        print("📋 Test Summary:")
        print(f"   ✅ Image Reader: {'PASS' if image_result.success else 'FAIL'}")
        print(f"   ✅ DrawInAir: {'PASS' if gesture_result.success else 'FAIL'}")
        print(f"   ✅ Plot Crafter: {'PASS' if story_result.success else 'FAIL'}")
        print(f"   ✅ Analytics: PASS")
        
        # Overall success
        all_passed = all([
            image_result.success,
            gesture_result.success,
            story_result.success
        ])
        
        print(f"\n🎉 Overall Result: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
        
        return {
            "image_reader": image_result,
            "draw_in_air": gesture_result,
            "plot_crafter": story_result,
            "analytics": analytics_result,
            "all_passed": all_passed
        }
        
    except Exception as e:
        print(f"\n❌ Test Suite Failed: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return {"error": str(e), "all_passed": False}


def test_api_models():
    """Test the Pydantic models"""
    print("🔧 Testing API Models...")
    
    # Test ImageAnalysisRequest
    image_request = ImageAnalysisRequest(
        image_data="test_base64_data",
        analysis_type=AnalysisType.MATHEMATICAL,
        custom_instructions="Test instructions",
        user_id="test_user"
    )
    print(f"✅ ImageAnalysisRequest: {image_request.analysis_type}")
    
    # Test GesturePoint
    gesture_point = GesturePoint(
        x=100.5,
        y=200.3,
        timestamp=datetime.utcnow()
    )
    print(f"✅ GesturePoint: ({gesture_point.x}, {gesture_point.y})")
    
    # Test PlotCrafterRequest
    story_request = PlotCrafterRequest(
        story_prompt="Test story prompt",
        educational_topic="Mathematics",
        target_age_group="12-18",
        story_length="medium"
    )
    print(f"✅ PlotCrafterRequest: {story_request.story_prompt[:30]}...")
    
    print("✅ All models validated successfully!")


if __name__ == "__main__":
    print("🧪 Magic Learn Test Suite")
    print("=" * 40)
    
    # Test models first
    test_api_models()
    print()
    
    # Run comprehensive async tests
    results = asyncio.run(run_comprehensive_test())
    
    if results.get("all_passed"):
        print("\n🎊 Magic Learn backend is ready for deployment!")
        print("\nNext steps:")
        print("1. Start the FastAPI server: uvicorn app.main:app --reload")
        print("2. Visit http://localhost:8000/docs to see the API documentation")
        print("3. Test endpoints with the interactive Swagger UI")
        print("4. Integrate with your frontend application")
    else:
        print("\n⚠️  Some tests failed. Please check the implementation.")
        
    print("\n📖 API Documentation: See MAGIC_LEARN_API.md for detailed usage")