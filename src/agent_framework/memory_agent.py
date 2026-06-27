"""
Memory Agent for memory operations
"""

from typing import Dict, Any
from .base_agent import BaseAgent, AgentType, AgentResult
import logging
import asyncio
import sys
import os

# Import the memory manager from the memory_manager module
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
            input_data: Should contain 'operation' key (store, retrieve, search, forget, etc.)
                      and relevant parameters

        Returns:
            AgentResult: Result of the memory operation
        """
        try:
            operation = input_data.get('operation', '').lower()
            memory_type_str = input_data.get('memory_type', 'short_term').lower()

            # Map string to MemoryType enum
            try:
                memory_type = MemoryType[memory_type_str.upper()]
            except KeyError:
                return AgentResult(
                    success=False,
                    error=f"Invalid memory type: {memory_type_str}",
                    confidence=0.0
                )

            if not operation:
                return AgentResult(
                    success=False,
                    error="Operation is required",
                    confidence=0.0
                )

            self.logger.info(f"Performing memory operation: {operation} on {memory_type.value}")

            # Simulate processing delay
            await asyncio.sleep(0.5)

            if operation == 'store':
                content = input_data.get('content')
                importance = float(input_data.get('importance', 0.5))
                tags = input_data.get('tags', [])

                if content is None:
                    return AgentResult(
                        success=False,
                        error="Content is required for store operation",
                        confidence=0.0
                    )

                # Create appropriate memory item (simplified)
                from memory_manager.memory_types import MemoryItem
                item = MemoryItem(
                    content=content,
                    memory_type=memory_type,
                    importance=importance,
                    tags=tags
                )

                item_id = self.memory_manager.add_memory(item)

                result = {
                    "operation": "store",
                    "memory_id": item_id,
                    "memory_type": memory_type.value,
                    "stored": True
                }

            elif operation == 'retrieve':
                memory_id = input_data.get('memory_id')
                if not memory_id:
                    return AgentResult(
                        success=False,
                        error="Memory ID is required for retrieve operation",
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
                    "operation": "retrieve",
                    "memory_id": memory_id,
                    "content": item.content,
                    "memory_type": item.memory_type.value,
                    "importance": item.importance,
                    "timestamp": item.timestamp.isoformat(),
                    "access_count": item.access_count
                }

            elif operation == 'search':
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
                    "operation": "search",
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

            elif operation == 'forget':
                memory_id = input_data.get('memory_id')
                if not memory_id:
                    return AgentResult(
                        success=False,
                        error="Memory ID is required for forget operation",
                        confidence=0.0
                    )

                # In a real implementation, we would remove the memory
                # For now, we'll just simulate it
                result = {
                    "operation": "forget",
                    "memory_id": memory_id,
                    "success": True,
                    "message": f"Memory {memory_id} has been forgotten"
                }

            elif operation == 'stats':
                stats = self.memory_manager.get_memory_stats()
                result = {
                    "operation": "stats",
                    "statistics": stats
                }

            else:
                return AgentResult(
                    success=False,
                    error=f"Unsupported operation: {operation}",
                    confidence=0.0
                )

            return AgentResult(
                success=True,
                data=result,
                confidence=0.95,
                metadata={
                    "operation": operation,
                    "memory_type": memory_type.value if 'memory_type' in locals() else None,
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