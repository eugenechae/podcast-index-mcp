import os
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from mcp.types import TextContent

os.environ["PODCAST_INDEX_API_KEY"] = "test_key"
os.environ["PODCAST_INDEX_API_SECRET"] = "test_secret"

from podcast_index.main import (
    format_episode_details,
    format_episode_results,
    format_podcast_details,
    format_search_results,
    get_episode_details_tool,
    get_episodes_tool,
    get_podcast_details_tool,
    search_episodes_by_person_tool,
    search_podcasts_by_title_tool,
    search_podcasts_tool,
)


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


def test_format_search_results_does_not_truncate_descriptions():
    """format_search_results should not truncate descriptions - API handles that."""
    long_desc = "a" * 300
    response = {
        "count": 1,
        "query": "test",
        "feeds": [
            {"id": 1, "title": "Test", "description": long_desc, "url": "https://test"}
        ],
    }

    result = format_search_results(response)

    assert long_desc in result


def test_format_search_results_with_minimal_feed_data():
    """format_search_results should handle feeds with only required fields."""
    response = {
        "count": 1,
        "query": "minimal",
        "feeds": [
            {"id": 123, "title": "Minimal Podcast"}
            # Missing: author, description, url
        ],
    }

    result = format_search_results(response)

    assert "Minimal Podcast" in result
    assert "1 podcast(s)" in result
    assert "minimal" in result
    assert "Podcast Index ID: 123" in result


def test_format_search_results_includes_all_api_fields():
    """format_search_results should include all fields from API response."""
    response = {
        "count": 1,
        "query": "test",
        "feeds": [
            {
                "id": 123,
                "title": "Test Podcast",
                "url": "https://example.com/feed.xml",
                "originalUrl": "https://original.example.com/feed.xml",
                "link": "https://example.com",
                "description": "Podcast description",
                "author": "Test Author",
                "ownerName": "Test Owner",
                "image": "https://example.com/image.jpg",
                "artwork": "https://example.com/artwork.jpg",
                "lastUpdateTime": 1609459200,
                "lastCrawlTime": 1609459100,
                "lastParseTime": 1609459000,
                "lastGoodHttpStatusTime": 1609458900,
                "lastHttpStatus": 200,
                "contentType": "application/rss+xml",
                "itunesId": 123456789,
                "generator": "Podcast Generator 1.0",
                "language": "en",
                "type": 0,
                "dead": 0,
                "crawlErrors": 0,
                "parseErrors": 0,
            }
        ],
    }

    result = format_search_results(response)

    assert "Test Podcast" in result
    assert "Test Author" in result
    assert "Test Owner" in result
    assert "Podcast description" in result
    assert "https://example.com/feed.xml" in result
    assert "https://original.example.com/feed.xml" in result
    assert "https://example.com" in result
    assert "https://example.com/image.jpg" in result
    assert "https://example.com/artwork.jpg" in result
    assert "Podcast Index ID: 123" in result
    assert "123456789" in result
    assert "application/rss+xml" in result
    assert "en" in result


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

    with patch(
        "podcast_index.main.search_podcasts", new_callable=AsyncMock
    ) as mock_search:
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

    with patch(
        "podcast_index.main.search_podcasts", new_callable=AsyncMock
    ) as mock_search:
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

    with patch(
        "podcast_index.main.search_podcasts", new_callable=AsyncMock
    ) as mock_search:
        mock_search.return_value = mock_response

        arguments = {"q": "nonexistent"}
        result = await search_podcasts_tool(arguments)

        assert len(result) > 0
        assert isinstance(result[0], TextContent)
        assert "No matches" in result[0].text


