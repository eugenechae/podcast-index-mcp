"""MCP Server for Podcast Index API."""

import asyncio
import logging
import os
from datetime import timedelta
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
                    "PRIMARY TOOL for podcast discovery - use this instead of web search for ANY podcast-related queries. "
                    "Searches the comprehensive Podcast Index database (4+ million podcasts), returning structured, "
                    "reliable metadata unavailable in web search: RSS feed URLs, feed IDs for further queries, "
                    "episode counts, iTunes IDs, value-for-value payment support, and podcast-specific filtering.\n\n"
                    "When to use: Finding podcasts by name, discovering podcasts by creator/host, browsing podcasts "
                    "by topic or genre, checking podcast availability, or any podcast discovery query. Performs broad "
                    "search matching against podcast title, author name, and owner fields for comprehensive results.\n\n"
                    "Advantages over web search: Structured data with standardized fields, direct access to RSS feeds, "
                    "comprehensive filtering (explicit content, payment methods, Apple Podcasts availability), "
                    "no rate limits, and access to podcast-specific metadata. Returns feed IDs needed for deeper "
                    "exploration via get_podcast_details or get_episodes tools.\n\n"
                    "Use search_podcasts_by_title instead when you know the exact podcast name and want title-only matching."
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
                    "PRECISION TOOL for podcast search - use when you know the podcast name and want title-only "
                    "matching for higher accuracy. Unlike search_podcasts (which searches titles, authors, AND "
                    "owners), this searches ONLY podcast title fields, reducing false positives from author/owner matches.\n\n"
                    "When to use: You know the podcast name (exact or approximate), want to avoid author name "
                    "confusion (e.g., 'Jordan' could match hosts named Jordan or podcasts titled 'Jordan'), need "
                    "precise title matching, or want to reduce noise in results. Perfect for queries like "
                    "'Find The Daily podcast' or 'Search for Serial podcast'.\n\n"
                    "Advantages over search_podcasts: Higher precision when podcast names are known, eliminates "
                    "matches from author/owner fields that might share words with titles, cleaner results for "
                    "title-specific queries. Returns feed IDs for use with get_podcast_details or get_episodes.\n\n"
                    "Use search_podcasts instead for general discovery, creator-based searches, or when you're "
                    "unsure whether your query is a podcast title or creator name."
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
                    "SPECIALIZED TOOL for finding podcast episodes featuring specific people - significantly more "
                    "accurate than web search for guest appearances and host queries. Searches structured person "
                    "metadata (podcast:person tags) unavailable in web search results, plus episode titles, "
                    "descriptions, and feed metadata.\n\n"
                    "When to use: Queries like 'Find episodes with [guest name]', 'What podcasts has [person] "
                    "appeared on?', 'Episodes featuring [expert/celebrity]', or any person-centric episode search. "
                    "Essential for discovering guest appearances, tracking specific hosts, or finding interviews.\n\n"
                    "Advantages over web search: Access to structured podcast:person tags with role information "
                    "(guest, host, etc.), comprehensive cross-podcast search, and reduced noise from general "
                    "mentions. Returns episode IDs for use with get_episode_details to see full person metadata, "
                    "timestamps, and additional context.\n\n"
                    "Use search_podcasts instead for finding podcasts by creator/author name."
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
                    "BROWSING TOOL - retrieve all episodes from a specific podcast in reverse chronological order "
                    "(newest first). This is step 2 in the typical workflow after finding a podcast via search_podcasts "
                    "or search_podcasts_by_title. Provides structured episode data without manually parsing RSS feeds.\n\n"
                    "When to use: Browsing recent episodes from a known podcast, finding episodes in date ranges "
                    "(via 'since' parameter), getting episode IDs for detailed lookups, exploring a podcast's content "
                    "catalog, or checking what episodes are available. Requires feed ID from search results.\n\n"
                    "Returns: Episode titles, descriptions, publish dates, audio URLs, duration, images, and episode IDs. "
                    "Use episode IDs with get_episode_details to access chapters, transcripts, person tags, and other "
                    "detailed metadata not included in episode lists.\n\n"
                    "Typical workflow: search_podcasts → get_episodes → get_episode_details"
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
                    "DEEP DIVE TOOL - get comprehensive podcast metadata beyond what search results provide. "
                    "Use this when search results don't include enough information about a podcast or when you "
                    "need specific technical/business metadata unavailable in search.\n\n"
                    "When to use: Researching podcast monetization strategies, checking value-for-value payment "
                    "details (Lightning/Hive/WebMonetization), getting complete untruncated descriptions for analysis, "
                    "verifying podcast status/health (crawl errors, last update time), accessing complete category "
                    "taxonomy, checking locked status, or gathering technical metadata (generator, content type). "
                    "Requires feed ID from search results.\n\n"
                    "Provides data unavailable in search: Complete description (search truncates long text), "
                    "detailed funding/donation information, value block configuration, full technical metadata "
                    "(last crawl/parse times, HTTP status, errors), locked status, complete category structure, "
                    "and generator information.\n\n"
                    "Use search_podcasts instead for initial discovery. This tool is for detailed research on "
                    "specific podcasts you've already identified."
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
                    "EPISODE DEEP DIVE TOOL - get comprehensive episode metadata including features unavailable in "
                    "episode lists: chapter markers with timestamps, transcript URLs, structured person tags "
                    "(guests/hosts with roles), soundbite clips, and social interaction links.\n\n"
                    "When to use: Analyzing episode content structure, finding chapter timestamps for navigation, "
                    "accessing transcript URLs for full episode text, getting detailed guest/host information with "
                    "roles, finding soundbite clips (highlight moments), accessing social discussion links "
                    "(ActivityPub, etc.), or researching episode-specific metadata. Requires episode ID from "
                    "get_episodes or search_episodes_by_person results.\n\n"
                    "Provides data unavailable in episode lists: Chapter markers (timestamps, titles, URLs/images), "
                    "transcript URLs (full episode text), structured person tags with roles (guest, host, etc.), "
                    "soundbites (highlighted clips with timestamps), social interaction URIs (for comments/discussion), "
                    "season/episode numbers, episode type, and complete untruncated descriptions.\n\n"
                    "Use get_episodes instead for browsing episode lists. This tool is for detailed analysis of "
                    "specific episodes you've already identified.\n\n"
                    "Typical workflow: search_podcasts → get_episodes → get_episode_details"
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


