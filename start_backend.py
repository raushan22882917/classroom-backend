#!/usr/bin/env python3
"""
Backend startup script for the Educational Platform API
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Start the backend server"""
    
    # Ensure we're in the right directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    
    print("🚀 Starting Educational Platform Backend...")
    print(f"📁 Working directory: {backend_dir}")
    
    # Check if virtual environment exists
    venv_path = backend_dir / "venv_interactive_learning"
    if venv_path.exists():
        print(f"🐍 Virtual environment found: {venv_path}")
        # You can activate venv here if needed
    
    # Get port from environment or use default
    port = os.getenv("PORT", "8000")
    host = os.getenv("HOST", "0.0.0.0")
    
    print(f"🌐 Starting server on {host}:{port}")
    print("📋 Available endpoints:")
    print("  • GET  /api/admin/dashboard - Admin dashboard metrics")
    print("  • GET  /api/content/list - List all content")
    print("  • POST /api/content/upload/file - Upload content files")
    print("  • GET  /docs - API documentation")
    print("  • GET  /health - Health check")
    print()
    
    # Start the server
    try:
        cmd = [
            sys.executable, "-m", "uvicorn", 
            "app.main:app",
            "--host", host,
            "--port", port,
            "--reload"
        ]
        
        print(f"🔧 Running: {' '.join(cmd)}")
        print("🛑 Press Ctrl+C to stop the server")
        print("=" * 50)
        
        subprocess.run(cmd)
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())