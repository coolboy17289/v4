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
    Main chat endpoint that processes user messages
    """
    try:
        # Store the user message in memory
        user_memory_item = MemoryItem(
            content=message.message,
            memory_type=MemoryType.WORKING,
            importance=0.5,
            metadata={"message_type": "user_message", "session_id": message.session_id}
        )
        logger.info(f"User memory item type: {type(user_memory_item)}")
        memory_manager.add_memory(user_memory_item)

        # Determine what type of processing is needed
        # For now, we'll use a simple approach - in reality, this would be more sophisticated
        # We'll start with the research agent for questions, coding agent for code requests

        # Simple heuristic: if message contains code-related keywords, use coding agent
        code_keywords = ["code", "function", "class", "variable", "program", "script", "debug", "fix"]
        if any(keyword in message.message.lower() for keyword in code_keywords):
            # Use coding agent
            coding_request = {
                "task": message.message,
                "language": message.context.get("language", "python") if message.context else "python"
            }

            # Get available coding agent
            coding_result = await agent_manager.route_task(AgentType.CODING, coding_request)

            if coding_result.success:
                response_text = coding_result.data.get("code", "I couldn't generate code for that request.")
                explanation = coding_result.data.get("explanation", "")
                confidence = coding_result.confidence
            else:
                response_text = f"I encountered an error while trying to help with coding: {coding_result.error}"
                explanation = ""
                confidence = 0.1
        else:
            # Use research agent for general questions
            research_request = {
                "query": message.message
            }

            # Get available research agent
            research_result = await agent_manager.route_task(AgentType.RESEARCH, research_request)

            if research_result.success:
                findings = research_result.data.get("findings", [])
                summary = research_result.data.get("summary", "")
                sources = research_result.data.get("sources", [])
                response_text = f"{summary}\n\nKey findings:\n" + "\n".join([f"- {f}" for f in findings])
                confidence = research_result.confidence
            else:
                response_text = f"I encountered an error while researching: {research_result.error}"
                findings = []
                summary = ""
                sources = []
                confidence = 0.1

        # Store the assistant's response in memory
        assistant_memory_item = MemoryItem(
            content=response_text,
            memory_type=MemoryType.WORKING,
            importance=0.5,
            metadata={"message_type": "assistant_message", "session_id": message.session_id}
        )
        memory_manager.add_memory(assistant_memory_item)

        return ChatResponse(
            response=response_text,
            session_id=message.session_id or "default",
            confidence=confidence,
            sources=[] if 'sources' not in locals() else sources,
            metadata={"processing_type": "research" if 'research_result' in locals() else "coding"}
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