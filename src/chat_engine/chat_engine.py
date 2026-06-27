"""
Main Chat Engine that orchestrates conversation, reasoning, and tool usage
"""

import logging
from typing import Dict, List, Any, Optional
import asyncio
from datetime import datetime

from .conversation_manager import ConversationManager
from .tool_orchestrator import ToolOrchestrator
from .reasoning_engine import ReasoningEngine, ReasoningType
from ..agent_framework.agent_manager import AgentManager
from ..memory_manager.memory_manager import MemoryManager

logger = logging.getLogger(__name__)


class ChatEngine:
    """
    Main chat engine that orchestrates all components of the AI assistant
    """

    def __init__(self, agent_manager: AgentManager, memory_manager: MemoryManager):
        self.agent_manager = agent_manager
        self.memory_manager = memory_manager

        # Initialize sub-components
        self.conversation_manager = ConversationManager(memory_manager)
        self.tool_orchestrator = ToolOrchestrator(agent_manager)
        self.reasoning_engine = ReasoningEngine(
            self.tool_orchestrator,
            self.conversation_manager
        )

        self.logger = logging.getLogger(__name__)
        self.logger.info("ChatEngine initialized")

    async def process_message(self, user_id: str, message: str,
                            conversation_id: str = None,
                            context: Dict[str, Any] = None,
                            reasoning_type: str = "auto") -> Dict[str, Any]:
        """
        Process a user message and generate a response

        Args:
            user_id: ID of the user
            message: User's message
            conversation_id: Optional existing conversation ID
            context: Additional context
            reasoning_type: Type of reasoning to use ("auto", "chain_of_thought", "tree_of_thoughts", etc.)

        Returns:
            Response dictionary with answer and metadata
        """
        try:
            self.logger.info(f"Processing message from user {user_id}")

            # Get or create conversation
            if conversation_id is None or conversation_id not in self.conversation_manager.conversations:
                conversation_id = self.conversation_manager.create_conversation(
                    user_id=user_id,
                    title=f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                )
                self.logger.info(f"Created new conversation {conversation_id} for user {user_id}")

            # Add user message to conversation
            user_message_id = self.conversation_manager.add_message(
                conversation_id=conversation_id,
                role="user",
                content=message,
                metadata={"timestamp": datetime.now().isoformat()}
            )

            # Get conversation context for enhanced understanding
            conv_context = self.conversation_manager.get_conversation_context(conversation_id)
            enhanced_context = {
                **(context or {}),
                **conv_context
            }

            # Determine reasoning type based on message content if set to auto
            if reasoning_type == "auto":
                reasoning_type = self._determine_reasoning_type(message)

            # Process the message through reasoning engine
            reasoning_result = await self.reasoning_engine.reason(
                query=message,
                context=enhanced_context,
                reasoning_type=ReasoningType(reasoning_type) if reasoning_type in [e.value for e in ReasoningType] else ReasoningType.CHAIN_OF_THOUGHT
            )

            # Generate final response
            response_text = self._generate_response(message, reasoning_result, enhanced_context)

            # Add assistant message to conversation
            assistant_message_id = self.conversation_manager.add_message(
                conversation_id=conversation_id,
                role="assistant",
                content=response_text,
                metadata={
                    "timestamp": datetime.now().isoformat(),
                    "reasoning_type": reasoning_type,
                    "confidence": reasoning_result.get("confidence", 0.0)
                }
            )

            # Update conversation context with any learned information
            self._update_conversation_context_from_result(conversation_id, reasoning_result)

            return {
                "success": True,
                "response": response_text,
                "conversation_id": conversation_id,
                "user_message_id": user_message_id,
                "assistant_message_id": assistant_message_id,
                "reasoning_type": reasoning_type,
                "confidence": reasoning_result.get("confidence", 0.0),
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "processing_details": reasoning_result
                }
            }

        except Exception as e:
            self.logger.error(f"Error processing message: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "response": "I apologize, but I encountered an error while processing your request. Please try again.",
                "conversation_id": conversation_id
            }

    def _determine_reasoning_type(self, message: str) -> str:
        """
        Determine the appropriate reasoning type based on the message content

        Args:
            message: User's message

        Args:
            message: User's message

        Returns:
            Reasoning type string
        """
        message_lower = message.lower()

        # Complex problem-solving tasks
        if any(word in message_lower for word in [
            "solve", "calculate", "compute", "prove", "derive", "figure out",
            "how to", "steps", "method", "approach", "solution"
        ]):
            return "chain_of_thought"

        # Creative or design tasks
        if any(word in message_lower for word in [
            "design", "create", "invent", "brainstorm", "ideas", "options",
            "alternatives", "different ways", "various"
        ]):
            return "tree_of_thoughts"

        # Reflective or improvement tasks
        if any(word in message_lower for word in [
            "improve", "better", "optimize", "refine", "enhance", "fix",
            "mistake", "error", "wrong", "incorrect"
        ]):
            return "reflexion"

        # Interactive or step-by-step tasks
        if any(word in message_lower for word in [
            "first", "then", "next", "after", "step", "stage", "phase",
            "interact", "act", "do", "try"
        ]):
            return "react"

        # Default to chain of thought for most queries
        return "chain_of_thought"

    def _generate_response(self, user_message: str,
                         reasoning_result: Dict[str, Any],
                         context: Dict[str, Any]) -> str:
        """
        Generate the final response based on reasoning results

        Args:
            user_message: Original user message
            reasoning_result: Result from reasoning engine
            context: Conversation context

        Returns:
            Final response string
        """
        if not reasoning_result.get("success", False):
            # Handle unsuccessful reasoning
            error_msg = reasoning_result.get("error", "Unknown error")
            return f"I encountered some difficulty processing your request: {error_msg}. Let me try a different approach or clarify what you're asking."

        answer = reasoning_result.get("answer", "").strip()
        if not answer:
            return "I've thought about your question, but I'm not able to provide a specific answer at the moment. Could you rephrase or provide more context?"

        # Enhance the answer with reasoning process if requested or appropriate
        reasoning_type = reasoning_result.get("reasoning_type", "")
        confidence = reasoning_result.get("confidence", 0.0)

        # For now, just return the answer directly
        # In a more advanced version, we might include reasoning steps for certain query types
        return answer

    def _update_conversation_context_from_result(self, conversation_id: str,
                                               reasoning_result: Dict[str, Any]):
        """
        Update conversation context based on reasoning results

        Args:
            conversation_id: ID of the conversation
            reasoning_result: Result from reasoning engine
        """
        # Store any learned facts or conclusions in conversation context
        if reasoning_result.get("success", False):
            # Extract key information from reasoning steps if available
            steps = reasoning_result.get("steps", [])
            if steps:
                # Store summary of reasoning process
                self.conversation_manager.update_conversation_context(
                    conversation_id,
                    "last_reasoning_type",
                    reasoning_result.get("reasoning_type", "unknown")
                )
                self.conversation_manager.update_conversation_context(
                    conversation_id,
                    "last_confidence",
                    reasoning_result.get("confidence", 0.0)
                )

    def get_conversation_history(self, conversation_id: str,
                               limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get conversation history

        Args:
            conversation_id: ID of the conversation
            limit: Maximum number of messages to return

        Returns:
            List of messages
        """
        return self.conversation_manager.get_recent_messages(conversation_id, limit)

    def end_conversation(self, conversation_id: str):
        """
        End a conversation

        Args:
            conversation_id: ID of the conversation to end
        """
        self.conversation_manager.end_conversation(conversation_id)

    def get_active_conversations(self, user_id: str = None) -> List[Dict[str, Any]]:
        """
        Get list of active conversations

        Args:
            user_id: Optional user ID to filter by

        Returns:
            List of conversation summaries
        """
        return self.conversation_manager.get_active_conversations(user_id)