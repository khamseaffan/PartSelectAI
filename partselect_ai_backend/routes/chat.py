from datetime import datetime
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from uuid import uuid4, UUID 
from langchain_core.messages import HumanMessage
from typing import List, Optional, AsyncGenerator, Dict, Any
from agents.agent import build_agent_for_session
from langchain_core.callbacks.base import AsyncCallbackHandler
import asyncio
from redis_manager import redis_manager 

chat_router = APIRouter()

# In-memory cache for agent instances (eviction strategy for production)
session_memory_cache = {}

class FastAPIStreamingHandler(AsyncCallbackHandler):
    def __init__(self, prefix: str = "Handler"):
        # self.queue = queue
        self.prefix = prefix

    async def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs: Any):
        print(f"[{self.prefix} Log] Tool Start: {serialized.get('name')}, Input: {input_str}")

    async def on_tool_end(self, output: str, **kwargs: Any):
        print(f"[{self.prefix} Log] Tool End: Output: {output[:100]}{'...' if len(output) > 100 else ''}") 


class PartReference(BaseModel):
    part_number: str
    name: str
    price: str
    url: str

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

# ChatResponse might not be needed for stream, but useful for potential non-streaming endpoint
# class ChatResponse(BaseModel):
#     response: str
#     parts: List[PartReference] = []
#     is_off_topic: bool = False
#     session_id: str

def extract_parts(text: str) -> List[PartReference]:
    import re
    part_pattern = r'\*\*(PS-\d+)\*\*\s*\((.*?)\)\s*\$(\d+\.\d+).*?\[View Part\]\((.*?)\)'
    matches = re.findall(part_pattern, text)
    return [PartReference(part_number=p, name=n, price=pr, url=u) for p, n, pr, u in matches]

def is_off_topic(text: str) -> bool:
    return ("sorry" in text.lower()
            and "refrigerator" not in text.lower()
            and "dishwasher" not in text.lower())


@chat_router.get("/stream_chat")
async def stream_chat(message: str, session_id: Optional[str] = None):
    if session_id:
        try:
            UUID(session_id, version=4)
        except ValueError:
            print(f"Invalid session_id format: {session_id}. Generating new one.")
            session_id = str(uuid4())
    else:
        session_id = str(uuid4())
        print(f"No session_id provided. Generated new one: {session_id}")

    try:
        if session_id not in session_memory_cache:
            print(f"Creating new agent for session: {session_id}")
            handler = FastAPIStreamingHandler(prefix=f"Agent-{session_id[:4]}")

            app, memory = build_agent_for_session( 
                session_id,
                callback_handler=handler 
            )

            # Store the compiled app and memory in cache
            session_memory_cache[session_id] = {
                "app": app, 
                "memory": memory,
                "handler": handler
            }
            print(f"Agent and memory cached for session: {session_id}")

            redis_update_success = redis_manager.update_session(session_id, {
                "agent_initialized": True,
                "created_at": datetime.now().isoformat(),
            })
            if not redis_update_success:
                print(f"Warning: Failed initial Redis update for session {session_id}")

        else:
            print(f"Reusing existing agent for session: {session_id}")
            app = session_memory_cache[session_id]["app"]
            handler = session_memory_cache[session_id]["handler"] 

            redis_update_success = redis_manager.update_session(session_id, {
                 # No other fields needed, just updates last_active implicitly
            })
            if not redis_update_success:
                 print(f"Warning: Failed Redis last_active update for session {session_id}")

        async def event_stream() -> AsyncGenerator[str, None]:
            """Streams events from the LangGraph app's astream_events method."""
            print(f"[Stream] Starting event stream (astream_events) for session {session_id}...")
            try:
                graph_input = {"messages": [HumanMessage(content=message)]}
                config = {
                    "configurable": {"thread_id": session_id},
                    "recursion_limit": 15,
                    "callbacks": [handler],
                }

                event_counter = 0
                async for event in app.astream_events(graph_input, config=config, version="v2"):
                    event_counter += 1
                    kind = event["event"]
                    name = event.get("name")
                    tags = event.get("tags", [])

                    if kind == "on_chat_model_stream":
                     chunk_data = event.get("data", {}).get("chunk")
                     if chunk_data and hasattr(chunk_data, 'content'):
                        token = chunk_data.content
                        if isinstance(token, str):
                            # print(f"---> Backend Yielding Token (from event): '{token}'")
                            event_data = json.dumps({
                                "type": "token",
                                "content": token, 
                                "session_id": session_id
                            })
                            yield f"data: {event_data}\n\n"
                       
                print(f"[Stream] Completed successfully (astream_events loop finished) after {event_counter} events for session {session_id}.")
                done_event = json.dumps({"type": "done", "session_id": session_id})
                yield f"data: {done_event}\n\n"

            except asyncio.CancelledError:
                 print(f"[Stream] Client disconnected for session {session_id}.")
            except Exception as e:
                print(f"[ERROR] Streaming failed for session {session_id}: {type(e).__name__} - {str(e)}")
                print(traceback.format_exc())
                error_event = json.dumps({
                    "type": "error",
                    "content": f"An error occurred during streaming: {str(e)}",
                    "session_id": session_id
                })
                yield f"data: {error_event}\n\n"


        return StreamingResponse(event_stream(), media_type="text/event-stream")

    except ConnectionError as ce:
         print(f"ERROR in /stream_chat (Redis Connection): {str(ce)}")
         raise HTTPException(status_code=503, detail=f"Service temporarily unavailable: {str(ce)}")
    except Exception as e:
        import traceback
        print(f"ERROR in /stream_chat (Setup/General): {type(e).__name__} - {str(e)}")
        print(traceback.format_exc()) # Print full traceback for debugging
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

