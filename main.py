"""FastAPI server for LangGraph agent.

Provides REST API to invoke specific nodes in the graph with:
- Conversation memory (per thread_id)
- Streaming support (SSE)
- Context injection (user_id, session_id)
"""

import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from src import NODES, RequestContext, graph, logger, settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting LangGraph Agent API")
    yield
    logger.info("Shutting down")


app = FastAPI(
    title="LangGraph Agent",
    version="1.0.0",
    description="Scalable LangGraph agent template with node-based routing",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------------------------------------------------------
# Request/Response Models
# -----------------------------------------------------------------------------


class InvokeRequest(BaseModel):
    """Request to invoke a node."""

    message: str = Field(description="User message")
    node: str = Field(default="assistant", description="Node to execute")
    thread_id: str | None = Field(default=None, description="Thread ID for conversation memory")
    user_id: str | None = Field(default=None, description="User ID for context")


class InvokeResponse(BaseModel):
    """Response from invocation."""

    thread_id: str
    node: str
    response: str
    structured_response: dict | None = Field(
        default=None, description="Structured output if available"
    )


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------


@app.get("/health")
async def health():
    """Health check."""
    return {"status": "ok", "env": settings.ENV}


@app.get("/nodes")
async def list_nodes():
    """List available nodes."""
    return {"nodes": NODES}


@app.post("/invoke", response_model=InvokeResponse)
async def invoke(request: InvokeRequest):
    """Invoke a specific node.

    The node executes with the provided message and returns a response.
    Use thread_id to maintain conversation history across requests.
    """
    if request.node not in NODES:
        raise HTTPException(400, f"Unknown node: {request.node}. Available: {NODES}")

    thread_id = request.thread_id or str(uuid.uuid4())
    context = RequestContext(
        user_id=request.user_id or "",
        session_id=thread_id,
    )

    try:
        result = await graph.ainvoke(
            {
                "messages": [{"role": "user", "content": request.message}],
                "node": request.node,
            },
            {"configurable": {"thread_id": thread_id}},
            context=context,
        )

        # Extract response from messages
        messages = result.get("messages", [])
        response_text = ""
        if messages:
            last = messages[-1]
            response_text = last.content if hasattr(last, "content") else last.get("content", "")

        # Extract structured response if available
        structured = result.get("structured_response")
        structured_dict = structured.model_dump() if structured else None

        return InvokeResponse(
            thread_id=thread_id,
            node=request.node,
            response=response_text,
            structured_response=structured_dict,
        )

    except Exception as e:
        logger.error(f"Invoke error: {e}")
        raise HTTPException(500, str(e)) from e


@app.post("/stream")
async def stream(request: InvokeRequest):
    """Stream response from a node via SSE.

    Returns Server-Sent Events with token-by-token streaming.
    """
    if request.node not in NODES:
        raise HTTPException(400, f"Unknown node: {request.node}")

    thread_id = request.thread_id or str(uuid.uuid4())
    context = RequestContext(
        user_id=request.user_id or "",
        session_id=thread_id,
    )

    async def generate():
        try:
            async for event in graph.astream_events(
                {
                    "messages": [{"role": "user", "content": request.message}],
                    "node": request.node,
                },
                {"configurable": {"thread_id": thread_id}},
                version="v2",
                context=context,
            ):
                if event.get("event") == "on_chat_model_stream":
                    chunk = event.get("data", {}).get("chunk")
                    if chunk and hasattr(chunk, "content") and chunk.content:
                        yield f"data: {chunk.content}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield f"data: Error: {e}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"X-Thread-ID": thread_id, "X-Node": request.node},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