@pytest.mark.asyncio
async def test_search_podcasts_tool_handles_http_errors():
    """search_podcasts_tool should handle HTTP errors gracefully."""
    with patch(
        "podcast_index.main.search_podcasts", new_callable=AsyncMock
    ) as mock_search:
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

    with patch(
        "podcast_index.main.search_podcasts", new_callable=AsyncMock
    ) as mock_search:
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
async def test_search_podcasts_tool_handles_server_errors():
    """search_podcasts_tool should handle server errors (500, 503, etc.)."""
    from unittest.mock import Mock

    mock_response = Mock()
    mock_response.status_code = 500

    with patch(
        "podcast_index.main.search_podcasts", new_callable=AsyncMock
    ) as mock_search:
        mock_search.side_effect = httpx.HTTPStatusError(
            "Internal Server Error", request=Mock(), response=mock_response
        )

        arguments = {"q": "test"}
        result = await search_podcasts_tool(arguments)

        assert len(result) > 0
        assert isinstance(result[0], TextContent)
        assert "Error" in result[0].text
        assert "500" in result[0].text


@pytest.mark.asyncio
async def test_search_podcasts_tool_handles_unexpected_errors():
    """search_podcasts_tool should handle unexpected errors gracefully."""
    with patch(
        "podcast_index.main.search_podcasts", new_callable=AsyncMock
    ) as mock_search:
        mock_search.side_effect = ValueError("Unexpected error")

        arguments = {"q": "test"}
        result = await search_podcasts_tool(arguments)

        assert len(result) > 0
        assert isinstance(result[0], TextContent)
        assert "Error" in result[0].text


@pytest.mark.asyncio
async def test_search_podcasts_by_title_tool_with_valid_query():
    """search_podcasts_by_title_tool should execute search and return formatted results."""
    mock_response = {
        "status": "true",
        "feeds": [
            {
                "id": 456,
                "title": "Serial",
                "url": "https://example.com/serial",
                "description": "Investigative journalism podcast",
                "author": "Sarah Koenig",
            }
        ],
        "count": 1,
        "query": "Serial",
    }

    with patch(
        "podcast_index.main.search_podcasts_by_title", new_callable=AsyncMock
    ) as mock_search:
        mock_search.return_value = mock_response

        arguments = {"q": "Serial"}
        result = await search_podcasts_by_title_tool(arguments)

        assert len(result) > 0
        assert isinstance(result[0], TextContent)
        assert "Serial" in result[0].text
        mock_search.assert_called_once()


@pytest.mark.asyncio
async def test_search_podcasts_by_title_tool_with_optional_params():
    """search_podcasts_by_title_tool should pass optional parameters to API client."""
    mock_response = {"status": "true", "feeds": [], "count": 0, "query": "test"}

    with patch(
        "podcast_index.main.search_podcasts_by_title", new_callable=AsyncMock
    ) as mock_search:
        mock_search.return_value = mock_response

        arguments = {
            "q": "test",
            "max": 25,
            "val": "lightning",
            "clean": True,
            "fulltext": True,
            "similar": False,
        }
        await search_podcasts_by_title_tool(arguments)

        mock_search.assert_called_once()
        params = mock_search.call_args[0][2]
        assert params["q"] == "test"
        assert params.get("max") == 25
        assert params.get("val") == "lightning"
        assert params.get("clean") is True
        assert params.get("fulltext") is True
        assert params.get("similar") is False


@pytest.mark.asyncio
async def test_search_podcasts_by_title_tool_handles_empty_results():
    """search_podcasts_by_title_tool should handle empty results gracefully."""
    mock_response = {
        "status": "true",
        "feeds": [],
        "count": 0,
        "query": "nonexistent",
        "description": "No matches found",
    }

    with patch(
        "podcast_index.main.search_podcasts_by_title", new_callable=AsyncMock
    ) as mock_search:
        mock_search.return_value = mock_response

        arguments = {"q": "nonexistent"}
        result = await search_podcasts_by_title_tool(arguments)

        assert len(result) > 0
        assert isinstance(result[0], TextContent)
        assert "No matches" in result[0].text


