"""
Main API Server for the AI Assistant
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import uvicorn
import asyncio
import json
import logging

# Import our modules
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.agent_framework.agent_manager import AgentManager
from src.agent_framework.base_agent import AgentType
from src.agent_framework import (
    ResearchAgent, CodingAgent, PlanningAgent, FileAgent,
    BrowserAgent, VisionAgent, MemoryAgent, MathAgent, AutomationAgent
)
from src.memory_manager.memory_manager import MemoryManager
from src.model_manager.model_router import ModelRouter, TaskType
from src.memory_manager.memory_types import MemoryItem, MemoryType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the FastAPI app
app = FastAPI(title="AI Assistant API", version="0.1.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize core components
agent_manager = AgentManager()
memory_manager = MemoryManager()
model_router = ModelRouter()
chat_engine = ChatEngine(agent_manager, memory_manager)

# Create and register agents
agent_manager.register_agent(ResearchAgent("research_agent"))
agent_manager.register_agent(CodingAgent("coding_agent"))
agent_manager.register_agent(PlanningAgent("planning_agent"))
agent_manager.register_agent(FileAgent("file_agent"))
agent_manager.register_agent(BrowserAgent("browser_agent"))
agent_manager.register_agent(VisionAgent("vision_agent"))
agent_manager.register_agent(MemoryAgent("memory_agent"))
agent_manager.register_agent(MathAgent("math_agent"))
agent_manager.register_agent(AutomationAgent("automation_agent"))


# Pydantic models for request/response
class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    confidence: float
    sources: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None

class ResearchRequest(BaseModel):
    query: str
    depth: Optional[str] = "medium"  # quick, medium, deep

class ResearchResponse(BaseModel):
    query: str
    findings: List[str]
    sources: List[Dict[str, Any]]
    summary: str
    confidence: float

class CodeRequest(BaseModel):
    task: str
    language: Optional[str] = "python"
    requirements: Optional[List[str]] = None

class CodeResponse(BaseModel):
    task: str
    language: str
    code: str
    explanation: str
    confidence: float

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

# Routes
@app.get("/")
async def root():
    return {"message": "AI Assistant API is running"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "components": {
            "agent_manager": "active",
            "memory_manager": "active",
            "model_router": "active"
        }
    }

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(message: ChatMessage):
    """
    Main chat endpoint that processes user messages using the ChatEngine
    """
    print("ENTERING CHAT ENDPOINT")
    logger.info("About to enter try block")
    try:
        logger.info("Entering chat endpoint try block")
        # Process the message using the chat engine
        result = await chat_engine.process_message(
            user_id=message.session_id or "anonymous",
            message=message.message,
            conversation_id=None,  # Let chat engine create or find conversation
            context=message.context,
            reasoning_type="auto"  # Let the chat engine determine the best reasoning type
        )

        if result["success"]:
            return ChatResponse(
                response=result["response"],
                session_id=message.session_id or "default",
                confidence=result.get("confidence", 0.0),
                sources=[],  # Sources would come from specific tool usage in a full implementation
                metadata={
                    "processing_type": "chat_engine",
                    "conversation_id": result.get("conversation_id"),
                    "reasoning_type": result.get("reasoning_type")
                }
            )
        else:
            # Return error response
            return ChatResponse(
                response=result.get("response", "I encountered an error processing your request."),
                session_id=message.session_id or "default",
                confidence=0.1,
                sources=[],
                metadata={
                    "processing_type": "error",
                    "error": result.get("error", "Unknown error")
                }
            )
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/research", response_model=ResearchResponse)
async def research_endpoint(request: ResearchRequest):
    """
    Dedicated research endpoint
    """
    try:
        research_request = {
            "query": request.query
        }

        research_result = await agent_manager.route_task(AgentType.RESEARCH, research_request)

        if research_result.success:
            return ResearchResponse(
                query=request.query,
                findings=research_result.data.get("findings", []),
                sources=research_result.data.get("sources", []),
                summary=research_result.data.get("summary", ""),
                confidence=research_result.confidence
            )
        else:
            raise HTTPException(status_code=500, detail=research_result.error)

    except Exception as e:
        logger.error(f"Error in research endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/code", response_model=CodeResponse)
async def code_endpoint(request: CodeRequest):
    """
    Dedicated code generation endpoint
    """
    try:
        code_request = {
            "task": request.task,
            "language": request.language,
            "requirements": request.requirements or []
        }

        code_result = await agent_manager.route_task(AgentType.CODING, code_request)

        if code_result.success:
            return CodeResponse(
                task=request.task,
                language=request.language,
                code=code_result.data.get("code", ""),
                explanation=code_result.data.get("explanation", ""),
                confidence=code_result.confidence
            )
        else:
            raise HTTPException(status_code=500, detail=code_result.error)

    except Exception as e:
        logger.error(f"Error in code endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time communication
    """
    await manager.connect(websocket)
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)

            # Process the message
            chat_message = ChatMessage(
                message=message_data.get("message", ""),
                session_id=session_id,
                context=message_data.get("context", {})
            )

            # Get response
            response = await chat_endpoint(chat_message)

            # Send response back to client
            await manager.send_personal_message(json(response.dict()), websocket)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        manager.disconnect(websocket)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)