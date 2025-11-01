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
                    "Search for podcasts in the Podcast Index database. Performs a broad search "
                    "matching the query against podcast title, author name, and owner fields. "
                    "Use this for general podcast discovery when you want to search across multiple "
                    "fields. Returns podcast feed information including title, description, and URLs."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "q": {
                            "type": "string",
                            "description": (
                                "Search terms to match against podcast title, author, and owner fields. "
                                "Can be a podcast name (e.g., 'Serial'), creator name (e.g., 'Joe Rogan'), "
                                "or topic keywords (e.g., 'technology news'). Supports multi-word queries."
                            ),
                        },
                        "max": {
                            "type": "integer",
                            "description": (
                                "Maximum number of results to return. Defaults to a reasonable limit if not specified. "
                                "Use lower values (10-20) for quick searches, higher values (100+) for comprehensive results. "
                                "Maximum allowed: 1000."
                            ),
                            "minimum": 1,
                            "maximum": 1000,
                        },
                        "val": {
                            "type": "string",
                            "description": (
                                "Filter podcasts by value-for-value payment method support. Options: "
                                "'lightning' (supports Bitcoin Lightning Network payments), "
                                "'hive' (supports Hive blockchain payments), "
                                "'webmonetization' (supports Web Monetization standard), "
                                "'any' (has any value block enabled). "
                                "Use this to find podcasts that support direct listener compensation."
                            ),
                            "enum": ["any", "lightning", "hive", "webmonetization"],
                        },
                        "clean": {
                            "type": "boolean",
                            "description": (
                                "When true, excludes podcasts marked as explicit or containing adult content. "
                                "Useful for family-friendly searches or content curation for general audiences."
                            ),
                        },
                        "fulltext": {
                            "type": "boolean",
                            "description": (
                                "When true, returns complete description and text fields without truncation. "
                                "When false or omitted, long text fields may be shortened. "
                                "Use true when you need full podcast descriptions for detailed analysis."
                            ),
                        },
                        "aponly": {
                            "type": "boolean",
                            "description": (
                                "When true, only returns podcasts that are available on Apple Podcasts "
                                "(have iTunes IDs). Useful for finding mainstream podcasts or ensuring "
                                "compatibility with Apple's ecosystem."
                            ),
                        },
                        "similar": {
                            "type": "boolean",
                            "description": (
                                "When true, includes podcasts with similar titles using fuzzy matching. "
                                "Helpful for finding podcasts with spelling variations, alternative names, "
                                "or close matches when the exact title is unknown."
                            ),
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
