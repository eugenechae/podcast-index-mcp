from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from podcast_index.client import SearchParams, build_search_url, search_podcasts


def test_build_search_url_with_required_params():
    """Search URL should include base URL and query parameter."""
    params = SearchParams(q="python programming")

    url = build_search_url(params)

    assert url.startswith("https://api.podcastindex.org/api/1.0/search/byterm")
    assert "q=python+programming" in url or "q=python%20programming" in url


def test_build_search_url_with_max_results():
    """Search URL should include max parameter when specified."""
    params = SearchParams(q="test", max=50)

    url = build_search_url(params)

    assert "max=50" in url


def test_build_search_url_with_value_filter():
    """Search URL should include val parameter for value block filtering."""
    params = SearchParams(q="test", val="lightning")

    url = build_search_url(params)

    assert "val=lightning" in url


def test_build_search_url_with_boolean_flags():
    """Search URL should include boolean flags when enabled."""
    params = SearchParams(q="test", clean=True, fulltext=True, aponly=True)

    url = build_search_url(params)

    assert "clean=true" in url.lower()
    assert "fulltext=true" in url.lower()
    assert "aponly=true" in url.lower()


def test_build_search_url_omits_false_boolean_flags():
    """Search URL should not include boolean flags when False."""
    params = SearchParams(q="test", clean=False, fulltext=False)

    url = build_search_url(params)

    assert "clean" not in url
    assert "fulltext" not in url


def test_build_search_url_with_all_params():
    """Search URL should include all parameters when provided."""
    params = SearchParams(
        q="test query",
        max=100,
        val="lightning",
        clean=True,
        similar=True,
        fulltext=True,
        aponly=True,
    )

    url = build_search_url(params)

    assert "q=test" in url
    assert "max=100" in url
    assert "val=lightning" in url
    assert "clean=true" in url.lower()
    assert "similar=true" in url.lower()
    assert "fulltext=true" in url.lower()
    assert "aponly=true" in url.lower()


@pytest.mark.asyncio
async def test_search_podcasts_makes_request_with_auth_headers():
    """search_podcasts should make HTTP request with authentication headers."""
    api_key = "test_key"
    api_secret = "test_secret"
    params = SearchParams(q="test")

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "status": "true",
        "feeds": [],
        "count": 0,
        "query": "test",
        "description": "Found matches for 'test'",
    }

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        await search_podcasts(api_key, api_secret, params)

        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args

        headers = call_args.kwargs["headers"]
        assert headers["X-Auth-Key"] == api_key
        assert "X-Auth-Date" in headers
        assert "Authorization" in headers
        assert "User-Agent" in headers


@pytest.mark.asyncio
async def test_search_podcasts_returns_successful_response():
    """search_podcasts should return parsed response data."""
    api_key = "test_key"
    api_secret = "test_secret"
    params = SearchParams(q="test")

    expected_response = {
        "status": "true",
        "feeds": [
            {
                "id": 123,
                "title": "Test Podcast",
                "url": "https://example.com/feed",
                "description": "A test podcast",
            }
        ],
        "count": 1,
        "query": "test",
        "description": "Found 1 match",
    }

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = expected_response

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        result = await search_podcasts(api_key, api_secret, params)

        assert result == expected_response
        assert result["count"] == 1
        assert len(result["feeds"]) == 1


@pytest.mark.asyncio
async def test_search_podcasts_handles_http_errors():
    """search_podcasts should raise exception for HTTP errors."""
    api_key = "test_key"
    api_secret = "test_secret"
    params = SearchParams(q="test")

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get.side_effect = httpx.HTTPError("Network error")
        mock_client_class.return_value = mock_client

        with pytest.raises(httpx.HTTPError):
            await search_podcasts(api_key, api_secret, params)


@pytest.mark.asyncio
async def test_search_podcasts_handles_unauthorized():
    """search_podcasts should handle 401 unauthorized responses."""
    api_key = "invalid_key"
    api_secret = "invalid_secret"
    params = SearchParams(q="test")

    mock_response = Mock()
    mock_response.status_code = 401
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Unauthorized", request=Mock(), response=mock_response
    )

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        with pytest.raises(httpx.HTTPStatusError):
            await search_podcasts(api_key, api_secret, params)


@pytest.mark.asyncio
async def test_search_podcasts_with_empty_results():
    """search_podcasts should handle empty search results."""
    api_key = "test_key"
    api_secret = "test_secret"
    params = SearchParams(q="nonexistent")

    expected_response = {
        "status": "true",
        "feeds": [],
        "count": 0,
        "query": "nonexistent",
        "description": "No matches found",
    }

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = expected_response

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        result = await search_podcasts(api_key, api_secret, params)

        assert result["count"] == 0
        assert result["feeds"] == []


@pytest.mark.asyncio
async def test_search_podcasts_handles_malformed_json():
    """search_podcasts should raise exception when API returns invalid JSON."""
    api_key = "test_key"
    api_secret = "test_secret"
    params = SearchParams(q="test")

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.side_effect = ValueError("Invalid JSON")

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        with pytest.raises(ValueError):
            await search_podcasts(api_key, api_secret, params)
