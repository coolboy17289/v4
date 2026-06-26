"""
Basic test to verify the agent framework is working
"""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from agent_framework.agent_manager import AgentManager
from agent_framework.research_agent import ResearchAgent
from agent_framework.coding_agent import CodingAgent
from agent_framework.planning_agent import PlanningAgent


async def test_agent_framework():
    """Test the basic agent framework functionality"""
    print("Testing Agent Framework...")

    # Create agent manager
    manager = AgentManager()

    # Create agents
    research_agent = ResearchAgent("research_001")
    coding_agent = CodingAgent("coding_001")
    planning_agent = PlanningAgent("planning_001")

    # Register agents
    manager.register_agent(research_agent)
    manager.register_agent(coding_agent)
    manager.register_agent(planning_agent)

    print(f"Registered agents: {len(manager.get_agent_statuses())} types")

    # Test research agent
    print("\nTesting Research Agent...")
    research_result = await manager.route_task(
        agent_type="research",
        input_data={"query": "What is the capital of France?"}
    )

    if research_result.success:
        print(f"Research successful: {research_result.data['summary']}")
    else:
        print(f"Research failed: {research_result.error}")

    # Test coding agent
    print("\nTesting Coding Agent...")
    coding_result = await manager.route_task(
        agent_type="coding",
        input_data={"task": "Create a function to calculate factorial", "language": "python"}
    )

    if coding_result.success:
        print(f"Coding successful: Generated {len(coding_result.data['code'].split())} words of code")
    else:
        print(f"Coding failed: {coding_result.error}")

    # Test planning agent
    print("\nTesting Planning Agent...")
    planning_result = await manager.route_task(
        agent_type="planning",
        input_data={"goal": "Learn to play guitar"}
    )

    if planning_result.success:
        print(f"Planning successful: Generated {len(planning_result.data['plan_steps'])} step plan")
    else:
        print(f"Planning failed: {planning_result.error}")

    print("\nAgent Framework test completed!")


if __name__ == "__main__":
    asyncio.run(test_agent_framework())