# LangChain-LangGraph Agent Template

A production-ready template for building AI agents with LangChain and LangGraph. Features a modular architecture with pluggable middleware, tool runtime access, conversation memory, and a FastAPI server with streaming support.

## Quick Start

```bash
uv sync
cp .env.example .env  # Add OPENAI_API_KEY
uv run uvicorn main:app --reload --port 8000
```

## API

```bash
# Invoke
curl -X POST http://localhost:8000/invoke \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "node": "assistant"}'

# Stream
curl -X POST http://localhost:8000/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "node": "assistant"}'

# List nodes
curl http://localhost:8000/nodes
```

## Project Structure

```text
├── main.py              # FastAPI server
├── src/
│   ├── core/            # Settings, context, middleware
│   ├── agent/           # State, agents, nodes, graph
│   ├── tools/           # Tool definitions
│   └── prompts/         # System prompts
└── docs/
    ├── architecture.md  # System design
    └── guide.md         # Developer guide
```

## Adding Agents

1. Add to `NODES` list in `src/core/constants.py`
2. Create agent in `src/agent/agents.py`
3. Create node in `src/agent/nodes.py`
4. Create prompt at `src/prompts/{name}.md`

See [guide.md](docs/guide.md) for details.

## Environment

```bash
OPENAI_API_KEY=sk-...           # Required
ENV=LOCAL                        # LOCAL, DEV, PROD
ENABLE_SUMMARIZATION=true        # Auto-summarize conversations
ENABLE_RETRY=false               # Retry failed LLM calls
ENABLE_LOGGING=false             # Log requests/responses
```

## Docker

```bash
docker build -t langgraph-agent .
docker run -p 8000:8000 --env-file .env langgraph-agent
```
