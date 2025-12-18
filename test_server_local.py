#!/usr/bin/env python3
"""
Test script to start server locally and test endpoints
"""

import asyncio
import subprocess
import time
import requests
import json
import signal
import sys
from threading import Thread

def start_server():
    """Start the uvicorn server"""
    try:
        print("🚀 Starting local server...")
        process = subprocess.Popen([
            "python3", "-m", "uvicorn", "app.main:app", 
            "--host", "127.0.0.1", "--port", "8080"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Give server time to start
        time.sleep(5)
        
        return process
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        return None

def test_endpoints():
    """Test various endpoints"""
    base_url = "http://127.0.0.1:8080"
    
    tests = [
        ("GET", "/", "Root endpoint"),
        ("GET", "/ready", "Readiness probe"),
        ("GET", "/api/health", "Health check"),
        ("GET", "/info", "API info"),
        ("POST", "/api/rag/query", "RAG query", {"query": "What is photosynthesis?", "subject": "biology"})
    ]
    
    results = []
    
    for method, path, description, *data in tests:
        try:
            url = f"{base_url}{path}"
            print(f"🧪 Testing {description}: {method} {path}")
            
            if method == "GET":
                response = requests.get(url, timeout=10)
            elif method == "POST":
                payload = data[0] if data else {}
                response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ {description}: {response.status_code}")
                results.append((description, "PASS", response.status_code))
            else:
                print(f"❌ {description}: {response.status_code} - {response.text[:100]}")
                results.append((description, "FAIL", response.status_code))
                
        except Exception as e:
            print(f"❌ {description}: Error - {str(e)}")
            results.append((description, "ERROR", str(e)))
    
    return results

def main():
    """Main test function"""
    print("🧪 Starting local server test...")
    
    # Start server
    server_process = start_server()
    if not server_process:
        print("❌ Could not start server")
        return
    
    try:
        # Wait for server to be ready
        print("⏳ Waiting for server to be ready...")
        for i in range(10):
            try:
                response = requests.get("http://127.0.0.1:8080/", timeout=2)
                if response.status_code == 200:
                    print("✅ Server is ready!")
                    break
            except:
                time.sleep(1)
        else:
            print("❌ Server did not start properly")
            return
        
        # Run tests
        print("\n🧪 Running endpoint tests...")
        results = test_endpoints()
        
        # Print summary
        print("\n📊 Test Results:")
        print("-" * 50)
        for description, status, code in results:
            status_icon = "✅" if status == "PASS" else "❌"
            print(f"{status_icon} {description}: {status} ({code})")
        
        # Count results
        passed = sum(1 for _, status, _ in results if status == "PASS")
        total = len(results)
        print(f"\n🎯 Summary: {passed}/{total} tests passed")
        
    finally:
        # Clean up
        print("\n🧹 Cleaning up...")
        server_process.terminate()
        server_process.wait()
        print("✅ Server stopped")

if __name__ == "__main__":
    main()