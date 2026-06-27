"""
Conversation Manager for handling conversation state and memory
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
import uuid

from ..memory_manager.memory_manager import MemoryManager
from ..memory_manager.memory_types import MemoryType, MemoryItem

logger = logging.getLogger(__name__)


class ConversationManager:
    """Manages conversation state, history, and memory integration"""

    def __init__(self, memory_manager: MemoryManager):
        self.memory_manager = memory_manager
        self.conversations: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger(__name__)

    def create_conversation(self, user_id: str = None,
                          title: str = None) -> str:
        """
        Create a new conversation

        Args:
            user_id: Optional user identifier
            title: Optional conversation title

        Returns:
            Conversation ID
        """
        conversation_id = str(uuid.uuid4())
        now = datetime.now()

        self.conversations[conversation_id] = {
            "id": conversation_id,
            "user_id": user_id,
            "title": title or f"Conversation {now.strftime('%Y-%m-%d %H:%M')}",
            "created_at": now,
            "updated_at": now,
            "messages": [],
            "context": {},
            "metadata": {}
        }

        self.logger.info(f"Created conversation {conversation_id}")
        return conversation_id

    def add_message(self, conversation_id: str, role: str,
                   content: str, metadata: Dict[str, Any] = None) -> str:
        """
        Add a message to a conversation

        Args:
            conversation_id: ID of the conversation
            role: Role of the message sender (user, assistant, system)
            content: Message content
            metadata: Optional metadata

        Returns:
            Message ID
        """
        if conversation_id not in self.conversations:
            raise ValueError(f"Conversation {conversation_id} not found")

        message_id = str(uuid.uuid4())
        now = datetime.now()

        message = {
            "id": message_id,
            "role": role,
            "content": content,
            "timestamp": now.isoformat(),
            "metadata": metadata or {}
        }

        self.conversations[conversation_id]["messages"].append(message)
        self.conversations[conversation_id]["updated_at"] = now

        # Also store in long-term memory for important conversations
        if role in ["user", "assistant"]:
            self._store_in_memory(conversation_id, message_id, role, content, metadata)

        self.logger.debug(f"Added message {message_id} to conversation {conversation_id}")
        return message_id

    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a conversation by ID

        Args:
            conversation_id: ID of the conversation

        Returns:
            Conversation data or None if not found
        """
        return self.conversations.get(conversation_id)

    def get_recent_messages(self, conversation_id: str,
                          limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent messages from a conversation

        Args:
            conversation_id: ID of the conversation
            limit: Maximum number of messages to return

        Returns:
            List of recent messages
        """
        if conversation_id not in self.conversations:
            return []

        messages = self.conversations[conversation_id]["messages"]
        return messages[-limit:] if len(messages) > limit else messages

    def get_conversation_context(self, conversation_id: str) -> Dict[str, Any]:
        """
        Get conversation context for use in prompts

        Args:
            conversation_id: ID of the conversation

        Returns:
            Context dictionary
        """
        if conversation_id not in self.conversations:
            return {}

        conv = self.conversations[conversation_id]
        recent_messages = self.get_recent_messages(conversation_id, 10)

        # Build context from recent messages
        context = {
            "conversation_id": conversation_id,
            "message_count": len(conv["messages"]),
            "recent_messages": [
                {
                    "role": msg["role"],
                    "content": msg["content"][:200] + ("..." if len(msg["content"]) > 200 else ""),
                    "timestamp": msg["timestamp"]
                }
                for msg in recent_messages
            ],
            "conversation_summary": self._generate_conversation_summary(conversation_id),
            "created_at": conv["created_at"].isoformat(),
            "updated_at": conv["updated_at"].isoformat()
        }

        # Add any stored context
        context.update(conv.get("context", {}))

        return context

    def update_conversation_context(self, conversation_id: str,
                                  key: str, value: Any):
        """
        Update a specific context value

        Args:
            conversation_id: ID of the conversation
            key: Context key
            value: Context value
        """
        if conversation_id not in self.conversations:
            raise ValueError(f"Conversation {conversation_id} not found")

        if "context" not in self.conversations[conversation_id]:
            self.conversations[conversation_id]["context"] = {}

        self.conversations[conversation_id]["context"][key] = value
        self.conversations[conversation_id]["updated_at"] = datetime.now()

    def search_conversation_history(self, conversation_id: str,
                                  query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search through conversation history

        Args:
            conversation_id: ID of the conversation
            query: Search query
            limit: Maximum number of results

        Returns:
            List of matching messages
        """
        if conversation_id not in self.conversations:
            return []

        query_lower = query.lower()
        matches = []

        for message in self.conversations[conversation_id]["messages"]:
            if query_lower in message["content"].lower():
                matches.append(message)
                if len(matches) >= limit:
                    break

        return matches

    def get_conversation_stats(self, conversation_id: str) -> Dict[str, Any]:
        """
        Get statistics about a conversation

        Args:
            conversation_id: ID of the conversation

        Returns:
            Statistics dictionary
        """
        if conversation_id not in self.conversations:
            return {}

        conv = self.conversations[conversation_id]
        messages = conv["messages"]

        user_messages = [m for m in messages if m["role"] == "user"]
        assistant_messages = [m for m in messages if m["role"] == "assistant"]

        return {
            "conversation_id": conversation_id,
            "total_messages": len(messages),
            "user_messages": len(user_messages),
            "assistant_messages": len(assistant_messages),
            "duration_minutes": (conv["updated_at"] - conv["created_at"]).total_seconds() / 60,
            "created_at": conv["created_at"].isoformat(),
            "updated_at": conv["updated_at"].isoformat()
        }

    def end_conversation(self, conversation_id: str):
        """
        Mark a conversation as ended (optional cleanup)

        Args:
            conversation_id: ID of the conversation
        """
        if conversation_id in self.conversations:
            self.conversations[conversation_id]["ended_at"] = datetime.now()
            self.conversations[conversation_id]["status"] = "ended"
            self.logger.info(f"Ended conversation {conversation_id}")

    def _store_in_memory(self, conversation_id: str, message_id: str,
                        role: str, content: str, metadata: Dict[str, Any] = None):
        """
        Store a message in the long-term memory system

        Args:
            conversation_id: ID of the conversation
            message_id: ID of the message
            role: Role of the message sender
            content: Message content
            metadata: Optional metadata
        """
        try:
            memory_item = MemoryItem(
                content=content,
                memory_type=MemoryType.SHORT_TERM,
                importance=0.6 if role == "user" else 0.7,  # Assistant messages slightly more important
                tags=[role, "conversation", conversation_id],
                metadata={
                    "conversation_id": conversation_id,
                    "message_id": message_id,
                    "role": role,
                    "timestamp": datetime.now().isoformat(),
                    **(metadata or {})
                }
            )

            self.memory_manager.add_memory(memory_item)
            self.logger.debug(f"Stored message {message_id} in memory")

        except Exception as e:
            self.logger.warning(f"Failed to store message in memory: {str(e)}")

    def _generate_conversation_summary(self, conversation_id: str) -> str:
        """
        Generate a summary of the conversation

        Args:
            conversation_id: ID of the conversation

        Returns:
            Summary string
        """
        if conversation_id not in self.conversations:
            return ""

        conv = self.conversations[conversation_id]
        messages = conv["messages"]

        if not messages:
            return "Empty conversation"

        # Simple summarization: first and last user messages
        user_messages = [m for m in messages if m["role"] == "user"]
        if not user_messages:
            return "No user messages"

        first_user = user_messages[0]["content"][:100]
        last_user = user_messages[-1]["content"][:100] if len(user_messages) > 1 else first_user

        return f"Conversation started with: '{first_user}...' and ended with: '{last_user}...' ({len(user_messages)} user exchanges)"