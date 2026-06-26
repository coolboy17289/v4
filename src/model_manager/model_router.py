"""
Model Router for directing requests to appropriate models based on task type
"""

from enum import Enum
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class TaskType(Enum):
    """Types of tasks that determine model routing"""
    CHAT = "chat"
    CODING = "coding"
    REASONING = "reasoning"
    CREATIVE_WRITING = "creative_writing"
    TECHNICAL_WRITING = "technical_writing"
    MATH = "math"
    ANALYSIS = "analysis"
    TRANSLATION = "translation"
    SUMMARIZATION = "summarization"
    QUESTION_ANSWERING = "question_answering"
    CODE_COMPLETION = "code_completion"
    CODE_REVIEW = "code_review"
    DEBUGGING = "debugging"
    PLANNING = "planning"
    RESEARCH = "research"


class ModelRole(Enum):
    """Roles that models can specialize in"""
    GENERAL = "general"
    CODE = "code"
    REASONING = "reasoning"
    CREATIVE = "creative"
    TECHNICAL = "technical"
    MATH = "math"
    PLANNING = "planning"
    RESEARCH = "research"


class ModelRouter:
    """Routes tasks to appropriate models based on task type"""

    def __init__(self):
        # Mapping of task types to preferred model roles
        self.task_to_role_map = {
            TaskType.CHAT: ModelRole.GENERAL,
            TaskType.CODING: ModelRole.CODE,
            TaskType.REASONING: ModelRole.REASONING,
            TaskType.CREATIVE_WRITING: ModelRole.CREATIVE,
            TaskType.TECHNICAL_WRITING: ModelRole.TECHNICAL,
            TaskType.MATH: ModelRole.MATH,
            TaskType.ANALYSIS: ModelRole.REASONING,
            TaskType.TRANSLATION: ModelRole.GENERAL,
            TaskType.SUMMARIZATION: ModelRole.GENERAL,
            TaskType.QUESTION_ANSWERING: ModelRole.GENERAL,
            TaskType.CODE_COMPLETION: ModelRole.CODE,
            TaskType.CODE_REVIEW: ModelRole.CODE,
            TaskType.DEBUGGING: ModelRole.CODE,
            TaskType.PLANNING: ModelRole.PLANNING,
            TaskType.RESEARCH: ModelRole.RESEARCH
        }

        # Default model configurations (would be loaded from config in practice)
        self.model_configs = {
            ModelRole.GENERAL: {
                "model_name": "microsoft/DialoGPT-large",
                "max_length": 2048,
                "temperature": 0.7
            },
            ModelRole.CODE: {
                "model_name": "microsoft/CodeBERT-base",
                "max_length": 2048,
                "temperature": 0.2
            },
            ModelRole.REASONING: {
                "model_name": "microsoft/DialoGPT-large",
                "max_length": 4096,
                "temperature": 0.5
            },
            ModelRole.CREATIVE: {
                "model_name": "gpt2-large",
                "max_length": 2048,
                "temperature": 0.9
            },
            ModelRole.TECHNICAL: {
                "model_name": "microsoft/DialoGPT-medium",
                "max_length": 2048,
                "temperature": 0.3
            },
            ModelRole.MATH: {
                "model_name": "microsoft/DialoGPT-medium",
                "max_length": 2048,
                "temperature": 0.1
            },
            ModelRole.PLANNING: {
                "model_name": "microsoft/DialoGPT-large",
                "max_length": 4096,
                "temperature": 0.6
            },
            ModelRole.RESEARCH: {
                "model_name": "microsoft/DialoGPT-large",
                "max_length": 4096,
                "temperature": 0.5
            }
        }

    def route_task(self, task_type: TaskType) -> ModelRole:
        """
        Determine the appropriate model role for a given task type

        Args:
            task_type: The type of task to be performed

        Returns:
            ModelRole: The recommended model role for this task
        """
        return self.task_to_role_map.get(task_type, ModelRole.GENERAL)

    def get_model_config(self, role: ModelRole) -> Dict[str, Any]:
        """
        Get configuration for a specific model role

        Args:
            role: The model role to get configuration for

        Returns:
            Dict containing model configuration
        """
        return self.model_configs.get(role, self.model_configs[ModelRole.GENERAL])

    def get_model_for_task(self, task_type: TaskType) -> Dict[str, Any]:
        """
        Get model configuration for a specific task type

        Args:
            task_type: The type of task

        Returns:
            Dict containing model configuration for the task
        """
        role = self.route_task(task_type)
        return self.get_model_config(role)


# Global router instance
model_router = ModelRouter()