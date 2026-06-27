"""
Math Agent for mathematical computations and problem solving
"""

from typing import Dict, Any
from .base_agent import BaseAgent, AgentType, AgentResult
import logging
import asyncio
import re

logger = logging.getLogger(__name__)


class MathAgent(BaseAgent):
    """Agent responsible for mathematical operations"""

    def __init__(self, agent_id: str = None):
        super().__init__(AgentType.MATH, agent_id)

    async def process(self, input_data: Dict[str, Any]) -> AgentResult:
        """
        Process a math request

        Args:
            input_data: Should contain 'problem' key describing the mathematical problem
                      or 'expression' for direct evaluation
                      Optional: 'operation_type' for specific operations

        Returns:
            AgentResult: Result of the mathematical operation
        """
        try:
            problem = input_data.get('problem', '')
            expression = input_data.get('expression', '')
            operation_type = input_data.get('operation_type', '').lower()

            if not problem and not expression:
                return AgentResult(
                    success=False,
                    error="Either problem or expression must be provided",
                    confidence=0.0
                )

            self.logger.info(f"Processing math problem: {problem or expression}")

            # Simulate processing delay
            await asyncio.sleep(1.0)

            # If expression is provided, try to evaluate it directly
            if expression:
                try:
                    # Note: In a real application, you would use a safe eval or a math library
                    # For demonstration, we'll use a very restricted eval or just return a placeholder
                    # WARNING: Never use eval on untrusted input in production!
                    # This is just for demonstration in this controlled environment
                    result_value = eval(expression, {"__builtins__": {}}, {
                        "abs": abs, "max": max, "min": min, "round": round,
                        "sum": sum, "len": len, "pow": pow
                    })
                    result = {
                        "operation": "evaluate",
                        "expression": expression,
                        "result": result_value
                    }
                except Exception as e:
                    result = {
                        "operation": "evaluate",
                        "expression": expression,
                        "error": f"Could not evaluate expression: {str(e)}",
                        "result": None
                    }
            else:
                # Process the problem description
                # This is a simplified version - in reality, you'd use a math-solving model
                problem_lower = problem.lower()

                # Simple pattern matching for demonstration
                if "derivative" in problem_lower or "differentiate" in problem_lower:
                    # Extract function if possible
                    func_match = re.search(r'of\s+([^.\s]+)', problem)
                    function = func_match.group(1) if func_match else "f(x)"
                    result = {
                        "operation": "differentiate",
                        "problem": problem,
                        "result": f"d/dx [{function}] = 2*x (derivative result (simulated)",
                        "explanation": "This is a simulated derivative calculation."
                    }
                elif "integral" in problem_lower or "integrate" in problem_lower:
                    func_match = re.search(r'of\s+([^.\s]+)', problem)
                    function = func_match.group(1) if func_match else "f(x)"
                    result = {
                        "operation": "integrate",
                        "problem": problem,
                        "result": f"∫[{function}]dx = integral result (simulated) + C",
                        "explanation": "This is a simulated integral calculation."
                    }
                elif "solve" in problem_lower and "equation" in problem_lower:
                    result = {
                        "operation": "solve_equation",
                        "problem": problem,
                        "result": "x = 2, x = -3 (simulated solution)",
                        "explanation": "This is a simulated equation solving."
                    }
                elif "matrix" in problem_lower:
                    result = {
                        "operation": "matrix_operation",
                        "problem": problem,
                        "result": "Matrix operation result (simulated)",
                        "explanation": "This is a simulated matrix operation."
                    }
                else:
                    # Default to basic arithmetic if it looks like a calculation
                    # Extract numbers and operators
                    numbers = re.findall(r'-?\d+\.?\d*', problem)
                    if len(numbers) >= 2:
                        # Very simple: just add the first two numbers
                        try:
                            num1 = float(numbers[0])
                            num2 = float(numbers[1])
                            result_value = num1 + num2
                            result = {
                                "operation": "addition",
                                "problem": problem,
                                "result": f"{num1} + {num2} = {result_value}",
                                "explanation": "Simple addition of first two numbers found."
                            }
                        except ValueError:
                            result = {
                                "operation": "unknown",
                                "problem": problem,
                                "result": "Could not process the mathematical problem.",
                                "explanation": "The problem could not be interpreted."
                            }
                    else:
                        result = {
                            "operation": "unknown",
                            "problem": problem,
                            "result": "Could not process the mathematical problem.",
                            "explanation": "The problem could not be interpreted."
                        }

            return AgentResult(
                success=True,
                data=result,
                confidence=0.85,
                metadata={
                    "operation_type": operation_type,
                    "processing_time": 1.0
                }
            )

        except Exception as e:
            self.logger.error(f"Error in math agent: {str(e)}")
            return AgentResult(
                success=False,
                error=str(e),
                confidence=0.0
            )