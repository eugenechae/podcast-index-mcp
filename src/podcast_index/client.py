"""Podcast Index API client."""

from typing import Any, TypedDict
from urllib.parse import urlencode

import httpx

from podcast_index.auth import generate_auth_headers


# Shared HTTP client for connection pooling across requests
_http_client: httpx.AsyncClient | None = None


def get_client() -> httpx.AsyncClient:
    """
    Get or create the shared HTTP client for connection pooling.

    Returns:
        Shared AsyncClient instance that reuses connections to the same host
    """
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient()
    return _http_client


class SearchParams(TypedDict, total=False):
    """
    Parameters for podcast search requests.

    Attributes:
        q: Search query (required)
        max: Maximum number of results to return (default varies, max 1000)
        val: Filter by value block type (any, lightning, hive, webmonetization)
        aponly: Only return feeds with iTunes IDs
        clean: Exclude explicit content
        similar: Include similar matches, prioritizes title matches
        fulltext: Return complete text fields (otherwise truncated to 100 words)
    """

    q: str
    max: int
    val: str
    aponly: bool
    clean: bool
    similar: bool
    fulltext: bool


class SearchByTitleParams(TypedDict, total=False):
    """
    Parameters for title-focused podcast search requests.

    Attributes:
        q: Search query to match against podcast title field (required)
        max: Maximum number of results to return (default varies, max 1000)
        val: Filter by value block type (any, lightning, hive, webmonetization)
        clean: Exclude explicit content
        similar: Include similar matches using fuzzy search
        fulltext: Return complete text fields (otherwise truncated to 100 words)
    """

    q: str
    max: int
    val: str
    clean: bool
    similar: bool
    fulltext: bool


class SearchByPersonParams(TypedDict, total=False):
    """
    Parameters for episode search by person.

    Attributes:
        q: Person name to search for in person tags, titles, and descriptions (required)
        max: Maximum number of results to return (default varies, max 1000)
        fulltext: Return complete text fields (otherwise truncated to 100 words)
    """

    q: str
    max: int
    fulltext: bool


class GetEpisodesParams(TypedDict, total=False):
    """
    Parameters for retrieving episodes from a podcast feed.

    Attributes:
        id: Podcast feed ID (required)
        since: Unix timestamp - only return episodes published since this time
        max: Maximum number of results to return (default varies, max 1000)
        fulltext: Return complete text fields (otherwise truncated to 100 words)
    """

    id: int
    since: int
    max: int
    fulltext: bool


class GetPodcastDetailsParams(TypedDict, total=False):
    """
    Parameters for retrieving podcast details by feed ID.

    Attributes:
        id: Podcast feed ID (required)
    """

    id: int


class GetEpisodeDetailsParams(TypedDict, total=False):
    """
    Parameters for retrieving episode details by ID.

    Attributes:
        id: Episode ID (required)
        fulltext: Return complete text fields (otherwise truncated to 100 words)
    """

    id: int
    fulltext: bool


def build_search_url(params: SearchParams) -> str:
    """
    Build the search API URL with query parameters.

    Args:
        params: Search parameters including query and optional filters

    Returns:
        Complete URL with encoded query parameters
    """
    base_url = "https://api.podcastindex.org/api/1.0/search/byterm"

    query_params: dict[str, str | int] = {}
    query_params["q"] = params["q"]

    if "max" in params:
        query_params["max"] = params["max"]

    if "val" in params:
        query_params["val"] = params["val"]

    if params.get("aponly"):
        query_params["aponly"] = "true"

    if params.get("clean"):
        query_params["clean"] = "true"

    if params.get("similar"):
        query_params["similar"] = "true"

    if params.get("fulltext"):
        query_params["fulltext"] = "true"

    query_string = urlencode(query_params)
    return f"{base_url}?{query_string}"


async def search_podcasts(
    api_key: str, api_secret: str, params: SearchParams
) -> dict[str, Any]:
    """
    Search for podcasts using the Podcast Index API.

    Args:
        api_key: Podcast Index API key
        api_secret: Podcast Index API secret
        params: Search parameters

    Returns:
        API response containing search results

    Raises:
        httpx.HTTPError: If the request fails
        httpx.HTTPStatusError: If the API returns an error status
    """
    url = build_search_url(params)
    headers = generate_auth_headers(api_key, api_secret)

    client = get_client()
    response = await client.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def build_search_by_title_url(params: SearchByTitleParams) -> str:
    """
    Build the title search API URL with query parameters.

    Args:
        params: Search parameters including query and optional filters

    Returns:
        Complete URL with encoded query parameters
    """
    base_url = "https://api.podcastindex.org/api/1.0/search/bytitle"

    query_params: dict[str, str | int] = {}
    query_params["q"] = params["q"]

    if "max" in params:
        query_params["max"] = params["max"]

    if "val" in params:
        query_params["val"] = params["val"]

    if params.get("clean"):
        query_params["clean"] = "true"

    if params.get("similar"):
        query_params["similar"] = "true"

    if params.get("fulltext"):
        query_params["fulltext"] = "true"

    query_string = urlencode(query_params)
    return f"{base_url}?{query_string}"


