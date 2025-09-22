#!/usr/bin/env python3
"""
Development server launcher for MIDAS Vision API.

This script starts the FastAPI server with appropriate settings for development.
For production, you'd use a proper ASGI server deployment.
"""

import uvicorn
import sys
from pathlib import Path

# Add src to Python path so imports work correctly
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

if __name__ == "__main__":
    print("Starting MIDAS Vision API Development Server")
    print(f"Project root: {project_root}")
    print(f"Source path: {src_path}")
    print("Server will be available at: http://localhost:8000")
    print("API documentation at: http://localhost:8000/docs")
    print("Alternative docs at: http://localhost:8000/redoc")
    print("\n" + "="*50 + "\n")
    
    # Start the server
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",  # Accept connections from any IP
        port=8000,
        reload=True,     # Auto-reload on code changes (development only)
        reload_dirs=[str(src_path)],  # Only watch src directory
        log_level="info"
    )