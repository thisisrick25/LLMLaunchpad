"""Chat API routes for LLMLaunchpad.

Provides chat completion endpoints with SSE streaming support,
using either local llama-server or cloud LiteLLM routing.
"""

import json
import uuid
import asyncio
import logging
import time
from datetime import datetime
from typing import Optional, List, Dict, Any, AsyncIterator, Tuple

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ..llama import get_llama_server, LlamaServerState
from ..litellm import get_litellm_client, is_litellm_available, get_cloud_model
from ..config import get_config
from ..database import get_connection

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


# Request/Response models

class Message(BaseModel):
    """A chat message."""
    role: str  # user, assistant, system
    content: str


class ChatRequest(BaseModel):
    """Request for chat completion."""
    messages: List[Message]
    conversation_id: Optional[str] = None
    model: Optional[str] = None  # For cloud routing
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    stream: bool = True


class ChatResponse(BaseModel):
    """Response from chat completion."""
    id: str
    conversation_id: str
    content: str
    model: str
    finish_reason: str
    usage: Optional[Dict[str, int]] = None


# Helper functions

def generate_title(first_message: str, max_length: int = 50) -> str:
    """Generate a conversation title from the first message."""
    # Take first line or sentence
    title = first_message.split("\n")[0]
    if "." in title:
        title = title.split(".")[0] + "."
    
    # Truncate if too long
    if len(title) > max_length:
        title = title[:max_length - 3] + "..."
    
    return title.strip()


def save_message(
    conversation_id: str,
    role: str,
    content: str,
    model: Optional[str] = None,
) -> str:
    """Save a message to the database."""
    conn = get_connection()
    cursor = conn.cursor()
    
    message_id = str(uuid.uuid4())
    
    # Check if conversation exists
    cursor.execute(
        "SELECT id FROM conversations WHERE id = ?",
        (conversation_id,)
    )
    
    if not cursor.fetchone():
        # Create new conversation
        title = generate_title(content) if role == "user" else "New Conversation"
        cursor.execute(
            """
            INSERT INTO conversations (id, title, model, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (conversation_id, title, model, datetime.utcnow(), datetime.utcnow())
        )
    else:
        # Update conversation timestamp
        cursor.execute(
            "UPDATE conversations SET updated_at = ? WHERE id = ?",
            (datetime.utcnow(), conversation_id)
        )
    
    # Insert message
    cursor.execute(
        """
        INSERT INTO messages (id, conversation_id, role, content, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (message_id, conversation_id, role, content, datetime.utcnow())
    )
    
    # Update FTS index
    cursor.execute(
        """
        INSERT INTO messages_fts (rowid, content)
        VALUES (last_insert_rowid(), ?)
        """,
        (content,)
    )
    
    conn.commit()
    conn.close()
    
    return message_id


async def stream_local_completion(
    messages: List[Dict[str, str]],
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
) -> AsyncIterator[str]:
    """Stream completion from local llama-server."""
    import httpx
    
    server = get_llama_server()
    api_url = server.get_api_url()
    
    if not api_url:
        raise RuntimeError("llama-server is not running")
    
    # Convert to llama.cpp format
    request_data = {
        "messages": messages,
        "temperature": temperature,
        "stream": True,
    }
    
    if max_tokens:
        request_data["n_predict"] = max_tokens
    
    async with httpx.AsyncClient() as client:
        async with client.stream(
            "POST",
            f"{api_url}/v1/chat/completions",
            json=request_data,
            timeout=300.0,
        ) as response:
            if response.status_code != 200:
                error_text = await response.aread()
                raise RuntimeError(f"llama-server error: {error_text.decode()}")
            
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    
                    try:
                        chunk = json.loads(data)
                        if chunk.get("choices") and chunk["choices"][0].get("delta", {}).get("content"):
                            yield chunk["choices"][0]["delta"]["content"]
                    except json.JSONDecodeError:
                        continue


async def stream_cloud_completion(
    model: str,
    messages: List[Dict[str, str]],
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
) -> AsyncIterator[str]:
    """Stream completion from cloud via LiteLLM."""
    client = get_litellm_client()
    
    async for chunk in client.chat_completion_stream(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    ):
        yield chunk


async def get_local_completion(
    messages: List[Dict[str, str]],
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
) -> Dict[str, Any]:
    """Get non-streaming completion from local llama-server."""
    import httpx
    
    server = get_llama_server()
    api_url = server.get_api_url()
    
    if not api_url:
        raise RuntimeError("llama-server is not running")
    
    request_data = {
        "messages": messages,
        "temperature": temperature,
        "stream": False,
    }
    
    if max_tokens:
        request_data["n_predict"] = max_tokens
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{api_url}/v1/chat/completions",
                json=request_data,
                timeout=300.0,
            )
            
            if response.status_code != 200:
                error_text = response.text
                raise RuntimeError(f"llama-server error: {error_text}")
            
            result = response.json()
            # Validate that the response has the expected structure
            if not isinstance(result, dict) or "choices" not in result:
                raise RuntimeError(f"Invalid response format from llama-server: {result}")
            if not result["choices"] or not isinstance(result["choices"], list):
                raise RuntimeError(f"Invalid choices format from llama-server: {result.get('choices')}")
            return result
        except httpx.TimeoutException:
            raise RuntimeError("Timeout connecting to llama-server")
        except httpx.ConnectError:
            raise RuntimeError("Failed to connect to llama-server")
        except httpx.RequestError as e:
            raise RuntimeError(f"Request to llama-server failed: {str(e)}")


