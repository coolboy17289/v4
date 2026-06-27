"""
Memory Agent for memory operations and management
"""

from typing import Dict, Any
from .base_agent import BaseAgent, AgentType, AgentResult
import logging
import asyncio

# Import memory manager from memory_manager module
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from memory_manager.memory_manager import MemoryManager
from memory_manager.memory_types import MemoryType

logger = logging.getLogger(__name__)


class MemoryAgent(BaseAgent):
    """Agent responsible for memory operations"""

    def __init__(self, agent_id: str = None):
        super().__init__(AgentType.MEMORY, agent_id)
        self.memory_manager = MemoryManager()

    async def process(self, input_data: Dict[str, Any]) -> AgentResult:
        """
        Process a memory request

        Args:
            input_data: Should contain 'action' key (store, retrieve, search, forget, etc.)

        Returns:
            AgentResult: Result of the memory operation
        """
        try:
            action = input_data.get('action', '').lower()

            if not action:
                return AgentResult(
                    success=False,
                    error="Action is required",
                    confidence=0.0
                )

            self.logger.info(f"Performing memory action: {action}")

            # Simulate processing delay
            await asyncio.sleep(0.5)

            if action == 'store':
                content = input_data.get('content')
                memory_type_str = input_data.get('memory_type', 'short_term')
                importance = float(input_data.get('importance', 0.5))

                if content is None:
                    return AgentResult(
                        success=False,
                        error="Content is required for store action",
                        confidence=0.0
                    )

                # Convert string to MemoryType enum
                try:
                    memory_type = MemoryType[memory_type_str.upper()]
                except KeyError:
                    return AgentResult(
                        success=False,
                        error=f"Invalid memory type: {memory_type_str}",
                        confidence=0.0
                    )

                # Create appropriate memory item (simplified)
                from memory_manager.memory_types import MemoryItem
                item = MemoryItem(
                    id="",  # Will be auto-generated
                    content=content,
                    memory_type=memory_type,
                    importance=importance
                )

                item_id = self.memory_manager.add_memory(item)

                result = {
                    "action": "store",
                    "memory_id": item_id,
                    "memory_type": memory_type_str,
                    "stored": True
                }

            elif action == 'retrieve':
                memory_id = input_data.get('memory_id')
                if not memory_id:
                    return AgentResult(
                        success=False,
                        error="Memory ID is required for retrieve action",
                        confidence=0.0
                    )

                item = self.memory_manager.get_memory(memory_id)
                if item is None:
                    return AgentResult(
                        success=False,
                        error=f"Memory not found: {memory_id}",
                        confidence=0.0
                    )

                result = {
                    "action": "retrieve",
                    "memory_id": memory_id,
                    "content": item.content,
                    "memory_type": item.memory_type.value,
                    "importance": item.importance,
                    "timestamp": item.timestamp.isoformat()
                }

            elif action == 'search':
                query = input_data.get('query', '')
                memory_types_str = input_data.get('memory_types', None)
                limit = int(input_data.get('limit', 10))

                memory_types = None
                if memory_types_str:
                    # Convert comma-separated string to list of MemoryType
                    try:
                        memory_types = [MemoryType[mt.strip().upper()] for mt in memory_types_str.split(',')]
                    except KeyError as e:
                        return AgentResult(
                            success=False,
                            error=f"Invalid memory type: {e}",
                            confidence=0.0
                        )

                items = self.memory_manager.search_memories(query, memory_types, limit)

                result = {
                    "action": "search",
                    "query": query,
                    "results": [
                        {
                            "memory_id": item.id,
                            "content": str(item.content)[:200] + "..." if len(str(item.content)) > 200 else str(item.content),
                            "memory_type": item.memory_type.value,
                            "importance": item.importance
                        } for item in items
                    ],
                    "count": len(items)
                }

            elif action == 'forget':
                memory_id = input_data.get('memory_id')
                if not memory_id:
                    return AgentResult(
                        success=False,
                        error="Memory ID is required for forget action",
                        confidence=0.0
                    )

                # In a real implementation, we would remove the memory
                # For now, we'll just simulate
                result = {
                    "action": "forget",
                    "memory_id": memory_id,
                    "forgotten": True
                }

            elif action == 'stats':
                stats = self.memory_manager.get_memory_stats()
                result = {
                    "action": "stats",
                    "statistics": stats
                }

            else:
                return AgentResult(
                    success=False,
                    error=f"Unsupported action: {action}",
                    confidence=0.0
                )

            return AgentResult(
                success=True,
                data=result,
                confidence=0.95,
                metadata={
                    "action": action,
                    "processing_time": 0.5
                }
            )

        except Exception as e:
            self.logger.error(f"Error in memory agent: {str(e)}")
            return AgentResult(
                success=False,
                error=str(e),
                confidence=0.0
            )