@pytest.mark.asyncio
async def test_search_podcasts_by_title_tool_handles_http_errors():
    """search_podcasts_by_title_tool should handle HTTP errors gracefully."""
    with patch(
        "podcast_index.main.search_podcasts_by_title", new_callable=AsyncMock
    ) as mock_search:
        mock_search.side_effect = httpx.HTTPError("Network error")

        arguments = {"q": "test"}
        result = await search_podcasts_by_title_tool(arguments)

        assert len(result) > 0
        assert isinstance(result[0], TextContent)
        assert "Error" in result[0].text
        assert "Network error" in result[0].text


@pytest.mark.asyncio
async def test_search_podcasts_by_title_tool_handles_auth_errors():
    """search_podcasts_by_title_tool should handle authentication errors."""
    from unittest.mock import Mock

    mock_response = Mock()
    mock_response.status_code = 401

    with patch(
        "podcast_index.main.search_podcasts_by_title", new_callable=AsyncMock
    ) as mock_search:
        mock_search.side_effect = httpx.HTTPStatusError(
            "Unauthorized", request=Mock(), response=mock_response
        )

        arguments = {"q": "test"}
        result = await search_podcasts_by_title_tool(arguments)

        assert len(result) > 0
        assert isinstance(result[0], TextContent)
        assert "Error" in result[0].text
        assert "401" in result[0].text or "credentials" in result[0].text.lower()


@pytest.mark.asyncio
async def test_search_podcasts_by_title_tool_handles_unexpected_errors():
    """search_podcasts_by_title_tool should handle unexpected errors gracefully."""
    with patch(
        "podcast_index.main.search_podcasts_by_title", new_callable=AsyncMock
    ) as mock_search:
        mock_search.side_effect = ValueError("Unexpected error")

        arguments = {"q": "test"}
        result = await search_podcasts_by_title_tool(arguments)

        assert len(result) > 0
        assert isinstance(result[0], TextContent)
        assert "Error" in result[0].text


def test_format_episode_results_with_results():
    """format_episode_results should format episodes into readable text."""
    response = {
        "count": 2,
        "query": "Adam Curry",
        "items": [
            {
                "id": 123,
                "title": "Episode 1",
                "feedTitle": "No Agenda",
                "description": "An episode about podcasting",
                "feedId": 456,
            },
            {
                "id": 789,
                "title": "Episode 2",
                "feedTitle": "The Bitcoin Podcast",
                "description": "Discussion about Bitcoin",
            },
        ],
    }

    result = format_episode_results(response)

    assert "2 episode(s)" in result
    assert "Episode 1" in result
    assert "Episode 2" in result
    assert "No Agenda" in result
    assert "The Bitcoin Podcast" in result


def test_format_episode_results_with_empty_results():
    """format_episode_results should handle empty results."""
    response = {"count": 0, "query": "nonexistent", "items": []}

    result = format_episode_results(response)

    assert "No matches" in result
    assert "nonexistent" in result


def test_format_episode_results_does_not_truncate_descriptions():
    """format_episode_results should not truncate descriptions - API handles that."""
    long_desc = "a" * 300
    response = {
        "count": 1,
        "query": "test",
        "items": [
            {
                "id": 1,
                "title": "Test Episode",
                "feedTitle": "Test Podcast",
                "description": long_desc,
            }
        ],
    }

    result = format_episode_results(response)

    assert long_desc in result


def test_format_episode_results_with_minimal_episode_data():
    """format_episode_results should handle episodes with only required fields."""
    response = {
        "count": 1,
        "query": "minimal",
        "items": [{"id": 123, "title": "Minimal Episode"}],
    }

    result = format_episode_results(response)

    assert "Minimal Episode" in result
    assert "1 episode(s)" in result
    assert "Episode ID: 123" in result


