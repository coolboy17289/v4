"""
Startup script for the AI Assistant
"""

import uvicorn
import sys
import os

if __name__ == "__main__":
    # Add the src directory to the path
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

    print("Starting AI Assistant API Server...")
    print("Access the API at http://localhost:8000")
    print("API documentation available at http://localhost:8000/docs")
    print("Press Ctrl+C to stop the server")

    uvicorn.run(
        "src.api_server.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )