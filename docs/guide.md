# Developer Guide

## Quick Start

```bash
uv sync
cp .env.example .env  # Add OPENAI_API_KEY
uv run uvicorn main:app --reload --port 8000
```

## Adding a New Agent

### 1. Register node in `src/core/constants.py`

```python
NODES: list[str] = [
    "assistant",
    "researcher",  # new
]
```

### 2. Create agent in `src/agent/agents.py`

```python
def researcher(self):
    return create_agent(
        model=get_llm(),
        tools=[search_web],
        state_schema=State,
        system_prompt=load_prompt("researcher"),
        response_format=Output,
        middleware=DEFAULT_MIDDLEWARE,
        context_schema=RequestContext,
    )
```

### 3. Create node in `src/agent/nodes.py`

```python
async def researcher(self, state: State, runtime: Runtime[RequestContext]) -> dict:
    context = runtime.context or RequestContext()
    agent = agents.researcher()
    return await agent.ainvoke(state, context=context)
```

### 4. Create prompt at `src/prompts/researcher.md`

Done. The graph auto-registers nodes from the `NODES` list.

---

## Creating Tools

### Basic

```python
@tool
def get_weather(location: str) -> str:
    """Get weather for a location."""
    return f"Weather in {location}: Sunny"
```

### With Runtime Access

```python
@tool
def user_data(runtime: ToolRuntime[RequestContext]) -> str:
    """Access context, state, store. Runtime is hidden from model."""
    return f"User: {runtime.context.user_id}"
```

### Updating State

```python
@tool
def save_note(content: str, runtime: ToolRuntime) -> Command:
    """Return Command to update state."""
    return Command(update={
        "messages": [ToolMessage(content="Saved", tool_call_id=runtime.tool_call_id)],
        "notes": runtime.state.get("notes", []) + [content],
    })
```

---

## Middleware

### Built-in (in `DEFAULT_MIDDLEWARE`)

- `SummarizationMiddleware` - Auto-summarize long conversations
- `logging_middleware` - Log LLM requests/responses
- `retry_middleware` - Retry failed calls with backoff
- `tool_error_middleware` - Graceful tool error handling

### Custom

```python
@wrap_model_call
def my_middleware(request, handler):
    # Pre-process
    response = handler(request)
    # Post-process
    return response

@dynamic_prompt
def custom_prompt(request: ModelRequest) -> str | None:
    """Return str to override prompt, None to keep default."""
    if request.runtime.context.user_role == "admin":
        return "You have admin access."
    return None
```

---

## Deployment

```bash
docker build -t langgraph-agent .
docker run -p 8000:8000 --env-file .env langgraph-agent
```

### Production Checklist

- [ ] Set `ENV=PROD`
- [ ] Replace `MemorySaver` → `PostgresSaver`
- [ ] Replace `InMemoryStore` → `PostgresStore`
- [ ] Enable LangSmith tracing
- [ ] Add authentication
