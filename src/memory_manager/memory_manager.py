"""
Memory Manager for handling the multi-layer memory system
"""

from typing import Dict, List, Any, Optional
from .memory_types import (
    MemoryType, MemoryItem, SensoryMemoryItem, WorkingMemoryItem,
    ShortTermMemoryItem, LongTermMemoryItem, KnowledgeMemoryItem,
    SkillMemoryItem, PreferenceMemoryItem, ProjectMemoryItem
)
import logging
from datetime import datetime, timedelta
import heapq

logger = logging.getLogger(__name__)


class MemoryManager:
    """Manages the multi-layer memory system"""

    def __init__(self):
        # Initialize memory stores for each type
        self.memory_stores: Dict[MemoryType, List[MemoryItem]] = {
            memory_type: [] for memory_type in MemoryType
        }

        # Configuration for each memory type
        self.config = {
            MemoryType.SENSORY: {
                "max_items": 1000,
                "retention_time": timedelta(seconds=5),  # Very short-term
                "importance_threshold": 0.1
            },
            MemoryType.WORKING: {
                "max_items": 100,
                "retention_time": timedelta(minutes=30),
                "importance_threshold": 0.3
            },
            MemoryType.SHORT_TERM: {
                "max_items": 1000,
                "retention_time": timedelta(days=1),
                "importance_threshold": 0.4
            },
            MemoryType.LONG_TERM: {
                "max_items": 10000,
                "retention_time": timedelta(days=365),
                "importance_threshold": 0.6
            },
            MemoryType.KNOWLEDGE: {
                "max_items": 50000,
                "retention_time": timedelta(days=365*10),  # 10 years
                "importance_threshold": 0.7
            },
            MemoryType.SKILL: {
                "max_items": 1000,
                "retention_time": timedelta(days=365*5),  # 5 years
                "importance_threshold": 0.5
            },
            MemoryType.PREFERENCE: {
                "max_items": 500,
                "retention_time": timedelta(days=365*2),  # 2 years
                "importance_threshold": 0.6
            },
            MemoryType.PROJECT: {
                "max_items": 5000,
                "retention_time": timedelta(days=365*2),  # 2 years
                "importance_threshold": 0.5
            }
        }

        self.logger = logging.getLogger(__name__)

    def add_memory(self, item: MemoryItem) -> str:
        """
        Add an item to memory

        Args:
            item: MemoryItem to store

        Returns:
            str: ID of the stored item
        """
        try:
            # Add to appropriate memory store
            memory_type = item.memory_type
            self.memory_stores[memory_type].append(item)

            # Enforce limits
            self._enforce_limits(memory_type)

            self.logger.debug(f"Added {memory_type.value} memory item: {item.id}")
            return item.id

        except Exception as e:
            self.logger.error(f"Error adding memory: {str(e)}")
            raise

    def get_memory(self, memory_id: str) -> Optional[MemoryItem]:
        """
        Retrieve a memory item by ID

        Args:
            memory_id: ID of the memory item to retrieve

        Returns:
            MemoryItem if found, None otherwise
        """
        try:
            # Search all memory stores
            for memory_type, store in self.memory_stores.items():
                for item in store:
                    if item.id == memory_id:
                        item.access()  # Update access tracking
                        return item
            return None
        except Exception as e:
            self.logger.error(f"Error retrieving memory: {str(e)}")
            return None

    def get_memories_by_type(self, memory_type: MemoryType, limit: int = None) -> List[MemoryItem]:
        """
        Get memories of a specific type

        Args:
            memory_type: Type of memory to retrieve
            limit: Maximum number of items to return (None for all)

        Returns:
            List of MemoryItems of the specified type
        """
        try:
            store = self.memory_stores.get(memory_type, [])
            # Update access times for returned items
            result = []
            for item in store:
                item.access()
                result.append(item)

            # Sort by importance and recency
            result.sort(key=lambda x: (x.importance, x.timestamp), reverse=True)

            if limit is not None:
                return result[:limit]
            return result
        except Exception as e:
            self.logger.error(f"Error retrieving memories by type: {str(e)}")
            return []

    def search_memories(self, query: str, memory_types: List[MemoryType] = None,
                       limit: int = 10) -> List[MemoryItem]:
        """
        Search for memories matching a query

        Args:
            query: Search query string
            memory_types: List of memory types to search (None for all)
            limit: Maximum number of results to return

        Returns:
            List of matching MemoryItems
        """
        try:
            if memory_types is None:
                memory_types = list(MemoryType)

            results = []
            query_lower = query.lower()

            for memory_type in memory_types:
                store = self.memory_stores.get(memory_type, [])
                for item in store:
                    # Simple text matching - in reality would use embeddings
                    if isinstance(item.content, str) and query_lower in item.content.lower():
                        item.access()
                        results.append(item)
                    elif isinstance(item.content, dict):
                        # Search in dict values
                        found = False
                        for value in item.content.values():
                            if isinstance(value, str) and query_lower in value.lower():
                                found = True
                                break
                        if found:
                            item.access()
                            results.append(item)

            # Sort by importance and recency
            results.sort(key=lambda x: (x.importance, x.timestamp), reverse=True)

            if limit is not None:
                return results[:limit]
            return results
        except Exception as e:
            self.logger.error(f"Error searching memories: {str(e)}")
            return []

    def consolidate_memory(self, source_type: MemoryType, target_type: MemoryType,
                          importance_threshold: float = 0.7) -> int:
        """
        Consolidate memories from one type to another (e.g., short-term to long-term)

        Args:
            source_type: Memory type to consolidate from
            target_type: Memory type to consolidate to
            importance_threshold: Minimum importance for consolidation

        Returns:
            Number of items consolidated
        """
        try:
            source_store = self.memory_stores.get(source_type, [])
            consolidated_count = 0

            # Find items to consolidate
            to_consolidate = [
                item for item in source_store
                if item.importance >= importance_threshold
            ]

            # Move items to target store
            for item in to_consolidate:
                # Create a copy for the target type
                if target_type == MemoryType.LONG_TERM:
                    new_item = LongTermMemoryItem(
                        id=str(item.id),
                        content=item.content,
                        memory_type=target_type,
                        timestamp=item.timestamp,
                        importance=item.importance,
                        access_count=item.access_count,
                        last_accessed=item.last_accessed,
                        metadata=item.metadata.copy(),
                        tags=item.tags.copy(),
                        consolidation_date=datetime.now(),
                        source_memory_ids=[item.id]
                    )
                else:
                    # For other types, create a generic memory item
                    new_item = MemoryItem(
                        id=str(item.id),
                        content=item.content,
                        memory_type=target_type,
                        timestamp=item.timestamp,
                        importance=item.importance,
                        access_count=item.access_count,
                        last_accessed=item.last_accessed,
                        metadata=item.metadata.copy(),
                        tags=item.tags.copy()
                    )

                self.memory_stores[target_type].append(new_item)
                consolidated_count += 1

            # Remove consolidated items from source (if moving, not copying)
            # In a real system, we might keep copies in both places
            # For now, we'll keep them in source as well

            self.logger.info(f"Consolidated {consolidated_count} items from {source_type.value} to {target_type.value}")
            return consolidated_count

        except Exception as e:
            self.logger.error(f"Error consolidating memory: {str(e)}")
            return 0

    def forget_old_memories(self, memory_type: MemoryType = None) -> int:
        """
        Forget memories that are past their retention time

        Args:
            memory_type: Specific memory type to clean (None for all)

        Returns:
            Number of items forgotten
        """
        try:
            if memory_type is None:
                memory_types = list(MemoryType)
            else:
                memory_types = [memory_type]

            forgotten_count = 0
            now = datetime.now()

            for mem_type in memory_types:
                config = self.config.get(mem_type, {})
                retention_time = config.get("retention_time", timedelta(days=1))

                store = self.memory_stores.get(mem_type, [])
                remaining = []

                for item in store:
                    age = now - item.timestamp
                    if age > retention_time:
                        forgotten_count += 1
                    else:
                        remaining.append(item)

                self.memory_stores[mem_type] = remaining

            self.logger.info(f"Forgot {forgotten_count} old memory items")
            return forgotten_count

        except Exception as e:
            self.logger.error(f"Error forgetting old memories: {str(e)}")
            return 0

    def _enforce_limits(self, memory_type: MemoryType):
        """Enforce maximum item limits for a memory type"""
        config = self.config.get(memory_type, {})
        max_items = config.get("max_items", 1000)

        store = self.memory_stores.get(memory_type, [])
        if len(store) > max_items:
            # Sort by importance and recency, keep the most important/recent
            store.sort(key=lambda x: (x.importance, x.timestamp), reverse=True)
            self.memory_stores[memory_type] = store[:max_items]

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get statistics about memory usage"""
        try:
            stats = {}
            total_items = 0

            for memory_type, store in self.memory_stores.items():
                count = len(store)
                total_items += count
                stats[memory_type.value] = {
                    "count": count,
                    "max_items": self.config.get(memory_type, {}).get("max_items", 0),
                    "usage_percent": (count / max(self.config.get(memory_type, {}).get("max_items", 1), 1)) * 100
                }

            stats["total_items"] = total_items
            return stats
        except Exception as e:
            self.logger.error(f"Error getting memory stats: {str(e)}")
            return {}