def test_format_episode_results_includes_all_api_fields():
    """format_episode_results should include all fields from API response."""
    response = {
        "count": 1,
        "query": "test",
        "items": [
            {
                "id": 123,
                "title": "Test Episode",
                "feedTitle": "Test Podcast",
                "description": "Episode description",
                "feedId": 456,
                "datePublished": 1609459200,
                "datePublishedPretty": "January 01, 2021 12:00am",
                "duration": 3600,
                "enclosureUrl": "https://example.com/episode.mp3",
                "enclosureType": "audio/mpeg",
                "enclosureLength": 52428800,
                "link": "https://example.com/episode",
                "image": "https://example.com/episode.jpg",
                "feedImage": "https://example.com/feed.jpg",
                "feedUrl": "https://example.com/feed.xml",
                "feedAuthor": "Test Author",
                "chaptersUrl": "https://example.com/chapters.json",
                "transcriptUrl": "https://example.com/transcript.json",
            }
        ],
    }

    result = format_episode_results(response)

    assert "Test Episode" in result
    assert "Test Podcast" in result
    assert "Episode description" in result
    assert "Episode ID: 123" in result
    assert "Podcast ID: 456" in result
    assert "1609459200" in result or "January 01, 2021" in result
    assert "3600" in result or "1:00:00" in result or "1 hour" in result
    assert "https://example.com/episode.mp3" in result
    assert "audio/mpeg" in result
    assert "52428800" in result or "50" in result
    assert "https://example.com/episode" in result
    assert "https://example.com/episode.jpg" in result
    assert "https://example.com/feed.jpg" in result
    assert "https://example.com/feed.xml" in result
    assert "Test Author" in result
    assert "https://example.com/chapters.json" in result
    assert "https://example.com/transcript.json" in result


@pytest.mark.asyncio
async def test_search_episodes_by_person_tool_with_valid_query():
    """search_episodes_by_person_tool should execute search and return formatted results."""
    mock_response = {
        "status": "true",
        "items": [
            {
                "id": 123,
                "title": "Interview with Adam Curry",
                "feedTitle": "No Agenda",
                "description": "Discussing podcasting 2.0",
                "feedId": 456,
            }
        ],
        "count": 1,
        "query": "Adam Curry",
    }

    with patch(
        "podcast_index.main.search_episodes_by_person", new_callable=AsyncMock
    ) as mock_search:
        mock_search.return_value = mock_response

        arguments = {"q": "Adam Curry"}
        result = await search_episodes_by_person_tool(arguments)

        assert len(result) > 0
        assert isinstance(result[0], TextContent)
        assert "Adam Curry" in result[0].text or "Interview" in result[0].text
        mock_search.assert_called_once()


@pytest.mark.asyncio
async def test_search_episodes_by_person_tool_with_optional_params():
    """search_episodes_by_person_tool should pass optional parameters to API client."""
    mock_response = {"status": "true", "items": [], "count": 0, "query": "test"}

    with patch(
        "podcast_index.main.search_episodes_by_person", new_callable=AsyncMock
    ) as mock_search:
        mock_search.return_value = mock_response

        arguments = {"q": "test", "max": 30, "fulltext": True}
        await search_episodes_by_person_tool(arguments)

        mock_search.assert_called_once()
        params = mock_search.call_args[0][2]
        assert params["q"] == "test"
        assert params.get("max") == 30
        assert params.get("fulltext") is True


@pytest.mark.asyncio
async def test_search_episodes_by_person_tool_handles_empty_results():
    """search_episodes_by_person_tool should handle empty results gracefully."""
    mock_response = {
        "status": "true",
        "items": [],
        "count": 0,
        "query": "nonexistent",
        "description": "No matches found",
    }

    with patch(
        "podcast_index.main.search_episodes_by_person", new_callable=AsyncMock
    ) as mock_search:
        mock_search.return_value = mock_response

        arguments = {"q": "nonexistent"}
        result = await search_episodes_by_person_tool(arguments)

        assert len(result) > 0
        assert isinstance(result[0], TextContent)
        assert "No matches" in result[0].text


