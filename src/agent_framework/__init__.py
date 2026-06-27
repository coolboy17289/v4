"""
Agent Framework Package
"""

from .base_agent import BaseAgent, AgentType, AgentStatus, AgentResult
from .agent_manager import AgentManager
from .research_agent import ResearchAgent, CodingAgent, PlanningAgent
from .file_agent import FileAgent
from .browser_agent import BrowserAgent
from .vision_agent import VisionAgent
from .memory_agent import MemoryAgent
from .math_agent import MathAgent
from .automation_agent import AutomationAgent

__all__ = [
    "BaseAgent",
    "AgentType",
    "AgentStatus",
    "AgentResult",
    "AgentManager",
    "ResearchAgent",
    "CodingAgent",
    "PlanningAgent",
    "FileAgent",
    "BrowserAgent",
    "VisionAgent",
    "MemoryAgent",
    "MathAgent",
    "AutomationAgent"
]