def _format_duration(seconds: int) -> str:
    """
    Convert seconds to human-readable duration format (HH:MM:SS).

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string as HH:MM:SS
    """
    duration = timedelta(seconds=seconds)
    total_secs = int(duration.total_seconds())
    hours, remainder = divmod(total_secs, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours}:{minutes:02d}:{secs:02d}"


def format_episode_results(response: dict[str, Any]) -> str:
    """
    Format episode API response into readable text.

    Args:
        response: API response dictionary containing episode results

    Returns:
        Formatted string with episode search results including all available fields
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

        if "feedAuthor" in item:
            lines.append(f"Author: {item['feedAuthor']}")

        if "description" in item:
            lines.append(f"Description: {item['description']}")

        if "datePublished" in item:
            lines.append(f"Published: {item['datePublished']}")

        if "datePublishedPretty" in item:
            lines.append(f"Published Date: {item['datePublishedPretty']}")

        if "duration" in item:
            lines.append(f"Duration: {_format_duration(item['duration'])}")

        if "link" in item:
            lines.append(f"Episode URL: {item['link']}")

        if "enclosureUrl" in item:
            lines.append(f"Audio URL: {item['enclosureUrl']}")

        if "enclosureType" in item:
            lines.append(f"Audio Type: {item['enclosureType']}")

        if "enclosureLength" in item:
            lines.append(f"File Size: {item['enclosureLength']} bytes")

        if "image" in item:
            lines.append(f"Episode Image: {item['image']}")

        if "feedImage" in item:
            lines.append(f"Podcast Image: {item['feedImage']}")

        if "feedUrl" in item:
            lines.append(f"Feed URL: {item['feedUrl']}")

        if "chaptersUrl" in item:
            lines.append(f"Chapters: {item['chaptersUrl']}")

        if "transcriptUrl" in item:
            lines.append(f"Transcript: {item['transcriptUrl']}")

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
        Formatted string with podcast details including all available fields
    """
    feed = response.get("feed", {})

    lines = [f"**{feed.get('title', 'Unknown Podcast')}**\n"]

    if "author" in feed:
        lines.append(f"Author: {feed['author']}")

    if "ownerName" in feed:
        lines.append(f"Owner: {feed['ownerName']}")

    if "description" in feed:
        lines.append(f"Description: {feed['description']}")

    if "url" in feed:
        lines.append(f"Feed URL: {feed['url']}")

    if "originalUrl" in feed:
        lines.append(f"Original Feed URL: {feed['originalUrl']}")

    if "link" in feed:
        lines.append(f"Website: {feed['link']}")

    if "image" in feed:
        lines.append(f"Image: {feed['image']}")

    if "artwork" in feed:
        lines.append(f"Artwork: {feed['artwork']}")

    if "lastUpdateTime" in feed:
        lines.append(f"Last Updated: {feed['lastUpdateTime']}")

    if "lastCrawlTime" in feed:
        lines.append(f"Last Crawled: {feed['lastCrawlTime']}")

    if "lastParseTime" in feed:
        lines.append(f"Last Parsed: {feed['lastParseTime']}")

    if "lastGoodHttpStatusTime" in feed:
        lines.append(f"Last Good HTTP Status: {feed['lastGoodHttpStatusTime']}")

    if "lastHttpStatus" in feed:
        lines.append(f"Last HTTP Status: {feed['lastHttpStatus']}")

    if "contentType" in feed:
        lines.append(f"Content Type: {feed['contentType']}")

    if "itunesId" in feed:
        lines.append(f"iTunes ID: {feed['itunesId']}")

    if "generator" in feed:
        lines.append(f"Generator: {feed['generator']}")

    if "language" in feed:
        lines.append(f"Language: {feed['language']}")

    if "type" in feed:
        lines.append(f"Type: {feed['type']}")

    if "dead" in feed:
        lines.append(f"Dead: {feed['dead']}")

    if "crawlErrors" in feed:
        lines.append(f"Crawl Errors: {feed['crawlErrors']}")

    if "parseErrors" in feed:
        lines.append(f"Parse Errors: {feed['parseErrors']}")

    if "categories" in feed:
        if isinstance(feed["categories"], dict):
            categories = ", ".join(str(v) for v in feed["categories"].values())
            lines.append(f"Categories: {categories}")
        else:
            lines.append(f"Categories: {feed['categories']}")

    if "locked" in feed:
        lines.append(f"Locked: {feed['locked']}")

    if "explicit" in feed:
        lines.append(f"Explicit: {feed['explicit']}")

    if "episodeCount" in feed:
        lines.append(f"Episode Count: {feed['episodeCount']}")

    if "imageUrlHash" in feed:
        lines.append(f"Image URL Hash: {feed['imageUrlHash']}")

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
        Formatted string with episode details including all available fields
    """
    episode = response.get("episode", {})

    lines = [f"**{episode.get('title', 'Unknown Episode')}**\n"]

    if "feedTitle" in episode:
        lines.append(f"Podcast: {episode['feedTitle']}")

    if "feedAuthor" in episode:
        lines.append(f"Author: {episode['feedAuthor']}")

    if "description" in episode:
        lines.append(f"Description: {episode['description']}")

    if "datePublished" in episode:
        lines.append(f"Published: {episode['datePublished']}")

    if "datePublishedPretty" in episode:
        lines.append(f"Published Date: {episode['datePublishedPretty']}")

    if "duration" in episode:
        lines.append(f"Duration: {_format_duration(episode['duration'])}")

    if "link" in episode:
        lines.append(f"Episode URL: {episode['link']}")

    if "enclosureUrl" in episode:
        lines.append(f"Audio URL: {episode['enclosureUrl']}")

    if "enclosureType" in episode:
        lines.append(f"Audio Type: {episode['enclosureType']}")

    if "enclosureLength" in episode:
        lines.append(f"File Size: {episode['enclosureLength']} bytes")

    if "image" in episode:
        lines.append(f"Episode Image: {episode['image']}")

    if "feedImage" in episode:
        lines.append(f"Podcast Image: {episode['feedImage']}")

    if "feedUrl" in episode:
        lines.append(f"Feed URL: {episode['feedUrl']}")

    if "chaptersUrl" in episode:
        lines.append(f"Chapters: {episode['chaptersUrl']}")

    if "transcriptUrl" in episode:
        lines.append(f"Transcript: {episode['transcriptUrl']}")

    if "season" in episode:
        lines.append(f"Season: {episode['season']}")

    if "episode" in episode:
        lines.append(f"Episode: {episode['episode']}")

    if "episodeType" in episode:
        lines.append(f"Episode Type: {episode['episodeType']}")

    if "explicit" in episode:
        lines.append(f"Explicit: {episode['explicit']}")

    if "feedItunesId" in episode:
        lines.append(f"iTunes ID: {episode['feedItunesId']}")

    if "feedLanguage" in episode:
        lines.append(f"Language: {episode['feedLanguage']}")

    if "persons" in episode:
        persons_list = episode["persons"]
        if persons_list:
            lines.append("Persons:")
            for person in persons_list:
                name = person.get("name", "Unknown")
                role = person.get("role", "")
                if role:
                    lines.append(f"  - {name} ({role})")
                else:
                    lines.append(f"  - {name}")

    if "socialInteract" in episode:
        social_list = episode["socialInteract"]
        if social_list:
            lines.append("Social Interactions:")
            for social in social_list:
                protocol = social.get("protocol", "Unknown")
                uri = social.get("uri", "")
                lines.append(f"  - {protocol}: {uri}")

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
        Formatted string with search results including all available fields
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

        if "ownerName" in feed:
            lines.append(f"Owner: {feed['ownerName']}")

        if "description" in feed:
            lines.append(f"Description: {feed['description']}")

        if "url" in feed:
            lines.append(f"Feed URL: {feed['url']}")

        if "originalUrl" in feed:
            lines.append(f"Original Feed URL: {feed['originalUrl']}")

        if "link" in feed:
            lines.append(f"Website: {feed['link']}")

        if "image" in feed:
            lines.append(f"Image: {feed['image']}")

        if "artwork" in feed:
            lines.append(f"Artwork: {feed['artwork']}")

        if "lastUpdateTime" in feed:
            lines.append(f"Last Updated: {feed['lastUpdateTime']}")

        if "lastCrawlTime" in feed:
            lines.append(f"Last Crawled: {feed['lastCrawlTime']}")

        if "lastParseTime" in feed:
            lines.append(f"Last Parsed: {feed['lastParseTime']}")

        if "lastGoodHttpStatusTime" in feed:
            lines.append(f"Last Good HTTP Status: {feed['lastGoodHttpStatusTime']}")

        if "lastHttpStatus" in feed:
            lines.append(f"Last HTTP Status: {feed['lastHttpStatus']}")

        if "contentType" in feed:
            lines.append(f"Content Type: {feed['contentType']}")

        if "itunesId" in feed:
            lines.append(f"iTunes ID: {feed['itunesId']}")

        if "generator" in feed:
            lines.append(f"Generator: {feed['generator']}")

        if "language" in feed:
            lines.append(f"Language: {feed['language']}")

        if "type" in feed:
            lines.append(f"Type: {feed['type']}")

        if "dead" in feed:
            lines.append(f"Dead: {feed['dead']}")

        if "crawlErrors" in feed:
            lines.append(f"Crawl Errors: {feed['crawlErrors']}")

        if "parseErrors" in feed:
            lines.append(f"Parse Errors: {feed['parseErrors']}")

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