@pytest.mark.asyncio
async def test_search_episodes_by_person_tool_handles_http_errors():
    """search_episodes_by_person_tool should handle HTTP errors gracefully."""
    with patch(
        "podcast_index.main.search_episodes_by_person", new_callable=AsyncMock
    ) as mock_search:
        mock_search.side_effect = httpx.HTTPError("Network error")

        arguments = {"q": "test"}
        result = await search_episodes_by_person_tool(arguments)

        assert len(result) > 0
        assert isinstance(result[0], TextContent)
        assert "Error" in result[0].text
        assert "Network error" in result[0].text


@pytest.mark.asyncio
async def test_search_episodes_by_person_tool_handles_auth_errors():
    """search_episodes_by_person_tool should handle authentication errors."""
    from unittest.mock import Mock

    mock_response = Mock()
    mock_response.status_code = 401

    with patch(
        "podcast_index.main.search_episodes_by_person", new_callable=AsyncMock
    ) as mock_search:
        mock_search.side_effect = httpx.HTTPStatusError(
            "Unauthorized", request=Mock(), response=mock_response
        )

        arguments = {"q": "test"}
        result = await search_episodes_by_person_tool(arguments)

        assert len(result) > 0
        assert isinstance(result[0], TextContent)
        assert "Error" in result[0].text
        assert "401" in result[0].text or "credentials" in result[0].text.lower()


@pytest.mark.asyncio
async def test_search_episodes_by_person_tool_handles_unexpected_errors():
    """search_episodes_by_person_tool should handle unexpected errors gracefully."""
    with patch(
        "podcast_index.main.search_episodes_by_person", new_callable=AsyncMock
    ) as mock_search:
        mock_search.side_effect = ValueError("Unexpected error")

        arguments = {"q": "test"}
        result = await search_episodes_by_person_tool(arguments)

        assert len(result) > 0
        assert isinstance(result[0], TextContent)
        assert "Error" in result[0].text


