import os
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from mcp.types import TextContent

os.environ["PODCAST_INDEX_API_KEY"] = "test_key"
os.environ["PODCAST_INDEX_API_SECRET"] = "test_secret"

from main import create_server, format_search_results, search_podcasts_tool


def test_create_server_returns_server_instance():
    """create_server should return an MCP Server instance."""
    server = create_server()
    assert server is not None


def test_format_search_results_with_results():
    """format_search_results should format podcasts into readable text."""
    response = {
        "count": 2,
        "query": "python",
        "feeds": [
            {
                "id": 1,
                "title": "Python Weekly",
                "url": "https://example.com/feed",
                "description": "A weekly Python podcast",
                "author": "Test Author",
            },
            {
                "id": 2,
                "title": "Talk Python",
                "url": "https://example.com/feed2",
                "description": "Another Python podcast",
            },
        ],
    }

    result = format_search_results(response)

    assert "2 podcast(s)" in result
    assert "Python Weekly" in result
    assert "Talk Python" in result
    assert "Test Author" in result


def test_format_search_results_with_empty_results():
    """format_search_results should handle empty results."""
    response = {"count": 0, "query": "nonexistent", "feeds": []}

    result = format_search_results(response)

    assert "No matches" in result
    assert "nonexistent" in result


def test_format_search_results_truncates_long_descriptions():
    """format_search_results should truncate long descriptions."""
    long_desc = "a" * 300
    response = {
        "count": 1,
        "query": "test",
        "feeds": [
            {"id": 1, "title": "Test", "description": long_desc, "url": "https://test"}
        ],
    }

    result = format_search_results(response)

    assert "..." in result
    assert len(result) < len(long_desc) + 100


@pytest.mark.asyncio
async def test_search_podcasts_tool_with_valid_query():
    """search_podcasts_tool should execute search and return formatted results."""
    mock_response = {
        "status": "true",
        "feeds": [
            {
                "id": 123,
                "title": "Python Weekly",
                "url": "https://example.com/feed",
                "description": "Python programming podcast",
                "author": "Test Author",
            }
        ],
        "count": 1,
        "query": "python",
    }

    with patch("main.search_podcasts", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = mock_response

        arguments = {"q": "python"}
        result = await search_podcasts_tool(arguments)

        assert len(result) > 0
        assert isinstance(result[0], TextContent)
        assert "Python Weekly" in result[0].text
        mock_search.assert_called_once()


@pytest.mark.asyncio
async def test_search_podcasts_tool_with_optional_params():
    """search_podcasts_tool should pass optional parameters to API client."""
    mock_response = {"status": "true", "feeds": [], "count": 0, "query": "test"}

    with patch("main.search_podcasts", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = mock_response

        arguments = {
            "q": "test",
            "max": 50,
            "clean": True,
            "fulltext": False,
        }
        await search_podcasts_tool(arguments)

        mock_search.assert_called_once()
        params = mock_search.call_args[0][2]
        assert params["q"] == "test"
        assert params.get("max") == 50
        assert params.get("clean") is True
        assert params.get("fulltext") is False


@pytest.mark.asyncio
async def test_search_podcasts_tool_handles_empty_results():
    """search_podcasts_tool should handle empty results gracefully."""
    mock_response = {
        "status": "true",
        "feeds": [],
        "count": 0,
        "query": "nonexistent",
        "description": "No matches found",
    }

    with patch("main.search_podcasts", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = mock_response

        arguments = {"q": "nonexistent"}
        result = await search_podcasts_tool(arguments)

        assert len(result) > 0
        assert isinstance(result[0], TextContent)
        assert "No matches" in result[0].text


@pytest.mark.asyncio
async def test_search_podcasts_tool_handles_http_errors():
    """search_podcasts_tool should handle HTTP errors gracefully."""
    with patch("main.search_podcasts", new_callable=AsyncMock) as mock_search:
        mock_search.side_effect = httpx.HTTPError("Network error")

        arguments = {"q": "test"}
        result = await search_podcasts_tool(arguments)

        assert len(result) > 0
        assert isinstance(result[0], TextContent)
        assert "Error" in result[0].text
        assert "Network error" in result[0].text


@pytest.mark.asyncio
async def test_search_podcasts_tool_handles_auth_errors():
    """search_podcasts_tool should handle authentication errors."""
    from unittest.mock import Mock

    mock_response = Mock()
    mock_response.status_code = 401

    with patch("main.search_podcasts", new_callable=AsyncMock) as mock_search:
        mock_search.side_effect = httpx.HTTPStatusError(
            "Unauthorized", request=Mock(), response=mock_response
        )

        arguments = {"q": "test"}
        result = await search_podcasts_tool(arguments)

        assert len(result) > 0
        assert isinstance(result[0], TextContent)
        assert "Error" in result[0].text
        assert "401" in result[0].text or "credentials" in result[0].text.lower()


@pytest.mark.asyncio
async def test_search_podcasts_tool_handles_unexpected_errors():
    """search_podcasts_tool should handle unexpected errors gracefully."""
    with patch("main.search_podcasts", new_callable=AsyncMock) as mock_search:
        mock_search.side_effect = ValueError("Unexpected error")

        arguments = {"q": "test"}
        result = await search_podcasts_tool(arguments)

        assert len(result) > 0
        assert isinstance(result[0], TextContent)
        assert "Error" in result[0].text
