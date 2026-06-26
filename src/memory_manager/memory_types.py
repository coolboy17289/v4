"""
Memory Type Definitions for the Multi-Layer Memory System
"""

from enum import Enum
from dataclasses import dataclass
from typing import Any, Optional, Dict, List
from datetime import datetime
import uuid


class MemoryType(Enum):
    """Types of memory in the system"""
    SENSORY = "sensory"          # Ultra-short-term sensory buffer
    WORKING = "working"          # Active conversation context
    SHORT_TERM = "short_term"    # Recent interactions (hours)
    LONG_TERM = "long_term"      # User-consolidated knowledge (weeks/months)
    KNOWLEDGE = "knowledge"      # Curated factual knowledge (persistent)
    SKILL = "skill"              # Learned procedures and competencies
    PREFERENCE = "preference"    # User preferences and behavior patterns
    PROJECT = "project"          # Project-specific context and knowledge


@dataclass
class MemoryItem:
    """Base class for items stored in memory"""
    id: str
    content: Any
    memory_type: MemoryType
    timestamp: datetime
    importance: float = 0.5  # 0.0 to 1.0
    access_count: int = 0
    last_accessed: datetime = None
    metadata: Dict[str, Any] = None
    tags: List[str] = None

    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid.uuid4())
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.last_accessed is None:
            self.last_accessed = self.timestamp
        if self.metadata is None:
            self.metadata = {}
        if self.tags is None:
            self.tags = []

    def access(self):
        """Record an access to this memory item"""
        self.access_count += 1
        self.last_accessed = datetime.now()


@dataclass
class SensoryMemoryItem(MemoryItem):
    """Sensory memory - raw sensory input"""
    sensory_modality: str = "unknown"  # visual, auditory, etc.
    raw_data: Any = None

    def __post_init__(self):
        super().__post_init__()
        if self.memory_type != MemoryType.SENSORY:
            self.memory_type = MemoryType.SENSORY


@dataclass
class WorkingMemoryItem(MemoryItem):
    """Working memory - active conversation context"""
    context_id: str = None  # Links to conversation/session
    sequence_number: int = 0

    def __post_init__(self):
        super().__post_init__()
        if self.memory_type != MemoryType.WORKING:
            self.memory_type = MemoryType.WORKING


@dataclass
class ShortTermMemoryItem(MemoryItem):
    """Short-term memory - recent interactions"""
    session_id: str = None
    importance_decay: float = 0.1  # How fast importance decays over time

    def __post_init__(self):
        super().__post_init__()
        if self.memory_type != MemoryType.SHORT_TERM:
            self.memory_type = MemoryType.SHORT_TERM


@dataclass
class LongTermMemoryItem(MemoryItem):
    """Long-term memory - consolidated knowledge"""
    consolidation_date: datetime = None
    source_memory_ids: List[str] = None  # IDs of memories that contributed to this

    def __post_init__(self):
        super().__post_init__()
        if self.memory_type != MemoryType.LONG_TERM:
            self.memory_type = MemoryType.LONG_TERM
        if self.consolidation_date is None:
            self.consolidation_date = datetime.now()
        if self.source_memory_ids is None:
            self.source_memory_ids = []


@dataclass
class KnowledgeMemoryItem(MemoryItem):
    """Knowledge memory - curated factual knowledge"""
    source: str = None  # Where this knowledge came from
    confidence: float = 0.8  # Confidence in this knowledge
    verified: bool = False

    def __post_init__(self):
        super().__post_init__()
        if self.memory_type != MemoryType.KNOWLEDGE:
            self.memory_type = MemoryType.KNOWLEDGE


@dataclass
class SkillMemoryItem(MemoryItem):
    """Skill memory - learned procedures"""
    skill_type: str = None  # Type of skill (coding, reasoning, etc.)
    proficiency_level: float = 0.0  # 0.0 to 1.0
    practice_count: int = 0

    def __post_init__(self):
        super().__post_init__()
        if self.memory_type != MemoryType.SKILL:
            self.memory_type = MemoryType.SKILL


@dataclass
class PreferenceMemoryItem(MemoryItem):
    """Preference memory - user preferences"""
    preference_category: str = None  # e.g., "communication_style", "topics"
    preference_value: Any = None
    confidence: float = 0.8  # Confidence in this preference

    def __post_init__(self):
        super().__post_init__()
        if self.memory_type != MemoryType.PREFERENCE:
            self.memory_type = MemoryType.PREFERENCE


@dataclass
class ProjectMemoryItem(MemoryItem):
    """Project memory - project-specific context"""
    project_id: str = None
    project_name: str = None
    relevance_score: float = 0.5  # How relevant to current project

    def __post_init__(self):
        super().__post_init__()
        if self.memory_type != MemoryType.PROJECT:
            self.memory_type = MemoryType.PROJECT