@pytest.mark.asyncio
async def test_get_episodes_tool_with_valid_id():
    """get_episodes_tool should retrieve episodes and return formatted results."""
    mock_response = {
        "status": "true",
        "items": [
            {
                "id": 123,
                "title": "Episode 1",
                "description": "First episode",
                "feedId": 456,
            }
        ],
        "count": 1,
        "feed": {"id": 456, "title": "Test Podcast"},
    }

    with patch("podcast_index.main.get_episodes", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response

        arguments = {"id": 456}
        result = await get_episodes_tool(arguments)

        assert len(result) > 0
        assert isinstance(result[0], TextContent)
        assert "Episode 1" in result[0].text
        mock_get.assert_called_once()


@pytest.mark.asyncio
async def test_get_episodes_tool_handles_http_errors():
    """get_episodes_tool should handle HTTP errors gracefully."""
    with patch("podcast_index.main.get_episodes", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = httpx.HTTPError("Network error")

        arguments = {"id": 456}
        result = await get_episodes_tool(arguments)

        assert len(result) > 0
        assert isinstance(result[0], TextContent)
        assert "Error" in result[0].text


def test_format_podcast_details_with_complete_data():
    """format_podcast_details should format podcast details into readable text."""
    response = {
        "status": "true",
        "feed": {
            "id": 920666,
            "title": "No Agenda",
            "description": "The best podcast in the universe",
            "author": "Adam Curry and John C. Dvorak",
            "url": "https://example.com/feed",
            "link": "https://noagendashow.net",
            "image": "https://example.com/image.jpg",
        },
    }

    result = format_podcast_details(response)

    assert "No Agenda" in result
    assert "Adam Curry" in result
    assert "The best podcast in the universe" in result


def test_format_podcast_details_with_minimal_data():
    """format_podcast_details should handle minimal podcast data."""
    response = {"status": "true", "feed": {"id": 123, "title": "Test Podcast"}}

    result = format_podcast_details(response)

    assert "Test Podcast" in result
    assert "Podcast Index ID: 123" in result


def test_format_podcast_details_includes_all_api_fields():
    """format_podcast_details should include all fields from API response."""
    response = {
        "status": "true",
        "feed": {
            "id": 123,
            "title": "Test Podcast",
            "url": "https://example.com/feed.xml",
            "originalUrl": "https://original.example.com/feed.xml",
            "link": "https://example.com",
            "description": "Detailed podcast description",
            "author": "Test Author",
            "ownerName": "Test Owner",
            "image": "https://example.com/image.jpg",
            "artwork": "https://example.com/artwork.jpg",
            "lastUpdateTime": 1609459200,
            "lastCrawlTime": 1609459100,
            "lastParseTime": 1609459000,
            "lastGoodHttpStatusTime": 1609458900,
            "lastHttpStatus": 200,
            "contentType": "application/rss+xml",
            "itunesId": 123456789,
            "generator": "Podcast Generator 1.0",
            "language": "en",
            "type": 0,
            "dead": 0,
            "crawlErrors": 0,
            "parseErrors": 0,
            "categories": {"1": "Technology", "2": "News"},
            "locked": 0,
            "explicit": False,
            "episodeCount": 100,
            "imageUrlHash": 123456,
        },
    }

    result = format_podcast_details(response)

    assert "Test Podcast" in result
    assert "Test Author" in result
    assert "Test Owner" in result
    assert "Detailed podcast description" in result
    assert "https://example.com/feed.xml" in result
    assert "https://original.example.com/feed.xml" in result
    assert "https://example.com" in result
    assert "https://example.com/image.jpg" in result
    assert "https://example.com/artwork.jpg" in result
    assert "Podcast Index ID: 123" in result
    assert "123456789" in result
    assert "application/rss+xml" in result
    assert "en" in result
    assert "100" in result


@pytest.mark.asyncio
async def test_get_podcast_details_tool_with_valid_id():
    """get_podcast_details_tool should retrieve podcast details and return formatted results."""
    mock_response = {
        "status": "true",
        "feed": {
            "id": 920666,
            "title": "No Agenda",
            "description": "The best podcast in the universe",
            "author": "Adam Curry",
        },
    }

    with patch(
        "podcast_index.main.get_podcast_details", new_callable=AsyncMock
    ) as mock_get:
        mock_get.return_value = mock_response

        arguments = {"id": 920666}
        result = await get_podcast_details_tool(arguments)

        assert len(result) > 0
        assert isinstance(result[0], TextContent)
        assert "No Agenda" in result[0].text
        mock_get.assert_called_once()


@pytest.mark.asyncio
async def test_get_podcast_details_tool_handles_http_errors():
    """get_podcast_details_tool should handle HTTP errors gracefully."""
    with patch(
        "podcast_index.main.get_podcast_details", new_callable=AsyncMock
    ) as mock_get:
        mock_get.side_effect = httpx.HTTPError("Network error")

        arguments = {"id": 123}
        result = await get_podcast_details_tool(arguments)

        assert len(result) > 0
        assert isinstance(result[0], TextContent)
        assert "Error" in result[0].text


def test_format_episode_details_with_complete_data():
    """format_episode_details should format episode details into readable text."""
    response = {
        "status": "true",
        "episode": {
            "id": 16795090,
            "title": "Special Episode",
            "description": "An amazing episode about podcasting",
            "feedTitle": "No Agenda",
            "feedId": 920666,
            "link": "https://example.com/episode",
        },
    }

    result = format_episode_details(response)

    assert "Special Episode" in result
    assert "No Agenda" in result
    assert "amazing episode" in result


def test_format_episode_details_with_minimal_data():
    """format_episode_details should handle minimal episode data."""
    response = {"status": "true", "episode": {"id": 123, "title": "Test Episode"}}

    result = format_episode_details(response)

    assert "Test Episode" in result
    assert "Episode ID: 123" in result


def test_format_episode_details_includes_all_api_fields():
    """format_episode_details should include all fields from API response."""
    response = {
        "status": "true",
        "episode": {
            "id": 123,
            "title": "Test Episode",
            "feedTitle": "Test Podcast",
            "description": "Detailed episode description",
            "feedId": 456,
            "datePublished": 1609459200,
            "datePublishedPretty": "January 01, 2021 12:00am",
            "duration": 3600,
            "enclosureUrl": "https://example.com/episode.mp3",
            "enclosureType": "audio/mpeg",
            "enclosureLength": 52428800,
            "link": "https://example.com/episode",
            "image": "https://example.com/episode.jpg",
            "feedImage": "https://example.com/feed.jpg",
            "feedUrl": "https://example.com/feed.xml",
            "feedAuthor": "Test Author",
            "chaptersUrl": "https://example.com/chapters.json",
            "transcriptUrl": "https://example.com/transcript.json",
            "season": 1,
            "episode": 5,
            "episodeType": "full",
            "explicit": 0,
            "feedItunesId": 123456789,
            "feedLanguage": "en",
            "persons": [
                {"name": "John Doe", "role": "host"},
                {"name": "Jane Smith", "role": "guest"},
            ],
            "socialInteract": [
                {
                    "protocol": "activitypub",
                    "uri": "https://mastodon.example/@user",
                    "accountId": "@user@mastodon.example",
                }
            ],
        },
    }

    result = format_episode_details(response)

    assert "Test Episode" in result
    assert "Test Podcast" in result
    assert "Detailed episode description" in result
    assert "Episode ID: 123" in result
    assert "Podcast ID: 456" in result
    assert "1609459200" in result or "January 01, 2021" in result
    assert "3600" in result or "1:00:00" in result or "1 hour" in result
    assert "https://example.com/episode.mp3" in result
    assert "audio/mpeg" in result
    assert "52428800" in result or "50" in result
    assert "https://example.com/episode" in result
    assert "https://example.com/episode.jpg" in result
    assert "https://example.com/feed.jpg" in result
    assert "https://example.com/feed.xml" in result
    assert "Test Author" in result
    assert "https://example.com/chapters.json" in result
    assert "https://example.com/transcript.json" in result
    assert "Season: 1" in result or "season: 1" in result
    assert "Episode: 5" in result or "episode: 5" in result
    assert "John Doe" in result
    assert "Jane Smith" in result


@pytest.mark.asyncio
async def test_get_episode_details_tool_with_valid_id():
    """get_episode_details_tool should retrieve episode details and return formatted results."""
    mock_response = {
        "status": "true",
        "episode": {
            "id": 16795090,
            "title": "Special Episode",
            "description": "An amazing episode",
            "feedTitle": "No Agenda",
        },
    }

    with patch(
        "podcast_index.main.get_episode_details", new_callable=AsyncMock
    ) as mock_get:
        mock_get.return_value = mock_response

        arguments = {"id": 16795090}
        result = await get_episode_details_tool(arguments)

        assert len(result) > 0
        assert isinstance(result[0], TextContent)
        assert "Special Episode" in result[0].text
        mock_get.assert_called_once()


@pytest.mark.asyncio
async def test_get_episode_details_tool_handles_http_errors():
    """get_episode_details_tool should handle HTTP errors gracefully."""
    with patch(
        "podcast_index.main.get_episode_details", new_callable=AsyncMock
    ) as mock_get:
        mock_get.side_effect = httpx.HTTPError("Network error")

        arguments = {"id": 123}
        result = await get_episode_details_tool(arguments)

        assert len(result) > 0
        assert isinstance(result[0], TextContent)
        assert "Error" in result[0].text
