"""
Test script for the API server
"""

import asyncio
import sys
import os
import httpx
import json

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

BASE_URL = "http://localhost:8000"

async def test_api_endpoints():
    """Test the API endpoints"""
    print("Testing API Endpoints...")

    async with httpx.AsyncClient() as client:
        # Test root endpoint
        print("\n1. Testing root endpoint...")
        response = await client.get(f"{BASE_URL}/")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")

        # Test health endpoint
        print("\n2. Testing health endpoint...")
        response = await client.get(f"{BASE_URL}/health")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")

        # Test chat endpoint
        print("\n3. Testing chat endpoint...")
        chat_data = {
            "message": "What is the capital of Japan?",
            "session_id": "test_session_1"
        }
        response = await client.post(f"{BASE_URL}/chat", json=chat_data)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   Response: {result['response'][:100]}...")
            print(f"   Confidence: {result['confidence']}")
        else:
            print(f"   Error: {response.text}")

        # Test research endpoint
        print("\n4. Testing research endpoint...")
        research_data = {
            "query": "Explain quantum computing in simple terms",
            "depth": "medium"
        }
        response = await client.post(f"{BASE_URL}/research", json=research_data)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   Summary: {result['summary'][:100]}...")
            print(f"   Confidence: {result['confidence']}")
            print(f"   Findings count: {len(result['findings'])}")
        else:
            print(f"   Error: {response.text}")

        # Test code endpoint
        print("\n5. Testing code endpoint...")
        code_data = {
            "task": "Create a function to calculate the factorial of a number",
            "language": "python"
        }
        response = await client.post(f"{BASE_URL}/code", json=code_data)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   Language: {result['language']}")
            print(f"   Code length: {len(result['code'])} characters")
            print(f"   Confidence: {result['confidence']}")
        else:
            print(f"   Error: {response.text}")

    print("\nAPI testing completed!")

if __name__ == "__main__":
    # Note: This test requires the API server to be running
    # Start the server first with: python -m src.api_server.main
    try:
        asyncio.run(test_api_endpoints())
    except Exception as e:
        print(f"Error during testing: {e}")
        print("Make sure the API server is running before running this test.")
        print("Start it with: python -m src.api_server.main")