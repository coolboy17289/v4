"""
Conversation Manager for handling conversation state and memory
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid

from src.memory_manager.memory_manager import MemoryManager
from src.memory_manager.memory_types import MemoryItem, MemoryType

logger = logging.getLogger(__name__)


class ConversationManager:
    """Manages conversation state, history, and memory integration"""

    def __init__(self, memory_manager: MemoryManager):
        self.memory_manager = memory_manager
        self.conversations: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger(__name__)

    def create_conversation(self, user_id: str = None) -> str:
        """
        Create a new conversation

        Args:
            user_id: Optional user identifier

        Returns:
            Conversation ID
        """
        conversation_id = str(uuid.uuid4())
        self.conversations[conversation_id] = {
            "id": conversation_id,
            "user_id": user_id,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "messages": [],
            "context": {},
            "active": True
        }
        self.logger.info(f"Created conversation {conversation_id}")
        return conversation_id

    def add_message(self, conversation_id: str, content: str,
                   message_type: str = "user", metadata: Dict[str, Any] = None) -> str:
        """
        Add a message to a conversation

        Args:
            conversation_id: ID of the conversation
            content: Message content
            message_type: Type of message (user, assistant, system)
            metadata: Additional metadata

        Returns:
            Message ID
        """
        if conversation_id not in self.conversations:
            raise ValueError(f"Conversation {conversation_id} not found")

        message_id = str(uuid.uuid4())
        message = {
            "id": message_id,
            "content": content,
            "type": message_type,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }

        self.conversations[conversation_id]["messages"].append(message)
        self.conversations[conversation_id]["updated_at"] = datetime.now()

        # Also store in memory manager for long-term retention
        memory_item = MemoryItem(
            content=content,
            memory_type=MemoryType.WORKING,
            importance=0.7 if message_type == "user" else 0.8,
            metadata={
                "conversation_id": conversation_id,
                "message_id": message_id,
                "message_type": message_type,
                **(metadata or {})
            }
        )
        self.memory_manager.add_memory(memory_item)

        self.logger.debug(f"Added message {message_id} to conversation {conversation_id}")
        return message_id

    def get_conversation_history(self, conversation_id: str,
                                limit: int = None) -> List[Dict[str, Any]]:
        """
        Get conversation history

        Args:
            conversation_id: ID of the conversation
            limit: Maximum number of messages to return

        Returns:
            List of messages
        """
        if conversation_id not in self.conversations:
            return []

        messages = self.conversations[conversation_id]["messages"]
        if limit:
            return messages[-limit:]
        return messages

    def get_conversation_context(self, conversation_id: str) -> Dict[str, Any]:
        """
        Get conversation context

        Args:
            conversation_id: ID of the conversation

        Returns:
            Context dictionary
        """
        if conversation_id not in self.conversations:
            return {}
        return self.conversations[conversation_id]["context"]

    def update_conversation_context(self, conversation_id: str,
                                   context_updates: Dict[str, Any]):
        """
        Update conversation context

        Args:
            conversation_id: ID of the conversation
            context_updates: Dictionary of updates to apply
        """
        if conversation_id not in self.conversations:
            raise ValueError(f"Conversation {conversation_id} not found")

        self.conversations[conversation_id]["context"].update(context_updates)
        self.conversations[conversation_id]["updated_at"] = datetime.now()

    def end_conversation(self, conversation_id: str):
        """
        End a conversation

        Args:
            conversation_id: ID of the conversation to end
        """
        if conversation_id in self.conversations:
            self.conversations[conversation_id]["active"] = False
            self.conversations[conversation_id]["ended_at"] = datetime.now()
            self.logger.info(f"Ended conversation {conversation_id}")

    def get_active_conversations(self, user_id: str = None) -> List[Dict[str, Any]]:
        """
        Get list of active conversations

        Args:
            user_id: Optional user ID to filter by

        Returns:
            List of conversation summaries
        """
        conversations = []
        for conv in self.conversations.values():
            if not conv["active"]:
                continue
            if user_id is not None and conv["user_id"] != user_id:
                continue
            conversations.append({
                "id": conv["id"],
                "user_id": conv["user_id"],
                "created_at": conv["created_at"].isoformat(),
                "updated_at": conv["updated_at"].isoformat(),
                "message_count": len(conv["messages"]),
                "last_message": conv["messages"][-1] if conv["messages"] else None
            })
        return conversations