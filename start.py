"""
Startup script for the AI Assistant API server
"""
import uvicorn
from src.api_server.main import app

if __name__ == "__main__":
    uvicorn.run("src.api_server.main:app", host="0.0.0.0", port=8003, reload=True)