# Routes

@router.post("/completions")
async def chat_completions(request: ChatRequest):
    """
    Generate a chat completion.
    
    If stream=True, returns Server-Sent Events.
    If stream=False, returns the full response.
    
    Uses local llama-server by default. If a cloud model is specified
    or the local server is not running and cloud mode is enabled,
    routes through LiteLLM.
    """
    config = get_config()
    server = get_llama_server()
    
    # Determine which backend to use
    use_cloud = False
    cloud_model = None
    
    if request.model:
        # Check if this is a cloud model
        cloud_model = get_cloud_model(request.model)
        if cloud_model:
            use_cloud = True
    
    if not use_cloud and server.state != LlamaServerState.RUNNING:
        if config.mode == "cloud" and config.litellm_enabled:
            use_cloud = True
            # Use default cloud model
            cloud_model = get_cloud_model("gpt-4o-mini")
        else:
            raise HTTPException(
                status_code=503,
                detail="llama-server is not running. Start the server or enable cloud mode."
            )
    
    if use_cloud and not is_litellm_available():
        raise HTTPException(
            status_code=503,
            detail="Cloud model requested but LiteLLM is not installed."
        )
    
    # Convert messages to dict format
    messages = [{"role": m.role, "content": m.content} for m in request.messages]
    
    # Generate or use conversation ID
    conversation_id = request.conversation_id or str(uuid.uuid4())
    
    # Save user message
    if request.messages:
        last_user_msg = next(
            (m for m in reversed(request.messages) if m.role == "user"),
            None
        )
        if last_user_msg:
            save_message(
                conversation_id,
                "user",
                last_user_msg.content,
                model=request.model or "local",
            )
    
    if request.stream:
        # Streaming response
        async def event_generator():
            full_response = []
            
            try:
                if use_cloud and cloud_model:
                    stream = stream_cloud_completion(
                        model=cloud_model.model_id,
                        messages=messages,
                        temperature=request.temperature,
                        max_tokens=request.max_tokens,
                    )
                else:
                    stream = stream_local_completion(
                        messages=messages,
                        temperature=request.temperature,
                        max_tokens=request.max_tokens,
                    )
                
                async for chunk in stream:
                    full_response.append(chunk)
                    yield f"data: {json.dumps({'content': chunk, 'conversation_id': conversation_id})}\n\n"
                
                # Save assistant response
                if full_response:
                    save_message(
                        conversation_id,
                        "assistant",
                        "".join(full_response),
                    )
                
                yield f"data: {json.dumps({'done': True, 'conversation_id': conversation_id})}\n\n"
                
            except Exception as e:
                logger.error(f"Chat completion error: {e}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )
    else:
        # Non-streaming response
        try:
            if use_cloud and cloud_model:
                client = get_litellm_client()
                response = await client.chat_completion(
                    model=cloud_model.model_id,
                    messages=messages,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens,
                    stream=False,
                )
                # Safely extract content from LiteLLM response
                if (isinstance(response, dict) and 
                    "choices" in response and 
                    isinstance(response["choices"], list) and 
                    len(response["choices"]) > 0 and
                    isinstance(response["choices"][0], dict) and
                    "message" in response["choices"][0] and
                    isinstance(response["choices"][0]["message"], dict) and
                    "content" in response["choices"][0]["message"]):
                    content = response["choices"][0]["message"]["content"]
                else:
                    raise RuntimeError(f"Invalid response format from LiteLLM: {response}")
                model_name = cloud_model.model_id
            else:
                response = await get_local_completion(
                    messages=messages,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens,
                )
                # Safely extract content from llama-server response
                if (isinstance(response, dict) and 
                    "choices" in response and 
                    isinstance(response["choices"], list) and 
                    len(response["choices"]) > 0 and
                    isinstance(response["choices"][0], dict) and
                    "message" in response["choices"][0] and
                    isinstance(response["choices"][0]["message"], dict) and
                    "content" in response["choices"][0]["message"]):
                    content = response["choices"][0]["message"]["content"]
                else:
                    raise RuntimeError(f"Invalid response format from llama-server: {response}")
                model_name = "local"
            
            # Save assistant response
            save_message(conversation_id, "assistant", content)
            
            return ChatResponse(
                id=str(uuid.uuid4()),
                conversation_id=conversation_id,
                content=content,
                model=model_name,
                finish_reason="stop",
                usage=response.get("usage"),
            )
            
        except Exception as e:
            logger.error(f"Chat completion error: {e}")
            raise HTTPException(status_code=500, detail=str(e))


@router.get("/models")
async def get_chat_models():
    """
    Get available models for chat.
    
    Returns both local models (if server is running) and cloud models.
    """
    from ..models import get_local_models
    from ..litellm import get_available_cloud_models
    
    server = get_llama_server()
    config = get_config()
    
    models = {
        "local": {
            "available": server.state == LlamaServerState.RUNNING,
            "current_model": server.get_status().model_name,
        },
        "cloud": {
            "available": config.litellm_enabled and is_litellm_available(),
            "models": [m.to_dict() for m in get_available_cloud_models()],
        },
    }
    
    return models


@router.post("/abort")
async def abort_generation():
    """
    Abort the current generation.
    
    This is a best-effort operation - streaming may have already completed.
    """
    # For now, this is a no-op since we don't track active generations
    # In a more sophisticated implementation, we'd track and cancel active streams
    return {"status": "abort_requested"}
