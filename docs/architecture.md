# Architecture

## Overview

```text
API (main.py) → Graph (graph.py) → Nodes (nodes.py) → Agents (agents.py) → LLM
                     ↓                    ↓                   ↓
              Checkpointer            Runtime            Middleware
              (memory)               (context)           (hooks)
```

**Flow:** HTTP request → route to node → execute agent → middleware chain → tools → response

## Directory Structure

```text
├── main.py                 # FastAPI endpoints
├── src/
│   ├── core/
│   │   ├── settings.py     # Environment config
│   │   ├── constants.py    # NODES list, models
│   │   ├── context.py      # RequestContext (DI)
│   │   └── middleware.py   # Middleware implementations
│   ├── agent/
│   │   ├── state.py        # State (TypedDict) + Output schema
│   │   ├── agents.py       # Agent factory (create_agent)
│   │   ├── nodes.py        # Node implementations
│   │   └── graph.py        # StateGraph compilation
│   ├── tools/
│   │   └── tools.py        # Tool definitions
│   └── prompts/
│       └── assistant.md    # System prompts
```

## Key Components

| Component  | File            | Purpose                              |
| ---------- | --------------- | ------------------------------------ |
| State      | `state.py`      | TypedDict with `messages`, `node`    |
| Agents     | `agents.py`     | `create_agent()` factory             |
| Nodes      | `nodes.py`      | Graph vertices, invoke agents        |
| Graph      | `graph.py`      | Routes requests to nodes             |
| Middleware | `middleware.py` | Hooks: logging, retry, summarization |
| Context    | `context.py`    | Request-scoped data (user_id, etc.)  |

## Memory

| Type             | Scope              | Use Case                 | Default         |
| ---------------- | ------------------ | ------------------------ | --------------- |
| **Checkpointer** | Per thread_id      | Conversation history     | `MemorySaver`   |
| **Store**        | Cross-conversation | User preferences, facts  | `InMemoryStore` |

For production, use `PostgresSaver` and `PostgresStore`.
