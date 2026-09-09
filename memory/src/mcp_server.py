"""
OpenMemory MCP Server:
Exposes tools and resources conforming to the Model Context Protocol (MCP)
so external clients (Cursor, Claude Desktop, ChatGPT) and autonomous agents
can read, query, store, and clear shared memories.
"""
from __future__ import annotations
from typing import Optional, Dict, Any, List
import json
import asyncio

from memory.src.service import MemoryService
from memory.src.schemas import MemoryCategory, MemoryItem


class OpenMemoryMCPServer:
    """
    Standard MCP-compatible tool handler interface for memory operations.
    Can be run via stdio JSON-RPC or embedded into multi-agent systems.
    """

    def __init__(self, memory_service: Optional[MemoryService] = None):
        self.memory_service = memory_service or MemoryService()

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Returns MCP tool manifests matching standard schema."""
        return [
            {
                "name": "retrieve_memories",
                "description": "Retrieve relevant memories from the user's long-term memory bank using semantic similarity and recency ranking.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "The search query or conversation topic to find memories for"},
                        "user_id": {"type": "string", "default": "default_user", "description": "User identifier"},
                        "category": {
                            "type": "string",
                            "enum": ["preferences", "biographical", "projects", "communication_style"],
                            "description": "Optional category filter",
                        },
                        "limit": {"type": "integer", "default": 5, "description": "Maximum number of memories to return"},
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "store_memory",
                "description": "Manually store a durable fact, preference, or work context item into the shared long-term memory bank.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "content": {"type": "string", "description": "The factual statement to remember"},
                        "category": {
                            "type": "string",
                            "enum": ["preferences", "biographical", "projects", "communication_style"],
                            "default": "projects",
                        },
                        "user_id": {"type": "string", "default": "default_user"},
                        "source_agent": {"type": "string", "default": "mcp_client"},
                    },
                    "required": ["content"],
                },
            },
            {
                "name": "list_all_memories",
                "description": "List all stored memories for a user, optionally filtered by category.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string", "default": "default_user"},
                        "category": {"type": "string"},
                    },
                },
            },
            {
                "name": "delete_memory",
                "description": "Delete a specific memory by its unique ID.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "memory_id": {"type": "string", "description": "ID of memory to delete"},
                    },
                    "required": ["memory_id"],
                },
            },
        ]

    async def execute_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatches an MCP tool call to the underlying memory service."""
        if name == "retrieve_memories":
            query = arguments.get("query", "")
            user_id = arguments.get("user_id", "default_user")
            category_str = arguments.get("category")
            category = MemoryCategory(category_str) if category_str else None
            limit = int(arguments.get("limit", 5))

            results = self.memory_service.retrieve(
                query=query,
                user_id=user_id,
                category=category,
                limit=limit,
            )
            # Fallback for meta-queries if semantic match returned zero
            if not results and any(kw in query.lower() for kw in ["all", "know", "remember", "project"]):
                all_m = self.memory_service.get_all(user_id=user_id, category=category)
                results = [(m, 1.0) for m in all_m[:limit]]

            formatted = [
                {
                    "id": item.id,
                    "content": item.content,
                    "category": item.category.value,
                    "score": round(score, 4),
                    "source_agent": item.source_agent,
                }
                for item, score in results
            ]
            return {"memories": formatted, "count": len(formatted)}

        elif name == "store_memory":
            content = arguments.get("content", "")
            category_val = arguments.get("category", "projects")
            category = MemoryCategory(category_val)
            user_id = arguments.get("user_id", "default_user")
            source_agent = arguments.get("source_agent", "mcp_client")

            item = self.memory_service.add_manual_memory(
                content=content,
                category=category,
                user_id=user_id,
                source_agent=source_agent,
            )
            return {
                "success": True,
                "memory": {
                    "id": item.id,
                    "content": item.content,
                    "category": item.category.value,
                    "source_agent": item.source_agent,
                },
            }

        elif name == "list_all_memories":
            user_id = arguments.get("user_id", "default_user")
            category_str = arguments.get("category")
            category = MemoryCategory(category_str) if category_str else None

            items = self.memory_service.get_all(user_id=user_id, category=category)
            return {
                "total": len(items),
                "memories": [
                    {"id": m.id, "content": m.content, "category": m.category.value, "source_agent": m.source_agent}
                    for m in items
                ],
            }

        elif name == "delete_memory":
            memory_id = arguments.get("memory_id", "")
            success = self.memory_service.delete_memory(memory_id)
            return {"success": success, "memory_id": memory_id}

        raise ValueError(f"Unknown MCP tool: {name}")