# @chat_router.post("/stream_chat")
# async def stream_chat(request: ChatRequest):
#     try:
#         print("\n--- [Streaming Request Started] ---")
#         message = request.message
#         session_id = request.session_id or str(uuid4())
#         print(f"Incoming message: {message}")
#         print(f"Session ID: {session_id}")

#         # Create or reuse agent
#         if session_id not in session_memory_cache:
#             print(f"[Session Init] Creating new agent for session: {session_id}")
#             handler_queue = asyncio.Queue()
#             handler = FastAPIStreamingHandler(handler_queue)
#             agent, memory = build_agent_for_session(session_id, callback_handler=handler)
#             session_memory_cache[session_id] = {"agent": agent, "memory": memory}
#         else:
#             print(f"[Session Reuse] Using existing agent for session: {session_id}")
#             handler_queue = asyncio.Queue()
#             handler = FastAPIStreamingHandler(handler_queue)
#             agent = session_memory_cache[session_id]["agent"]

#         async def token_stream():
#             try:
#                 print("[Agent Invoke] Starting agent execution...")

#                 async def run_agent():
#                     await agent.ainvoke(
#                         {"messages": [{"role": "user", "content": message}]},
#                         config={
#                             "configurable": {"thread_id": session_id},
#                             "recursion_limit": 10,
#                             "callbacks": [handler],
#                         },
#                     )
#                     await handler_queue.put("[DONE]")
#                     print("[Agent Invoke] Finished agent execution.")

#                 asyncio.create_task(run_agent())

#                 while True:
#                     token = await handler_queue.get()
#                     if token == "[DONE]":
#                         print("[Stream Complete] All tokens sent.")
#                         break
#                     yield f"data: {token}\n\n"

#             except Exception as e:
#                 print(f"[ERROR] Streaming failed: {str(e)}")
#                 yield f"data: [ERROR] {str(e)}\n\n"

#         return StreamingResponse(token_stream(), media_type="text/event-stream")
#     except Exception as e:
#         print(f"ERROR in /chat: {str(e)}")
#         raise HTTPException(status_code=500, detail=str(e))

