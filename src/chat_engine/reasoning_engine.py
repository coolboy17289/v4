"""
Reasoning Engine for handling complex reasoning and decision-making
"""

import logging
from typing import Dict, List, Any, Optional
from enum import Enum
import json

from .tool_orchestrator import ToolOrchestrator, ToolType
from .conversation_manager import ConversationManager

logger = logging.getLogger(__name__)


class ReasoningType(Enum):
    """Types of reasoning approaches"""
    CHAIN_OF_THOUGHT = "chain_of_thought"
    TREE_OF_THOUGHTS = "tree_of_thoughts"
    REFLEXION = "reflexion"
    REACT = "react"


class ReasoningEngine:
    """Handles complex reasoning and problem-solving"""

    def __init__(self, tool_orchestrator: ToolOrchestrator,
                 conversation_manager: ConversationManager):
        self.tool_orchestrator = tool_orchestrator
        self.conversation_manager = conversation_manager
        self.logger = logging.getLogger(__name__)

    async def reason(self, query: str, context: Dict[str, Any] = None,
                    reasoning_type: ReasoningType = ReasoningType.CHAIN_OF_THOUGHT) -> Dict[str, Any]:
        """
        Perform reasoning on a query

        Args:
            query: The question or problem to reason about
            context: Additional context
            reasoning_type: Type of reasoning to apply

        Returns:
            Reasoning result with answer and process
        """
        context = context or {}

        if reasoning_type == ReasoningType.CHAIN_OF_THOUGHT:
            return await self._chain_of_thought_reasoning(query, context)
        elif reasoning_type == ReasoningType.TREE_OF_THOUGHTS:
            return await self._tree_of_thoughts_reasoning(query, context)
        elif reasoning_type == ReasoningType.REFLEXION:
            return await self._reflexion_reasoning(query, context)
        elif reasoning_type == ReasoningType.REACT:
            return await self._react_reasoning(query, context)
        else:
            # Default to simple direct reasoning
            return await self._direct_reasoning(query, context)

    async def _chain_of_thought_reasoning(self, query: str,
                                        context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform chain-of-thought reasoning: break down problem into steps
        """
        self.logger.info(f"Performing chain-of-thought reasoning on: {query}")

        # Step 1: Decompose the problem
        decomposition_prompt = f"""
        Break down the following question into logical steps:
        {query}

        Provide a numbered list of steps needed to solve this problem.
        """

        decomposition_result = await self.tool_orchestrator.use_tool(
            ToolType.REASONING,  # Using reasoning tool for meta-reasoning
            {
                "task": decomposition_prompt,
                "context": context
            }
        )

        steps = []
        if decomposition_result["success"]:
            # Parse steps from result (simplified)
            steps_text = decomposition_result["data"].get("generated_text", "")
            steps = [s.strip() for s in steps_text.split('\n') if s.strip() and not s.startswith('#')]
        else:
            # Fallback: treat as single step
            steps = [query]

        # Step 2: Solve each step
        step_results = []
        accumulated_context = context.copy()

        for i, step in enumerate(steps):
            step_prompt = f"""
            Step {i+1}: {step}

            Context from previous steps:
            {json.dumps(step_results, indent=2) if step_results else 'None'}

            Additional context:
            {json.dumps(accumulated_context, indent=2)}

            Solve this step and provide your answer.
            """

            step_result = await self.tool_orchestrator.use_tool(
                ToolType.REASONING,
                {
                    "task": step_prompt,
                    "context": accumulated_context
                }
            )

            step_results.append({
                "step": step,
                "result": step_result
            })

            # Update accumulated context with this step's result
            if step_result["success"]:
                accumulated_context[f"step_{i+1}_result"] = step_result["data"]

        # Step 3: Synthesize final answer
        synthesis_prompt = f"""
        Original question: {query}

        Steps taken:
        {json.dumps([{"step": sr["step"], "success": sr["result"]["success"]} for sr in step_results], indent=2)}

        Detailed results:
        {json.dumps([sr["result"] for sr in step_results], indent=2)}

        Provide a comprehensive answer to the original question based on the reasoning steps above.
        """

        final_result = await self.tool_orchestrator.use_tool(
            ToolType.REASONING,
            {
                "task": synthesis_prompt,
                "context": accumulated_context
            }
        )

        return {
            "success": final_result["success"],
            "answer": final_result["data"].get("generated_text", "") if final_result["success"] else "",
            "reasoning_type": "chain_of_thought",
            "steps": step_results,
            "confidence": final_result.get("confidence", 0.0) if final_result["success"] else 0.0
        }

    async def _tree_of_thoughts_reasoning(self, query: str,
                                        context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform tree-of-thoughts reasoning: explore multiple reasoning paths
        """
        self.logger.info(f"Performing tree-of-thoughts reasoning on: {query}")

        # Generate multiple initial approaches
        approaches_prompt = f"""
        For the following problem, generate 3 different approaches to solve it:
        {query}

        For each approach, provide:
        1. A brief description of the approach
        2. The first step you would take
        3. What resources or tools you might need
        """

        approaches_result = await self.tool_orchestrator.use_tool(
            ToolType.REASONING,
            {
                "task": approaches_prompt,
                "context": context
            }
        )

        # For simplicity, we'll explore the first approach in depth
        # In a full implementation, we'd explore multiple paths and evaluate them
        if approaches_result["success"]:
            approach_text = approaches_result["data"].get("generated_text", "")
            # Extract first approach (simplified)
            first_approach = approach_text.split('\n\n')[0] if '\n\n' in approach_text else approach_text

            # Now do chain-of-thought on this approach
            return await self._chain_of_thought_reasoning(
                f"Using this approach: {first_approach}\n\nOriginal problem: {query}",
                context
            )
        else:
            # Fallback to chain of thought
            return await self._chain_of_thought_reasoning(query, context)

    async def _reflexion_reasoning(self, query: str,
                                 context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform reflexion: try, reflect on mistakes, and try again
        """
        self.logger.info(f"Performing reflexion reasoning on: {query}")

        max_attempts = 3
        best_result = None
        best_confidence = 0.0

        for attempt in range(max_attempts):
            self.logger.info(f"Reflexion attempt {attempt + 1}/{max_attempts}")

            # Try to solve the problem
            attempt_result = await self._chain_of_thought_reasoning(query, context)

            if attempt_result["success"]:
                confidence = attempt_result.get("confidence", 0.0)
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_result = attempt_result

                # If we're confident enough, we can stop early
                if confidence > 0.8:
                    break

            # Generate reflection on what went wrong or could be improved
            if attempt < max_attempts - 1:  # Don't reflect on the last attempt
                reflection_prompt = f"""
                Previous attempt at solving: "{query}"
                Result: {"Success" if attempt_result["success"] else "Failure"}
                Confidence: {attempt_result.get("confidence", 0.0)}

                What could be improved in the approach?
                Were there any mistaken assumptions or missing information?
                How should the strategy be adjusted for the next attempt?
                """

                reflection_result = await self.tool_orchestrator.use_tool(
                    ToolType.REASONING,
                    {
                        "task": reflection_prompt,
                        "context": {
                            **context,
                            "previous_attempt": attempt_result,
                            "attempt_number": attempt + 1
                        }
                    }
                )

                # Update context with reflection for next attempt
                if reflection_result["success"]:
                    reflection_text = reflection_result["data"].get("generated_text", "")
                    context["reflection"] = reflection_text
                    context["attempt"] = attempt + 1

        return best_result or {
            "success": False,
            "answer": "Unable to solve after multiple attempts",
            "reasoning_type": "reflexion",
            "confidence": 0.0
        }

    async def _react_reasoning(self, query: str,
                             context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform ReAct reasoning: Reason and Act in alternating steps
        """
        self.logger.info(f"Performing ReAct reasoning on: {query}")

        max_iterations = 5
        observation = f"Starting to solve: {query}"
        thought_history = []
        action_history = []

        for i in range(max_iterations):
            # Thought step: reason about what to do next
            thought_prompt = f"""
            Problem: {query}

            History:
            Thoughts: {json.dumps(thought_history, indent=2)}
            Actions: {json.dumps(action_history, indent=2)}
            Current observation: {observation}

            What should I think about next? What information do I need?
            Is there an action I should take? If so, what action and with what input?
            Provide your reasoning and conclude with either:
            - THOUGHT: [your reasoning]
            - ACTION: [action_type]: [action_input]
            - OR if finished: ANSWER: [your final answer]
            """

            thought_result = await self.tool_orchestrator.use_tool(
                ToolType.REASONING,
                {
                    "task": thought_prompt,
                    "context": context
                }
            )

            if not thought_result["success"]:
                break

            thought_text = thought_result["data"].get("generated_text", "")
            thought_history.append(thought_text)

            # Parse the thought to see if we have an action or answer
            if "ANSWER:" in thought_text:
                # Extract answer
                answer_part = thought_text.split("ANSWER:")[1].strip()
                # Clean up any extra formatting
                answer = answer_part.split('\n')[0].strip()
                return {
                    "success": True,
                    "answer": answer,
                    "reasoning_type": "react",
                    "thought_history": thought_history,
                    "action_history": action_history,
                    "confidence": 0.8  # Reasonable confidence for ReAct
                }

            if "ACTION:" in thought_text:
                # Extract action
                action_part = thought_text.split("ACTION:")[1].strip()
                action_line = action_part.split('\n')[0].strip()

                # Parse action_type and action_input
                if ":" in action_line:
                    action_type_str, action_input = action_line.split(":", 1)
                    action_type = action_type_str.strip()
                    action_input = action_input.strip()
                else:
                    action_type = action_line
                    action_input = ""

                # Map action type to tool type
                tool_mapping = {
                    "search": ToolType.RESEARCH,
                    "calculate": ToolType.MATH,
                    "lookup": ToolType.MEMORY,
                    "create": ToolType.CODING,
                    "analyze": ToolType.PLANNING
                }

                tool_type = tool_mapping.get(action_type.lower(), ToolType.RESEARCH)

                # Execute the action
                action_result = await self.tool_orchestrator.use_tool(
                    tool_type,
                    {
                        "task": action_input,
                        "context": context
                    }
                )

                observation = f"Action {action_type} with input '{action_input}' resulted in: {str(action_result)[:200]}"
                action_history.append({
                    "action": action_type,
                    "input": action_input,
                    "result": action_result
                })

                # Update context with observation
                context["last_observation"] = observation
            else:
                # Just a thought, continue to next iteration
                observation = f"After thinking: {thought_text[:100]}..."

        # If we exhausted iterations without answering
        return {
            "success": False,
            "answer": "Maximum reasoning iterations reached without conclusive answer",
            "reasoning_type": "react",
            "thought_history": thought_history,
            "action_history": action_history,
            "confidence": 0.0
        }

    async def _direct_reasoning(self, query: str,
                              context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Direct reasoning: simple one-step approach
        """
        self.logger.info(f"Performing direct reasoning on: {query}")

        result = await self.tool_orchestrator.use_tool(
            ToolType.REASONING,
            {
                "task": query,
                "context": context
            }
        )

        return {
            "success": result["success"],
            "answer": result["data"].get("generated_text", "") if result["success"] else "",
            "reasoning_type": "direct",
            "confidence": result.get("confidence", 0.0) if result["success"] else 0.0
        }