async def search_podcasts_by_title(
    api_key: str, api_secret: str, params: SearchByTitleParams
) -> dict[str, Any]:
    """
    Search for podcasts by title using the Podcast Index API.

    Args:
        api_key: Podcast Index API key
        api_secret: Podcast Index API secret
        params: Search parameters

    Returns:
        API response containing search results

    Raises:
        httpx.HTTPError: If the request fails
        httpx.HTTPStatusError: If the API returns an error status
    """
    url = build_search_by_title_url(params)
    headers = generate_auth_headers(api_key, api_secret)

    client = get_client()
    response = await client.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def build_search_by_person_url(params: SearchByPersonParams) -> str:
    """
    Build the person search API URL with query parameters.

    Args:
        params: Search parameters including person name and optional filters

    Returns:
        Complete URL with encoded query parameters
    """
    base_url = "https://api.podcastindex.org/api/1.0/search/byperson"

    query_params: dict[str, str | int] = {}
    query_params["q"] = params["q"]

    if "max" in params:
        query_params["max"] = params["max"]

    if params.get("fulltext"):
        query_params["fulltext"] = "true"

    query_string = urlencode(query_params)
    return f"{base_url}?{query_string}"


async def search_episodes_by_person(
    api_key: str, api_secret: str, params: SearchByPersonParams
) -> dict[str, Any]:
    """
    Search for episodes by person using the Podcast Index API.

    Args:
        api_key: Podcast Index API key
        api_secret: Podcast Index API secret
        params: Search parameters

    Returns:
        API response containing episode search results

    Raises:
        httpx.HTTPError: If the request fails
        httpx.HTTPStatusError: If the API returns an error status
    """
    url = build_search_by_person_url(params)
    headers = generate_auth_headers(api_key, api_secret)

    client = get_client()
    response = await client.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def build_episodes_url(params: GetEpisodesParams) -> str:
    """
    Build the get episodes API URL with query parameters.

    Args:
        params: Parameters including feed ID and optional filters

    Returns:
        Complete URL with encoded query parameters
    """
    base_url = "https://api.podcastindex.org/api/1.0/episodes/byfeedid"

    query_params: dict[str, str | int] = {}
    query_params["id"] = params["id"]

    if "since" in params:
        query_params["since"] = params["since"]

    if "max" in params:
        query_params["max"] = params["max"]

    if params.get("fulltext"):
        query_params["fulltext"] = "true"

    query_string = urlencode(query_params)
    return f"{base_url}?{query_string}"


async def get_episodes(
    api_key: str, api_secret: str, params: GetEpisodesParams
) -> dict[str, Any]:
    """
    Get episodes from a podcast feed using the Podcast Index API.

    Args:
        api_key: Podcast Index API key
        api_secret: Podcast Index API secret
        params: Parameters including feed ID

    Returns:
        API response containing episode data

    Raises:
        httpx.HTTPError: If the request fails
        httpx.HTTPStatusError: If the API returns an error status
    """
    url = build_episodes_url(params)
    headers = generate_auth_headers(api_key, api_secret)

    client = get_client()
    response = await client.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def build_podcast_details_url(params: GetPodcastDetailsParams) -> str:
    """
    Build the get podcast details API URL with query parameters.

    Args:
        params: Parameters including feed ID

    Returns:
        Complete URL with encoded query parameters
    """
    base_url = "https://api.podcastindex.org/api/1.0/podcasts/byfeedid"

    query_params: dict[str, str | int] = {}
    query_params["id"] = params["id"]

    query_string = urlencode(query_params)
    return f"{base_url}?{query_string}"


async def get_podcast_details(
    api_key: str, api_secret: str, params: GetPodcastDetailsParams
) -> dict[str, Any]:
    """
    Get podcast details by feed ID using the Podcast Index API.

    Args:
        api_key: Podcast Index API key
        api_secret: Podcast Index API secret
        params: Parameters including feed ID

    Returns:
        API response containing podcast details

    Raises:
        httpx.HTTPError: If the request fails
        httpx.HTTPStatusError: If the API returns an error status
    """
    url = build_podcast_details_url(params)
    headers = generate_auth_headers(api_key, api_secret)

    client = get_client()
    response = await client.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def build_episode_details_url(params: GetEpisodeDetailsParams) -> str:
    """
    Build the get episode details API URL with query parameters.

    Args:
        params: Parameters including episode ID and optional filters

    Returns:
        Complete URL with encoded query parameters
    """
    base_url = "https://api.podcastindex.org/api/1.0/episodes/byid"

    query_params: dict[str, str | int] = {}
    query_params["id"] = params["id"]

    if params.get("fulltext"):
        query_params["fulltext"] = "true"

    query_string = urlencode(query_params)
    return f"{base_url}?{query_string}"


async def get_episode_details(
    api_key: str, api_secret: str, params: GetEpisodeDetailsParams
) -> dict[str, Any]:
    """
    Get episode details by ID using the Podcast Index API.

    Args:
        api_key: Podcast Index API key
        api_secret: Podcast Index API secret
        params: Parameters including episode ID

    Returns:
        API response containing episode details

    Raises:
        httpx.HTTPError: If the request fails
        httpx.HTTPStatusError: If the API returns an error status
    """
    url = build_episode_details_url(params)
    headers = generate_auth_headers(api_key, api_secret)

    client = get_client()
    response = await client.get(url, headers=headers)
    response.raise_for_status()
    return response.json()
