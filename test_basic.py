"""
Basic test to verify the agent framework is working
"""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from agent_framework.agent_manager import AgentManager
from agent_framework import (
    ResearchAgent, CodingAgent, PlanningAgent, FileAgent,
    BrowserAgent, VisionAgent, MemoryAgent, MathAgent, AutomationAgent,
    AgentType
)


async def test_agent_framework():
    """Test the basic agent framework functionality"""
    print("Testing Agent Framework...")

    # Create agent manager
    manager = AgentManager()

    # Create all agents
    agents = [
        ("research_001", ResearchAgent("research_001")),
        ("coding_001", CodingAgent("coding_001")),
        ("planning_001", PlanningAgent("planning_001")),
        ("file_001", FileAgent("file_001")),
        ("browser_001", BrowserAgent("browser_001")),
        ("vision_001", VisionAgent("vision_001")),
        ("memory_001", MemoryAgent("memory_001")),
        ("math_001", MathAgent("math_001")),
        ("automation_001", AutomationAgent("automation_001"))
    ]

    # Register agents
    for agent_id, agent in agents:
        manager.register_agent(agent)

    print(f"Registered agents: {len(manager.get_agent_statuses())} types")

    # Test research agent
    print("\nTesting Research Agent...")
    research_result = await manager.route_task(
        agent_type=AgentType.RESEARCH,
        input_data={"query": "What is the capital of France?"}
    )

    if research_result.success:
        print(f"Research successful: {research_result.data['summary']}")
    else:
        print(f"Research failed: {research_result.error}")

    # Test coding agent
    print("\nTesting Coding Agent...")
    coding_result = await manager.route_task(
        agent_type=AgentType.CODING,
        input_data={"task": "Create a function to calculate factorial", "language": "python"}
    )

    if coding_result.success:
        print(f"Coding successful: Generated {len(coding_result.data['code'].split())} words of code")
    else:
        print(f"Coding failed: {coding_result.error}")

    # Test planning agent
    print("\nTesting Planning Agent...")
    planning_result = await manager.route_task(
        agent_type=AgentType.PLANNING,
        input_data={"goal": "Learn to play guitar"}
    )

    if planning_result.success:
        print(f"Planning successful: Generated {len(planning_result.data['plan_steps'])} step plan")
    else:
        print(f"Planning failed: {planning_result.error}")

    # Test file agent
    print("\nTesting File Agent...")
    file_result = await manager.route_task(
        agent_type=AgentType.FILE,
        input_data={"operation": "read", "path": "/tmp/test.txt"}
    )

    if file_result.success:
        print(f"File operation successful: {file_result.data.get('content', 'No content')[:50]}...")
    else:
        print(f"File operation failed: {file_result.error}")

    # Test browser agent
    print("\nTesting Browser Agent...")
    browser_result = await manager.route_task(
        agent_type=AgentType.BROWSER,
        input_data={"action": "search", "query": "latest AI news"}
    )

    if browser_result.success:
        print(f"Browser search successful: Found {browser_result.data.get('total_results', 0)} results")
    else:
        print(f"Browser search failed: {browser_result.error}")

    # Test vision agent
    print("\nTesting Vision Agent...")
    vision_result = await manager.route_task(
        agent_type=AgentType.VISION,
        input_data={"action": "describe", "image_data": "fake_image_data"}
    )

    if vision_result.success:
        print(f"Vision description successful: {vision_result.data.get('description', 'No description')}")
    else:
        print(f"Vision description failed: {vision_result.error}")

    # Test memory agent
    print("\nTesting Memory Agent...")
    memory_result = await manager.route_task(
        agent_type=AgentType.MEMORY,
        input_data={"operation": "store", "content": "This is a test memory", "memory_type": "short_term"}
    )

    if memory_result.success:
        print(f"Memory storage successful: Stored with ID {memory_result.data.get('memory_id')}")
    else:
        print(f"Memory storage failed: {memory_result.error}")

    # Test math agent
    print("\nTesting Math Agent...")
    math_result = await manager.route_task(
        agent_type=AgentType.MATH,
        input_data={"problem": "What is the derivative of x^2?"}
    )

    if math_result.success:
        print(f"Math solution successful: {math_result.data.get('result', 'No result')}")
    else:
        print(f"Math solution failed: {math_result.error}")

    # Test automation agent
    print("\nTesting Automation Agent...")
    automation_result = await manager.route_task(
        agent_type=AgentType.AUTOMATION,
        input_data={"action": "click", "target": "submit_button"}
    )

    if automation_result.success:
        print(f"Automation successful: {automation_result.data.get('message', 'No message')}")
    else:
        print(f"Automation failed: {automation_result.error}")

    print("\nAgent Framework test completed!")


if __name__ == "__main__":
    asyncio.run(test_agent_framework())