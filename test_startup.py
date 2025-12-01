#!/usr/bin/env python3
"""Test script to verify the application can start"""

import sys
import os

print("=" * 80)
print("Testing Application Startup")
print("=" * 80)
print()

# Test 1: Python imports
print("1. Testing Python imports...")
try:
    from fastapi import FastAPI
    print("   ✓ FastAPI imported")
except Exception as e:
    print(f"   ✗ Failed to import FastAPI: {e}")
    sys.exit(1)

# Test 2: Check environment variables
print()
print("2. Checking environment variables...")
required_vars = [
    "SUPABASE_URL",
    "SUPABASE_KEY", 
    "SUPABASE_SERVICE_KEY",
    "GOOGLE_CLOUD_PROJECT",
    "GEMINI_API_KEY",
    "WOLFRAM_APP_ID",
    "YOUTUBE_API_KEY"
]

missing = []
for var in required_vars:
    if os.getenv(var):
        print(f"   ✓ {var}: SET")
    else:
        print(f"   ✗ {var}: NOT SET")
        missing.append(var)

if missing:
    print()
    print("=" * 80)
    print("WARNING: Missing required environment variables:")
    print("=" * 80)
    for var in missing:
        print(f"  - {var}")
    print()
    print("The application will fail to start without these variables.")
    print("=" * 80)
    print()

# Test 3: Try to load settings
print()
print("3. Testing configuration loading...")
try:
    from app.config import settings
    print("   ✓ Settings loaded successfully")
except Exception as e:
    print(f"   ✗ Failed to load settings: {e}")
    print()
    print("=" * 80)
    print("ERROR: Configuration validation failed!")
    print("=" * 80)
    print(f"Details: {e}")
    print()
    if missing:
        print("This is likely because required environment variables are missing.")
        print("Please set all required environment variables in Cloud Run.")
    print("=" * 80)
    sys.exit(1)

# Test 4: Try to import the app
print()
print("4. Testing application import...")
try:
    from app.main import app
    print("   ✓ Application imported successfully")
except Exception as e:
    print(f"   ✗ Failed to import application: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("=" * 80)
print("✓ All startup checks passed!")
print("=" * 80)
print()



