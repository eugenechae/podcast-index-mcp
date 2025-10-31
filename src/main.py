"""MCP Server for Podcast Index API."""

import asyncio
import logging
import os
from typing import Any

import httpx
from mcp.server import Server
from mcp.types import TextContent, Tool

from podcast_index.client import SearchParams, search_podcasts

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_api_key = os.getenv("PODCAST_INDEX_API_KEY")
_api_secret = os.getenv("PODCAST_INDEX_API_SECRET")

if not _api_key or not _api_secret:
    raise ValueError(
        "PODCAST_INDEX_API_KEY and PODCAST_INDEX_API_SECRET environment variables must be set"
    )

API_KEY: str = _api_key
API_SECRET: str = _api_secret


def create_server() -> Server:
    """
    Create and configure the MCP server.

    Returns:
        Configured MCP Server instance
    """
    server = Server("podcast-index-mcp")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """List available tools."""
        return [
            Tool(
                name="search_podcasts",
                description=(
                    "Search for podcasts by term. Searches against podcast "
                    "title, author, and owner fields in the Podcast Index."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "q": {
                            "type": "string",
                            "description": "Search query term",
                        },
                        "max": {
                            "type": "integer",
                            "description": "Maximum number of results (max 1000)",
                            "minimum": 1,
                            "maximum": 1000,
                        },
                        "val": {
                            "type": "string",
                            "description": "Filter by value block type",
                            "enum": ["any", "lightning", "hive", "webmonetization"],
                        },
                        "clean": {
                            "type": "boolean",
                            "description": "Exclude explicit content",
                        },
                        "fulltext": {
                            "type": "boolean",
                            "description": "Return full text fields (not truncated)",
                        },
                        "aponly": {
                            "type": "boolean",
                            "description": "Only return podcasts with iTunes IDs",
                        },
                        "similar": {
                            "type": "boolean",
                            "description": "Include similar matches",
                        },
                    },
                    "required": ["q"],
                },
            )
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        """Handle tool calls."""
        if name != "search_podcasts":
            raise ValueError(f"Unknown tool: {name}")

        return await search_podcasts_tool(arguments)

    return server


async def search_podcasts_tool(arguments: dict[str, Any]) -> list[TextContent]:
    """
    Execute podcast search and format results.

    Args:
        arguments: Tool arguments including query and optional filters

    Returns:
        List of TextContent with formatted search results
    """
    params = SearchParams(q=arguments["q"])

    if "max" in arguments:
        params["max"] = arguments["max"]
    if "val" in arguments:
        params["val"] = arguments["val"]
    if "clean" in arguments:
        params["clean"] = arguments["clean"]
    if "fulltext" in arguments:
        params["fulltext"] = arguments["fulltext"]
    if "aponly" in arguments:
        params["aponly"] = arguments["aponly"]
    if "similar" in arguments:
        params["similar"] = arguments["similar"]

    try:
        response = await search_podcasts(API_KEY, API_SECRET, params)
        formatted_result = format_search_results(response)
        return [TextContent(type="text", text=formatted_result)]

    except httpx.HTTPStatusError as e:
        error_msg = f"API request failed with status {e.response.status_code}"
        if e.response.status_code == 401:
            error_msg += ": Invalid API credentials"
        logger.exception("HTTP status error during podcast search")
        return [TextContent(type="text", text=f"Error: {error_msg}")]

    except httpx.HTTPError:
        logger.exception("HTTP error during podcast search")
        return [
            TextContent(
                type="text", text="Error: Network error while searching podcasts"
            )
        ]

    except Exception:
        logger.exception("Unexpected error during podcast search")
        return [TextContent(type="text", text="Error: An unexpected error occurred")]


def format_search_results(response: dict[str, Any]) -> str:
    """
    Format API response into readable text.

    Args:
        response: API response dictionary

    Returns:
        Formatted string with search results
    """
    count = response.get("count", 0)
    feeds = response.get("feeds", [])
    query = response.get("query", "")

    if count == 0:
        return f"No matches found for '{query}'"

    lines = [f"Found {count} podcast(s) matching '{query}':\n"]

    for feed in feeds:
        lines.append(f"\n**{feed.get('title', 'Unknown Title')}**")

        if "author" in feed:
            lines.append(f"Author: {feed['author']}")

        if "description" in feed:
            description = feed["description"]
            if len(description) > 200:
                description = description[:200] + "..."
            lines.append(f"Description: {description}")

        if "url" in feed:
            lines.append(f"Feed URL: {feed['url']}")

        if "id" in feed:
            lines.append(f"Podcast Index ID: {feed['id']}")

    return "\n".join(lines)


async def main():
    """Run the MCP server."""
    from mcp.server.stdio import stdio_server

    server = create_server()

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream, write_stream, server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
