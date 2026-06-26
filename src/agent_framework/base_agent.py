"""
Base Agent Class for the Agent Framework
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class AgentType(Enum):
    """Types of agents in the system"""
    RESEARCH = "research"
    CODING = "coding"
    PLANNING = "planning"
    FILE = "file"
    BROWSER = "browser"
    VISION = "vision"
    MEMORY = "memory"
    MATH = "math"
    AUTOMATION = "automation"


class AgentStatus(Enum):
    """Status of an agent"""
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"


@dataclass
class AgentResult:
    """Result returned by an agent"""
    success: bool
    data: Any = None
    error: str = None
    confidence: float = 0.0
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseAgent(ABC):
    """Base class for all agents in the system"""

    def __init__(self, agent_type: AgentType, agent_id: str = None):
        self.agent_type = agent_type
        self.agent_id = agent_id or f"{agent_type.value}_{id(self)}"
        self.status = AgentStatus.IDLE
        self.logger = logging.getLogger(f"{__name__}.{self.agent_id}")
        self.metadata = {}

    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> AgentResult:
        """
        Process input data and return results

        Args:
            input_data: Input data for the agent

        Returns:
            AgentResult: Result of processing
        """
        pass

    async def execute(self, input_data: Dict[str, Any]) -> AgentResult:
        """
        Execute the agent with error handling and status tracking

        Args:
            input_data: Input data for the agent

        Returns:
            AgentResult: Result of processing
        """
        try:
            self.status = AgentStatus.BUSY
            self.logger.info(f"Agent {self.agent_id} processing input")

            result = await self.process(input_data)

            self.status = AgentStatus.IDLE
            return result

        except Exception as e:
            self.status = AgentStatus.ERROR
            self.logger.error(f"Agent {self.agent_id} encountered error: {str(e)}")
            return AgentResult(
                success=False,
                error=str(e),
                confidence=0.0
            )

    def get_status(self) -> AgentStatus:
        """Get current agent status"""
        return self.status

    def get_info(self) -> Dict[str, Any]:
        """Get agent information"""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type.value,
            "status": self.status.value,
            "metadata": self.metadata
        }


"""
Agent Manager for coordinating and routing tasks to appropriate agents
"""

from typing import Dict, List, Optional, Type
from .base_agent import BaseAgent, AgentType, AgentResult
import logging
import asyncio

logger = logging.getLogger(__name__)


class AgentManager:
    """Manages agents and routes tasks to appropriate agents"""

    def __init__(self):
        self.agents: Dict[AgentType, List[BaseAgent]] = {
            agent_type: [] for agent_type in AgentType
        }
        self.logger = logging.getLogger(__name__)

    def register_agent(self, agent: BaseAgent):
        """Register an agent with the manager"""
        agent_type = agent.agent_type
        if agent_type not in self.agents:
            self.agents[agent_type] = []
        self.agents[agent_type].append(agent)
        self.logger.info(f"Registered agent {agent.agent_id} of type {agent_type.value}")

    def unregister_agent(self, agent_id: str):
        """Unregister an agent by ID"""
        for agent_type, agents in self.agents.items():
            for i, agent in enumerate(agents):
                if agent.agent_id == agent_id:
                    del agents[i]
                    self.logger.info(f"Unregistered agent {agent_id}")
                    return True
        return False

    def get_available_agents(self, agent_type: AgentType) -> List[BaseAgent]:
        """Get available agents of a specific type"""
        agents = self.agents.get(agent_type, [])
        return [agent for agent in agents if agent.get_status() == AgentType.IDLE]

    async def route_task(self, agent_type: AgentType, input_data: Dict[str, Any]) -> AgentResult:
        """
        Route a task to an available agent of the specified type

        Args:
            agent_type: Type of agent needed
            input_data: Input data for the agent

        Returns:
            AgentResult: Result from the agent
        """
        available_agents = self.get_available_agents(agent_type)

        if not available_agents:
            # If no agents are available, wait for one to become available
            # In a real implementation, we might queue the request
            return AgentResult(
                success=False,
                error=f"No available agents of type {agent_type.value}",
                confidence=0.0
            )

        # Select the first available agent (could be improved with load balancing)
        agent = available_agents[0]
        self.logger.info(f"Routing task to agent {agent.agent_id}")

        return await agent.execute(input_data)

    def get_agent_statuses(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all registered agents"""
        statuses = {}
        for agent_type, agents in self.agents.items():
            statuses[agent_type.value] = [
                agent.get_info() for agent in agents
            ]
        return statuses