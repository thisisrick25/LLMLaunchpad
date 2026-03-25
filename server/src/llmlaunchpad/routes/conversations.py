"""Conversation history API routes for LLMLaunchpad.

Provides CRUD operations for conversations and messages,
including full-text search and export functionality.
"""

import json
import uuid
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel

from ..database import get_connection

router = APIRouter(prefix="/conversations", tags=["conversations"])


# Request/Response models

class ConversationSummary(BaseModel):
    """Summary of a conversation."""
    id: str
    title: str
    model: Optional[str]
    created_at: str
    updated_at: str
    message_count: int


class MessageResponse(BaseModel):
    """A message in a conversation."""
    id: str
    role: str
    content: str
    created_at: str


class ConversationDetail(BaseModel):
    """Full conversation with messages."""
    id: str
    title: str
    model: Optional[str]
    created_at: str
    updated_at: str
    messages: List[MessageResponse]


class UpdateTitleRequest(BaseModel):
    """Request to update conversation title."""
    title: str


class SearchResult(BaseModel):
    """A search result."""
    conversation_id: str
    conversation_title: str
    message_id: str
    content: str
    role: str
    created_at: str


# Routes

@router.get("", response_model=List[ConversationSummary])
@router.get("/", response_model=List[ConversationSummary])
async def list_conversations(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """
    List all conversations, ordered by most recent first.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        """
        SELECT 
            c.id,
            c.title,
            c.model,
            c.created_at,
            c.updated_at,
            COUNT(m.id) as message_count
        FROM conversations c
        LEFT JOIN messages m ON c.id = m.conversation_id
        GROUP BY c.id
        ORDER BY c.updated_at DESC
        LIMIT ? OFFSET ?
        """,
        (limit, offset)
    )
    
    conversations = []
    for row in cursor.fetchall():
        conversations.append(ConversationSummary(
            id=row["id"],
            title=row["title"] or "Untitled",
            model=row["model"],
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
            message_count=row["message_count"],
        ))
    
    conn.close()
    return conversations


@router.get("/count")
async def get_conversation_count():
    """Get total number of conversations."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as count FROM conversations")
    count = cursor.fetchone()["count"]
    
    conn.close()
    return {"count": count}


@router.get("/search", response_model=List[SearchResult])
async def search_conversations(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
):
    """
    Search conversations using full-text search.
    
    Searches message content and returns matching messages with context.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Use FTS5 for search
    cursor.execute(
        """
        SELECT 
            m.id as message_id,
            m.conversation_id,
            m.role,
            m.content,
            m.created_at,
            c.title as conversation_title
        FROM messages m
        JOIN conversations c ON m.conversation_id = c.id
        WHERE m.rowid IN (
            SELECT rowid FROM messages_fts WHERE messages_fts MATCH ?
        )
        ORDER BY m.created_at DESC
        LIMIT ?
        """,
        (q, limit)
    )
    
    results = []
    for row in cursor.fetchall():
        results.append(SearchResult(
            conversation_id=row["conversation_id"],
            conversation_title=row["conversation_title"] or "Untitled",
            message_id=row["message_id"],
            content=row["content"],
            role=row["role"],
            created_at=str(row["created_at"]),
        ))
    
    conn.close()
    return results


@router.get("/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(conversation_id: str):
    """Get a conversation with all its messages."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get conversation
    cursor.execute(
        "SELECT * FROM conversations WHERE id = ?",
        (conversation_id,)
    )
    conv = cursor.fetchone()
    
    if not conv:
        conn.close()
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Get messages
    cursor.execute(
        """
        SELECT id, role, content, created_at
        FROM messages
        WHERE conversation_id = ?
        ORDER BY created_at ASC
        """,
        (conversation_id,)
    )
    
    messages = [
        MessageResponse(
            id=row["id"],
            role=row["role"],
            content=row["content"],
            created_at=str(row["created_at"]),
        )
        for row in cursor.fetchall()
    ]
    
    conn.close()
    
    return ConversationDetail(
        id=conv["id"],
        title=conv["title"] or "Untitled",
        model=conv["model"],
        created_at=str(conv["created_at"]),
        updated_at=str(conv["updated_at"]),
        messages=messages,
    )


