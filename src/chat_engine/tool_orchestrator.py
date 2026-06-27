"""
Tool Orchestrator for managing and coordinating various tools and agents
"""

import logging
from typing import Dict, List, Any, Optional
import asyncio
from enum import Enum

from src.agent_framework.agent_manager import AgentManager
from src.agent_framework.base_agent import AgentType

logger = logging.getLogger(__name__)


class ToolType(Enum):
    """Types of tools available"""
    RESEARCH = "research"
    CODING = "coding"
    PLANNING = "planning"
    FILE = "file"
    BROWSER = "browser"
    VISION = "vision"
    MEMORY = "memory"
    MATH = "math"
    AUTOMATION = "automation"
    YOUTUBE = "youtube"
    DOCUMENT = "document"
    WEB_SEARCH = "web_search"
    KNOWLEDGE_GRAPH = "knowledge_graph"
    WORKFLOW = "workflow"


class ToolOrchestrator:
    """Orchestrates the use of various tools and agents"""

    def __init__(self, agent_manager: AgentManager):
        self.agent_manager = agent_manager
        self.logger = logging.getLogger(__name__)
        self._tool_agents: Dict[ToolType, str] = {}

        # Initialize tool-agent mapping
        self._initialize_tool_mapping()

    def _initialize_tool_mapping(self):
        """Initialize mapping of tool types to agent types"""
        self._tool_agents[ToolType.RESEARCH] = AgentType.RESEARCH
        self._tool_agents[ToolType.CODING] = AgentType.CODING
        self._tool_agents[ToolType.PLANNING] = AgentType.PLANNING
        self._tool_agents[ToolType.FILE] = AgentType.FILE
        self._tool_agents[ToolType.BROWSER] = AgentType.BROWSER
        self._tool_agents[ToolType.VISION] = AgentType.VISION
        self._tool_agents[ToolType.MEMORY] = AgentType.MEMORY
        self._tool_agents[ToolType.MATH] = AgentType.MATH
        self._tool_agents[ToolType.AUTOMATION] = AgentType.AUTOMATION

        # Additional tools that might use custom agents
        self._tool_agents[ToolType.YOUTUBE] = AgentType.CODING  # Placeholder
        self._tool_agents[ToolType.DOCUMENT] = AgentType.FILE   # Placeholder
        self._tool_agents[ToolType.WEB_SEARCH] = AgentType.RESEARCH  # Placeholder
        self._tool_agents[ToolType.KNOWLEDGE_GRAPH] = AgentType.PLANNING  # Placeholder
        self._tool_agents[ToolType.WORKFLOW] = AgentType.PLANNING  # Placeholder

    async def use_tool(self, tool_type: ToolType, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use a specific tool/agent

        Args:
            tool_type: Type of tool to use
            input_data: Input data for the tool

        Returns:
            Tool execution result
        """
        agent_type = self._tool_agents.get(tool_type)
        if not agent_type:
            raise ValueError(f"No agent mapped for tool type: {tool_type}")

        self.logger.info(f"Using tool {tool_type.value} with agent {agent_type.value}")

        try:
            # Route the task to the appropriate agent
            result = await self.agent_manager.route_task(agent_type, input_data)
            return {
                "success": result.success,
                "data": result.data,
                "error": result.error,
                "confidence":confidence: result.confidence
            }
        except Exception as e:
            self.logger.error(f"Error using tool {tool_type.value}: {str(e)}")
            return {
                "success": False,
                "data": {},
                "error": str(e),
                "confidence": 0.0
            }

    async def execute_tool_chain(self, tool_sequence: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Execute a chain of tools in sequence

        Args:
            tool_sequence: List of tool configurations, each with 'type' and 'input'

        Returns:
            List of results from each tool execution
        """
        results = []
        for tool_config in tool_sequence:
            tool_type = ToolType(tool_config["type"])
            input_data = tool_config["input"]

            result = await self.use_tool(tool_type, input_data)
            results.append({
                "tool_type": tool_type.value,
                "result": result
            })

            # If a tool fails and we shouldn't continue, break
            if not result["success"] and tool_config.get("stop_on_failure", False):
                break

        return results

    async def route_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Intelligently route a request to the appropriate tool(s)

        Args:
            request: Request containing user query and context

        Returns:
            Response from the routed tool(s)
        """
        query = request.get("query", "").lower()
        context = request.get("context", {})

        # Simple routing logic - in practice this would be more sophisticated
        if any(keyword in query for keyword in ["code", "program", "function", "debug", "script"]):
            return await self.use_tool(ToolType.CODING, {
                "task": request.get("query", ""),
                "language": context.get("language", "python"),
                "requirements": context.get("requirements", [])
            })
        elif any(keyword in query for keyword in ["research", "find information", "look up", "search for"]):
            return await self.use_tool(ToolType.RESEARCH, {
                "query": request.get("query", "")
            })
        elif any(keyword in query for keyword in ["plan", "organize", "schedule", "organize", "project"]):
            return await self.use_tool(ToolType.PLANNING, {
                "goal": request.get("query", ""),
                "constraints": context.get("constraints", [])
            })
        elif any(keyword in query for keyword in ["youtube", "video", "watch", "tutorial"]):
            # Extract URL if present
            url = None
            # Simple URL extraction - in practice would be more robust
            words = query.split()
            for word in words:
                if "youtube.com" in word or "youtu.be" in word:
                    url = word
                    break

            return await self.use_tool(ToolType.YOUTUBE, {
                "url": url or request.get("query", ""),
                "action": "summarize"
            })
        elif any(keyword in query for keyword in ["document", "pdf", "file", "read", "analyze"]):
            return await self.use_tool(ToolType.DOCUMENT, {
                "file_path": context.get("file_path", ""),
                "action": "analyze"
            })
        elif any(keyword in query for keyword in ["calculate", "math", "equation", "solve", "compute"]):
            return await self.use_tool(ToolType.MATH, {
                "operation": "solve",
                "problem": request.get("query", "")
            })
        else:
            # Default to research for general questions
            return await self.use_tool(ToolType.RESEARCH, {
                "query": request.get("query", "")
            })