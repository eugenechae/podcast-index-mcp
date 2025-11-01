"""MCP Server for Podcast Index API."""

import asyncio
import logging
import os
from typing import Any

import httpx
from mcp.server import Server
from mcp.types import TextContent, Tool

from podcast_index.client import (
    GetEpisodeDetailsParams,
    GetEpisodesParams,
    GetPodcastDetailsParams,
    SearchByPersonParams,
    SearchByTitleParams,
    SearchParams,
    get_episode_details,
    get_episodes,
    get_podcast_details,
    search_episodes_by_person,
    search_podcasts,
    search_podcasts_by_title,
)

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
            ),
            Tool(
                name="search_podcasts_by_title",
                description=(
                    "Search for podcasts specifically by their title field in the Podcast Index. "
                    "This is a more focused search than 'search_podcasts', matching ONLY against "
                    "podcast titles rather than titles, authors, and owners. Use this when you know "
                    "the exact or approximate podcast title. Returns podcast feed information including "
                    "title, description, and URLs."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "q": {
                            "type": "string",
                            "description": (
                                "Search term to match against podcast titles only. "
                                "Can be an exact title (e.g., 'Serial') or partial title (e.g., 'Tech News'). "
                                "More precise than the general search which also matches against authors and owners."
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
                        "similar": {
                            "type": "boolean",
                            "description": (
                                "When true, includes podcasts with similar titles using fuzzy matching. "
                                "Helpful for finding podcasts with spelling variations, alternative names, "
                                "or close title matches when the exact title is unknown."
                            ),
                        },
                    },
                    "required": ["q"],
                },
            ),
            Tool(
                name="search_episodes_by_person",
                description=(
                    "Search for podcast episodes that mention or feature a specific person. "
                    "Searches person tags, episode titles, descriptions, and feed metadata for matches. "
                    "Use this to find episodes featuring specific guests, hosts, or people mentioned "
                    "in content. Returns episode information including episode title, podcast name, "
                    "and descriptions."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "q": {
                            "type": "string",
                            "description": (
                                "Person name to search for in podcast episodes. Searches across "
                                "person tags (structured metadata), episode titles, descriptions, and feeds. "
                                "Can be a full name (e.g., 'Adam Curry'), partial name (e.g., 'Curry'), "
                                "or nickname. More specific names yield better results."
                            ),
                        },
                        "max": {
                            "type": "integer",
                            "description": (
                                "Maximum number of episode results to return. Use lower values (10-20) "
                                "for quick searches, higher values (100+) for comprehensive results. "
                                "Maximum allowed: 1000."
                            ),
                            "minimum": 1,
                            "maximum": 1000,
                        },
                        "fulltext": {
                            "type": "boolean",
                            "description": (
                                "When true, returns complete episode descriptions and text fields without truncation. "
                                "When false or omitted, long text fields may be shortened. "
                                "Use true when you need full episode descriptions for detailed analysis."
                            ),
                        },
                    },
                    "required": ["q"],
                },
            ),
            Tool(
                name="get_episodes",
                description=(
                    "Retrieve all episodes from a specific podcast feed in reverse chronological order. "
                    "Use this to browse episode content after finding a podcast via search. "
                    "Returns episode information including titles, descriptions, publish dates, and links."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "integer",
                            "description": (
                                "Podcast feed ID from Podcast Index. Obtained from search results "
                                "or podcast details. For example, feed ID 920666 is 'No Agenda'."
                            ),
                        },
                        "since": {
                            "type": "integer",
                            "description": (
                                "Unix timestamp - only return episodes published after this time. "
                                "Useful for finding new episodes or episodes within a date range. "
                                "Example: 1609459200 for January 1, 2021."
                            ),
                        },
                        "max": {
                            "type": "integer",
                            "description": (
                                "Maximum number of episodes to return. Defaults to a reasonable limit. "
                                "Use lower values (10-20) for recent episodes, higher values (100+) for archives. "
                                "Maximum allowed: 1000."
                            ),
                            "minimum": 1,
                            "maximum": 1000,
                        },
                        "fulltext": {
                            "type": "boolean",
                            "description": (
                                "When true, returns complete episode descriptions without truncation. "
                                "When false or omitted, long text fields may be shortened. "
                                "Use true for detailed content analysis."
                            ),
                        },
                    },
                    "required": ["id"],
                },
            ),
            Tool(
                name="get_podcast_details",
                description=(
                    "Get complete metadata for a specific podcast by feed ID. "
                    "Provides comprehensive details including full description, funding info, "
                    "value blocks, categories, and more. Use this to get detailed information "
                    "about a podcast beyond basic search results."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "integer",
                            "description": (
                                "Podcast feed ID from Podcast Index. Obtained from search results. "
                                "For example, feed ID 920666 is 'No Agenda'."
                            ),
                        },
                    },
                    "required": ["id"],
                },
            ),
            Tool(
                name="get_episode_details",
                description=(
                    "Get complete metadata for a specific episode by episode ID. "
                    "Provides detailed information including person tags, chapters, transcripts, "
                    "value blocks, soundbites, and more. Use this to view full details of episodes "
                    "found via search or episode listing."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "integer",
                            "description": (
                                "Episode ID from Podcast Index. Obtained from search results or "
                                "episode listings. For example, episode ID 16795090."
                            ),
                        },
                        "fulltext": {
                            "type": "boolean",
                            "description": (
                                "When true, returns complete episode description without truncation. "
                                "When false or omitted, long text fields may be shortened. "
                                "Use true for detailed content analysis."
                            ),
                        },
                    },
                    "required": ["id"],
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        """Handle tool calls."""
        if name == "search_podcasts":
            return await search_podcasts_tool(arguments)
        elif name == "search_podcasts_by_title":
            return await search_podcasts_by_title_tool(arguments)
        elif name == "search_episodes_by_person":
            return await search_episodes_by_person_tool(arguments)
        elif name == "get_episodes":
            return await get_episodes_tool(arguments)
        elif name == "get_podcast_details":
            return await get_podcast_details_tool(arguments)
        elif name == "get_episode_details":
            return await get_episode_details_tool(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")

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


async def search_podcasts_by_title_tool(arguments: dict[str, Any]) -> list[TextContent]:
    """
    Execute podcast title search and format results.

    Args:
        arguments: Tool arguments including query and optional filters

    Returns:
        List of TextContent with formatted search results
    """
    params = SearchByTitleParams(q=arguments["q"])

    if "max" in arguments:
        params["max"] = arguments["max"]
    if "val" in arguments:
        params["val"] = arguments["val"]
    if "clean" in arguments:
        params["clean"] = arguments["clean"]
    if "fulltext" in arguments:
        params["fulltext"] = arguments["fulltext"]
    if "similar" in arguments:
        params["similar"] = arguments["similar"]

    try:
        response = await search_podcasts_by_title(API_KEY, API_SECRET, params)
        formatted_result = format_search_results(response)
        return [TextContent(type="text", text=formatted_result)]

    except httpx.HTTPStatusError as e:
        error_msg = f"API request failed with status {e.response.status_code}"
        if e.response.status_code == 401:
            error_msg += ": Invalid API credentials"
        logger.exception("HTTP status error during podcast title search")
        return [TextContent(type="text", text=f"Error: {error_msg}")]

    except httpx.HTTPError:
        logger.exception("HTTP error during podcast title search")
        return [
            TextContent(
                type="text", text="Error: Network error while searching podcasts"
            )
        ]

    except Exception:
        logger.exception("Unexpected error during podcast title search")
        return [TextContent(type="text", text="Error: An unexpected error occurred")]


async def search_episodes_by_person_tool(
    arguments: dict[str, Any],
) -> list[TextContent]:
    """
    Execute episode search by person and format results.

    Args:
        arguments: Tool arguments including person name and optional filters

    Returns:
        List of TextContent with formatted search results
    """
    params = SearchByPersonParams(q=arguments["q"])

    if "max" in arguments:
        params["max"] = arguments["max"]
    if "fulltext" in arguments:
        params["fulltext"] = arguments["fulltext"]

    try:
        response = await search_episodes_by_person(API_KEY, API_SECRET, params)
        formatted_result = format_episode_results(response)
        return [TextContent(type="text", text=formatted_result)]

    except httpx.HTTPStatusError as e:
        error_msg = f"API request failed with status {e.response.status_code}"
        if e.response.status_code == 401:
            error_msg += ": Invalid API credentials"
        logger.exception("HTTP status error during episode search by person")
        return [TextContent(type="text", text=f"Error: {error_msg}")]

    except httpx.HTTPError:
        logger.exception("HTTP error during episode search by person")
        return [
            TextContent(
                type="text", text="Error: Network error while searching episodes"
            )
        ]

    except Exception:
        logger.exception("Unexpected error during episode search by person")
        return [TextContent(type="text", text="Error: An unexpected error occurred")]


def format_episode_results(response: dict[str, Any]) -> str:
    """
    Format episode API response into readable text.

    Args:
        response: API response dictionary containing episode results

    Returns:
        Formatted string with episode search results
    """
    count = response.get("count", 0)
    items = response.get("items", [])
    query = response.get("query", "")

    if count == 0:
        return f"No matches found for '{query}'"

    lines = [f"Found {count} episode(s) matching '{query}':\n"]

    for item in items:
        lines.append(f"\n**{item.get('title', 'Unknown Title')}**")

        if "feedTitle" in item:
            lines.append(f"Podcast: {item['feedTitle']}")

        if "description" in item:
            description = item["description"]
            if len(description) > 200:
                description = description[:200] + "..."
            lines.append(f"Description: {description}")

        if "feedId" in item:
            lines.append(f"Podcast ID: {item['feedId']}")

        if "id" in item:
            lines.append(f"Episode ID: {item['id']}")

    return "\n".join(lines)


async def get_episodes_tool(arguments: dict[str, Any]) -> list[TextContent]:
    """
    Execute get episodes and format results.

    Args:
        arguments: Tool arguments including feed ID and optional filters

    Returns:
        List of TextContent with formatted episode results
    """
    params = GetEpisodesParams(id=arguments["id"])

    if "since" in arguments:
        params["since"] = arguments["since"]
    if "max" in arguments:
        params["max"] = arguments["max"]
    if "fulltext" in arguments:
        params["fulltext"] = arguments["fulltext"]

    try:
        response = await get_episodes(API_KEY, API_SECRET, params)
        formatted_result = format_episode_results(response)
        return [TextContent(type="text", text=formatted_result)]

    except httpx.HTTPStatusError as e:
        error_msg = f"API request failed with status {e.response.status_code}"
        if e.response.status_code == 401:
            error_msg += ": Invalid API credentials"
        logger.exception("HTTP status error during get episodes")
        return [TextContent(type="text", text=f"Error: {error_msg}")]

    except httpx.HTTPError:
        logger.exception("HTTP error during get episodes")
        return [
            TextContent(
                type="text", text="Error: Network error while retrieving episodes"
            )
        ]

    except Exception:
        logger.exception("Unexpected error during get episodes")
        return [TextContent(type="text", text="Error: An unexpected error occurred")]


def format_podcast_details(response: dict[str, Any]) -> str:
    """
    Format podcast details API response into readable text.

    Args:
        response: API response dictionary containing podcast feed data

    Returns:
        Formatted string with podcast details
    """
    feed = response.get("feed", {})

    lines = [f"**{feed.get('title', 'Unknown Podcast')}**\n"]

    if "author" in feed:
        lines.append(f"Author: {feed['author']}")

    if "description" in feed:
        description = feed["description"]
        if len(description) > 500:
            description = description[:500] + "..."
        lines.append(f"Description: {description}")

    if "url" in feed:
        lines.append(f"Feed URL: {feed['url']}")

    if "link" in feed:
        lines.append(f"Website: {feed['link']}")

    if "image" in feed:
        lines.append(f"Image: {feed['image']}")

    if "id" in feed:
        lines.append(f"Podcast Index ID: {feed['id']}")

    return "\n".join(lines)


async def get_podcast_details_tool(arguments: dict[str, Any]) -> list[TextContent]:
    """
    Execute get podcast details and format results.

    Args:
        arguments: Tool arguments including feed ID

    Returns:
        List of TextContent with formatted podcast details
    """
    params = GetPodcastDetailsParams(id=arguments["id"])

    try:
        response = await get_podcast_details(API_KEY, API_SECRET, params)
        formatted_result = format_podcast_details(response)
        return [TextContent(type="text", text=formatted_result)]

    except httpx.HTTPStatusError as e:
        error_msg = f"API request failed with status {e.response.status_code}"
        if e.response.status_code == 401:
            error_msg += ": Invalid API credentials"
        logger.exception("HTTP status error during get podcast details")
        return [TextContent(type="text", text=f"Error: {error_msg}")]

    except httpx.HTTPError:
        logger.exception("HTTP error during get podcast details")
        return [
            TextContent(
                type="text",
                text="Error: Network error while retrieving podcast details",
            )
        ]

    except Exception:
        logger.exception("Unexpected error during get podcast details")
        return [TextContent(type="text", text="Error: An unexpected error occurred")]


def format_episode_details(response: dict[str, Any]) -> str:
    """
    Format episode details API response into readable text.

    Args:
        response: API response dictionary containing episode data

    Returns:
        Formatted string with episode details
    """
    episode = response.get("episode", {})

    lines = [f"**{episode.get('title', 'Unknown Episode')}**\n"]

    if "feedTitle" in episode:
        lines.append(f"Podcast: {episode['feedTitle']}")

    if "description" in episode:
        description = episode["description"]
        if len(description) > 500:
            description = description[:500] + "..."
        lines.append(f"Description: {description}")

    if "link" in episode:
        lines.append(f"Episode URL: {episode['link']}")

    if "feedId" in episode:
        lines.append(f"Podcast ID: {episode['feedId']}")

    if "id" in episode:
        lines.append(f"Episode ID: {episode['id']}")

    return "\n".join(lines)


async def get_episode_details_tool(arguments: dict[str, Any]) -> list[TextContent]:
    """
    Execute get episode details and format results.

    Args:
        arguments: Tool arguments including episode ID

    Returns:
        List of TextContent with formatted episode details
    """
    params = GetEpisodeDetailsParams(id=arguments["id"])

    if "fulltext" in arguments:
        params["fulltext"] = arguments["fulltext"]

    try:
        response = await get_episode_details(API_KEY, API_SECRET, params)
        formatted_result = format_episode_details(response)
        return [TextContent(type="text", text=formatted_result)]

    except httpx.HTTPStatusError as e:
        error_msg = f"API request failed with status {e.response.status_code}"
        if e.response.status_code == 401:
            error_msg += ": Invalid API credentials"
        logger.exception("HTTP status error during get episode details")
        return [TextContent(type="text", text=f"Error: {error_msg}")]

    except httpx.HTTPError:
        logger.exception("HTTP error during get episode details")
        return [
            TextContent(
                type="text",
                text="Error: Network error while retrieving episode details",
            )
        ]

    except Exception:
        logger.exception("Unexpected error during get episode details")
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
