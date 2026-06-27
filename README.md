# AI Assistant Project

A state-of-the-art AI assistant featuring an advanced agent framework with specialized agents for research, coding, planning, and more.

## Current Implementation Status

### Core Components Completed:
1. **Agent Framework** (`src/agent_framework/`)
   - BaseAgent class with lifecycle management
   - AgentManager for routing tasks to appropriate agents
   - Specialized agents:
     - ResearchAgent: For conducting research tasks
     - CodingAgent: For writing and debugging code
     - PlanningAgent: For breaking down complex tasks into steps
   - Agent status tracking (IDLE, BUSY, ERROR, OFFLINE)

2. **API Server** (`src/api_server/`)
   - FastAPI-based REST API
   - WebSocket support for real-time communication
   - Endpoints:
     - `GET /`: Health check
     - `GET /health`: Detailed health status
     - `POST /chat`: Main chat endpoint
     - `POST /research`: Dedicated research endpoint
     - `POST /code`: Dedicated code generation endpoint
     - `WS /ws/{session_id}`: WebSocket endpoint

3. **Supporting Infrastructure**
   - Basic project structure with all planned modules
   - Requirements files for dependencies
   - Docker configuration for containerization
   - Startup scripts

### Key Features Implemented:
- **Dynamic Agent Routing**: Tasks are automatically routed to the most appropriate specialist agent
- **Async Processing**: All agents operate asynchronously for better performance
- **Confidence Scoring**: Agents provide confidence scores with their results
- **Metadata Tracking**: Detailed metadata about processing time, resources used, etc.
- **Extensible Design**: Easy to add new agent types and capabilities
- **RESTful API**: Clean, well-documented API endpoints
- **WebSocket Support**: Real-time bidirectional communication

### How to Run:

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Start the API server:
   ```bash
   python start.py
   ```
   or
   ```bash
   uvicorn src.api_server.main:app --host 0.0.0.0 --port 8000 --reload
   ```

3. Access the API:
   - Main endpoint: http://localhost:8000
   - API docs: http://localhost:8000/docs
   - Alternative docs: http://localhost:8000/redoc

### Testing:

Run the basic tests to verify functionality:
```bash
python test_basic.py    # Test agent framework
python test_api.py      # Test API endpoints (requires server running)
```

### Example Usage:

**Research Request:**
```bash
curl -X POST "http://localhost:8000/research" \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the benefits of renewable energy?", "depth": "medium"}'
```

**Code Generation Request:**
```bash
curl -X POST "http://localhost:8000/code" \
  -H "Content-Type: application/json" \
  -d '{"task": "Create a function to check if a number is prime", "language": "python"}'
```

**Chat Request:**
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Explain quantum computing in simple terms", "session_id": "chat_001"}'
```

## Future Development

This implementation provides a solid foundation for the full AI assistant vision. Planned enhancements include:

1. **Additional Agents**:
   - File Agent: File system operations
   - Browser Agent: Web automation
   - Vision Agent: Image and document understanding
   - Memory Agent: Advanced memory management
   - Math Agent: Mathematical problem solving
   - And more...

2. **Advanced Features**:
   - Self-improvement loop with critic and refinement
   - Multi-model collaboration
   - Knowledge graph integration
   - Workflow builder
   - Plugin system
   - Memory hierarchy (short-term, long-term, etc.)
   - Model routing optimization
   - Continuous learning system

3. **Infrastructure Improvements**:
   - Database integration (PostgreSQL, Redis)
   - Vector database for RAG (FAISS/Qdrant)
   - Comprehensive testing suite
   - Performance monitoring and optimization
   - Security enhancements
   - Deployment orchestration (Kubernetes)

## License

MIT License - see LICENSE file for details