@router.patch("/{conversation_id}")
async def update_conversation(conversation_id: str, request: UpdateTitleRequest):
    """Update a conversation's title."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT id FROM conversations WHERE id = ?",
        (conversation_id,)
    )
    
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    cursor.execute(
        """
        UPDATE conversations 
        SET title = ?, updated_at = ?
        WHERE id = ?
        """,
        (request.title, datetime.utcnow(), conversation_id)
    )
    
    conn.commit()
    conn.close()
    
    return {"status": "updated", "title": request.title}


@router.delete("/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a conversation and all its messages."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT id FROM conversations WHERE id = ?",
        (conversation_id,)
    )
    
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Delete messages first (FTS entries will be orphaned but that's OK)
    cursor.execute(
        "DELETE FROM messages WHERE conversation_id = ?",
        (conversation_id,)
    )
    
    cursor.execute(
        "DELETE FROM conversations WHERE id = ?",
        (conversation_id,)
    )
    
    conn.commit()
    conn.close()
    
    return {"status": "deleted"}


@router.delete("")
@router.delete("/")
async def delete_all_conversations():
    """
    Delete all conversations.
    
    Use with caution - this is irreversible!
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM messages")
    cursor.execute("DELETE FROM conversations")
    
    conn.commit()
    conn.close()
    
    return {"status": "all_deleted"}


@router.get("/{conversation_id}/export/json")
async def export_conversation_json(conversation_id: str):
    """Export a conversation as JSON."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get conversation
    cursor.execute(
        "SELECT * FROM conversations WHERE id = ?",
        (conversation_id,)
    )
    conv = cursor.fetchone()
    
    if not conv:
        conn.close()
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Get messages
    cursor.execute(
        """
        SELECT role, content, created_at
        FROM messages
        WHERE conversation_id = ?
        ORDER BY created_at ASC
        """,
        (conversation_id,)
    )
    
    messages = [
        {
            "role": row["role"],
            "content": row["content"],
            "timestamp": str(row["created_at"]),
        }
        for row in cursor.fetchall()
    ]
    
    conn.close()
    
    export_data = {
        "id": conv["id"],
        "title": conv["title"],
        "model": conv["model"],
        "created_at": str(conv["created_at"]),
        "updated_at": str(conv["updated_at"]),
        "messages": messages,
        "exported_at": datetime.utcnow().isoformat(),
        "export_source": "LLMLaunchpad",
    }
    
    return Response(
        content=json.dumps(export_data, indent=2),
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="conversation-{conversation_id[:8]}.json"'
        },
    )


@router.get("/{conversation_id}/export/markdown")
async def export_conversation_markdown(conversation_id: str):
    """Export a conversation as Markdown."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get conversation
    cursor.execute(
        "SELECT * FROM conversations WHERE id = ?",
        (conversation_id,)
    )
    conv = cursor.fetchone()
    
    if not conv:
        conn.close()
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Get messages
    cursor.execute(
        """
        SELECT role, content, created_at
        FROM messages
        WHERE conversation_id = ?
        ORDER BY created_at ASC
        """,
        (conversation_id,)
    )
    
    messages = cursor.fetchall()
    conn.close()
    
    # Build markdown
    title = conv["title"] or "Untitled Conversation"
    lines = [
        f"# {title}",
        "",
        f"**Model:** {conv['model'] or 'Unknown'}",
        f"**Date:** {conv['created_at']}",
        "",
        "---",
        "",
    ]
    
    for msg in messages:
        role = msg["role"].capitalize()
        content = msg["content"]
        
        if msg["role"] == "user":
            lines.append(f"## User")
        elif msg["role"] == "assistant":
            lines.append(f"## Assistant")
        else:
            lines.append(f"## {role}")
        
        lines.append("")
        lines.append(content)
        lines.append("")
        lines.append("---")
        lines.append("")
    
    markdown = "\n".join(lines)
    
    return Response(
        content=markdown,
        media_type="text/markdown",
        headers={
            "Content-Disposition": f'attachment; filename="conversation-{conversation_id[:8]}.md"'
        },
    )


@router.post("/import")
async def import_conversation(data: dict):
    """
    Import a conversation from JSON.
    
    Expected format:
    {
        "title": "...",
        "model": "...",
        "messages": [
            {"role": "user", "content": "..."},
            {"role": "assistant", "content": "..."}
        ]
    }
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    conversation_id = str(uuid.uuid4())
    title = data.get("title", "Imported Conversation")
    model = data.get("model")
    messages = data.get("messages", [])
    
    if not messages:
        raise HTTPException(status_code=400, detail="No messages to import")
    
    now = datetime.utcnow()
    
    # Create conversation
    cursor.execute(
        """
        INSERT INTO conversations (id, title, model, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (conversation_id, title, model, now, now)
    )
    
    # Insert messages
    for msg in messages:
        message_id = str(uuid.uuid4())
        cursor.execute(
            """
            INSERT INTO messages (id, conversation_id, role, content, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (message_id, conversation_id, msg.get("role", "user"), msg.get("content", ""), now)
        )
        
        # Update FTS
        cursor.execute(
            """
            INSERT INTO messages_fts (rowid, content)
            VALUES (last_insert_rowid(), ?)
            """,
            (msg.get("content", ""),)
        )
    
    conn.commit()
    conn.close()
    
    return {
        "status": "imported",
        "conversation_id": conversation_id,
        "message_count": len(messages),
    }
