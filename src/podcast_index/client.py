"""Podcast Index API client."""

from typing import Any, TypedDict
from urllib.parse import urlencode

import httpx

from podcast_index.auth import generate_auth_headers


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

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
