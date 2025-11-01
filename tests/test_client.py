from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from podcast_index.client import (
    GetEpisodeDetailsParams,
    GetEpisodesParams,
    GetPodcastDetailsParams,
    SearchByPersonParams,
    SearchByTitleParams,
    SearchParams,
    build_episode_details_url,
    build_episodes_url,
    build_podcast_details_url,
    build_search_by_person_url,
    build_search_by_title_url,
    build_search_url,
    get_episode_details,
    get_episodes,
    get_podcast_details,
    search_episodes_by_person,
    search_podcasts,
    search_podcasts_by_title,
)


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


def test_build_search_by_title_url_with_required_params():
    """Search by title URL should include base URL and query parameter."""
    params = SearchByTitleParams(q="Serial")

    url = build_search_by_title_url(params)

    assert url.startswith("https://api.podcastindex.org/api/1.0/search/bytitle")
    assert "q=Serial" in url


def test_build_search_by_title_url_with_max_results():
    """Search by title URL should include max parameter when specified."""
    params = SearchByTitleParams(q="test", max=25)

    url = build_search_by_title_url(params)

    assert "max=25" in url


def test_build_search_by_title_url_with_value_filter():
    """Search by title URL should include val parameter for value block filtering."""
    params = SearchByTitleParams(q="test", val="lightning")

    url = build_search_by_title_url(params)

    assert "val=lightning" in url


def test_build_search_by_title_url_with_boolean_flags():
    """Search by title URL should include boolean flags when enabled."""
    params = SearchByTitleParams(q="test", clean=True, fulltext=True, similar=True)

    url = build_search_by_title_url(params)

    assert "clean=true" in url.lower()
    assert "fulltext=true" in url.lower()
    assert "similar=true" in url.lower()


def test_build_search_by_title_url_omits_false_boolean_flags():
    """Search by title URL should not include boolean flags when False."""
    params = SearchByTitleParams(q="test", clean=False, fulltext=False)

    url = build_search_by_title_url(params)

    assert "clean" not in url
    assert "fulltext" not in url


def test_build_search_by_title_url_with_all_params():
    """Search by title URL should include all parameters when provided."""
    params = SearchByTitleParams(
        q="test query",
        max=50,
        val="lightning",
        clean=True,
        similar=True,
        fulltext=True,
    )

    url = build_search_by_title_url(params)

    assert "q=test" in url
    assert "max=50" in url
    assert "val=lightning" in url
    assert "clean=true" in url.lower()
    assert "similar=true" in url.lower()
    assert "fulltext=true" in url.lower()


@pytest.mark.asyncio
async def test_search_podcasts_by_title_makes_request_with_auth_headers():
    """search_podcasts_by_title should make HTTP request with authentication headers."""
    api_key = "test_key"
    api_secret = "test_secret"
    params = SearchByTitleParams(q="Serial")

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "status": "true",
        "feeds": [],
        "count": 0,
        "query": "Serial",
        "description": "Found matches for 'Serial'",
    }

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        await search_podcasts_by_title(api_key, api_secret, params)

        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args

        headers = call_args.kwargs["headers"]
        assert headers["X-Auth-Key"] == api_key
        assert "X-Auth-Date" in headers
        assert "Authorization" in headers
        assert "User-Agent" in headers


@pytest.mark.asyncio
async def test_search_podcasts_by_title_returns_successful_response():
    """search_podcasts_by_title should return parsed response data."""
    api_key = "test_key"
    api_secret = "test_secret"
    params = SearchByTitleParams(q="Serial")

    expected_response = {
        "status": "true",
        "feeds": [
            {
                "id": 456,
                "title": "Serial",
                "url": "https://example.com/serial",
                "description": "The Serial podcast",
            }
        ],
        "count": 1,
        "query": "Serial",
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

        result = await search_podcasts_by_title(api_key, api_secret, params)

        assert result == expected_response
        assert result["count"] == 1
        assert len(result["feeds"]) == 1


@pytest.mark.asyncio
async def test_search_podcasts_by_title_handles_http_errors():
    """search_podcasts_by_title should raise exception for HTTP errors."""
    api_key = "test_key"
    api_secret = "test_secret"
    params = SearchByTitleParams(q="test")

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get.side_effect = httpx.HTTPError("Network error")
        mock_client_class.return_value = mock_client

        with pytest.raises(httpx.HTTPError):
            await search_podcasts_by_title(api_key, api_secret, params)


@pytest.mark.asyncio
async def test_search_podcasts_by_title_with_empty_results():
    """search_podcasts_by_title should handle empty search results."""
    api_key = "test_key"
    api_secret = "test_secret"
    params = SearchByTitleParams(q="nonexistent")

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

        result = await search_podcasts_by_title(api_key, api_secret, params)

        assert result["count"] == 0
        assert result["feeds"] == []


def test_build_search_by_person_url_with_required_params():
    """Search by person URL should include base URL and query parameter."""
    params = SearchByPersonParams(q="Adam Curry")

    url = build_search_by_person_url(params)

    assert url.startswith("https://api.podcastindex.org/api/1.0/search/byperson")
    assert "q=Adam" in url or "q=Adam+Curry" in url or "q=Adam%20Curry" in url


def test_build_search_by_person_url_with_max_results():
    """Search by person URL should include max parameter when specified."""
    params = SearchByPersonParams(q="test", max=30)

    url = build_search_by_person_url(params)

    assert "max=30" in url


def test_build_search_by_person_url_with_fulltext():
    """Search by person URL should include fulltext parameter when enabled."""
    params = SearchByPersonParams(q="test", fulltext=True)

    url = build_search_by_person_url(params)

    assert "fulltext=true" in url.lower()


def test_build_search_by_person_url_omits_false_fulltext():
    """Search by person URL should not include fulltext when False."""
    params = SearchByPersonParams(q="test", fulltext=False)

    url = build_search_by_person_url(params)

    assert "fulltext" not in url


def test_build_search_by_person_url_with_all_params():
    """Search by person URL should include all parameters when provided."""
    params = SearchByPersonParams(q="Adam Curry", max=50, fulltext=True)

    url = build_search_by_person_url(params)

    assert "q=Adam" in url
    assert "max=50" in url
    assert "fulltext=true" in url.lower()


@pytest.mark.asyncio
async def test_search_episodes_by_person_makes_request_with_auth_headers():
    """search_episodes_by_person should make HTTP request with authentication headers."""
    api_key = "test_key"
    api_secret = "test_secret"
    params = SearchByPersonParams(q="Adam Curry")

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "status": "true",
        "items": [],
        "count": 0,
        "query": "Adam Curry",
        "description": "Found matches for 'Adam Curry'",
    }

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        await search_episodes_by_person(api_key, api_secret, params)

        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args

        headers = call_args.kwargs["headers"]
        assert headers["X-Auth-Key"] == api_key
        assert "X-Auth-Date" in headers
        assert "Authorization" in headers
        assert "User-Agent" in headers


@pytest.mark.asyncio
async def test_search_episodes_by_person_returns_successful_response():
    """search_episodes_by_person should return parsed response data."""
    api_key = "test_key"
    api_secret = "test_secret"
    params = SearchByPersonParams(q="Adam Curry")

    expected_response = {
        "status": "true",
        "items": [
            {
                "id": 789,
                "title": "Episode about Adam Curry",
                "feedTitle": "No Agenda",
                "description": "Discussing Adam Curry",
            }
        ],
        "count": 1,
        "query": "Adam Curry",
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

        result = await search_episodes_by_person(api_key, api_secret, params)

        assert result == expected_response
        assert result["count"] == 1
        assert len(result["items"]) == 1


@pytest.mark.asyncio
async def test_search_episodes_by_person_handles_http_errors():
    """search_episodes_by_person should raise exception for HTTP errors."""
    api_key = "test_key"
    api_secret = "test_secret"
    params = SearchByPersonParams(q="test")

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get.side_effect = httpx.HTTPError("Network error")
        mock_client_class.return_value = mock_client

        with pytest.raises(httpx.HTTPError):
            await search_episodes_by_person(api_key, api_secret, params)


@pytest.mark.asyncio
async def test_search_episodes_by_person_with_empty_results():
    """search_episodes_by_person should handle empty search results."""
    api_key = "test_key"
    api_secret = "test_secret"
    params = SearchByPersonParams(q="nonexistent")

    expected_response = {
        "status": "true",
        "items": [],
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

        result = await search_episodes_by_person(api_key, api_secret, params)

        assert result["count"] == 0
        assert result["items"] == []


def test_build_episodes_url_with_required_params():
    """Episodes by feed ID URL should include base URL and ID parameter."""
    params = GetEpisodesParams(id=123456)

    url = build_episodes_url(params)

    assert url.startswith("https://api.podcastindex.org/api/1.0/episodes/byfeedid")
    assert "id=123456" in url


def test_build_episodes_url_with_all_params():
    """Episodes by feed ID URL should include all parameters when provided."""
    params = GetEpisodesParams(id=123, since=1609459200, max=50, fulltext=True)

    url = build_episodes_url(params)

    assert "id=123" in url
    assert "since=1609459200" in url
    assert "max=50" in url
    assert "fulltext=true" in url.lower()


@pytest.mark.asyncio
async def test_get_episodes_returns_successful_response():
    """get_episodes should return parsed response data."""
    api_key = "test_key"
    api_secret = "test_secret"
    params = GetEpisodesParams(id=123456)

    expected_response = {
        "status": "true",
        "items": [
            {
                "id": 789,
                "title": "Episode 1",
                "description": "First episode",
                "datePublished": 1609459200,
            }
        ],
        "count": 1,
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

        result = await get_episodes(api_key, api_secret, params)

        assert result == expected_response
        assert result["count"] == 1


@pytest.mark.asyncio
async def test_get_episodes_handles_http_errors():
    """get_episodes should raise exception for HTTP errors."""
    api_key = "test_key"
    api_secret = "test_secret"
    params = GetEpisodesParams(id=123)

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get.side_effect = httpx.HTTPError("Network error")
        mock_client_class.return_value = mock_client

        with pytest.raises(httpx.HTTPError):
            await get_episodes(api_key, api_secret, params)


def test_build_podcast_details_url_with_required_params():
    """Podcast details URL should include base URL and ID parameter."""
    params = GetPodcastDetailsParams(id=920666)

    url = build_podcast_details_url(params)

    assert url.startswith("https://api.podcastindex.org/api/1.0/podcasts/byfeedid")
    assert "id=920666" in url


@pytest.mark.asyncio
async def test_get_podcast_details_returns_successful_response():
    """get_podcast_details should return parsed response data."""
    api_key = "test_key"
    api_secret = "test_secret"
    params = GetPodcastDetailsParams(id=920666)

    expected_response = {
        "status": "true",
        "feed": {
            "id": 920666,
            "title": "No Agenda",
            "description": "The best podcast in the universe",
            "url": "https://example.com/feed",
        },
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

        result = await get_podcast_details(api_key, api_secret, params)

        assert result == expected_response
        assert result["feed"]["id"] == 920666


@pytest.mark.asyncio
async def test_get_podcast_details_handles_http_errors():
    """get_podcast_details should raise exception for HTTP errors."""
    api_key = "test_key"
    api_secret = "test_secret"
    params = GetPodcastDetailsParams(id=123)

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get.side_effect = httpx.HTTPError("Network error")
        mock_client_class.return_value = mock_client

        with pytest.raises(httpx.HTTPError):
            await get_podcast_details(api_key, api_secret, params)


def test_build_episode_details_url_with_required_params():
    """Episode details URL should include base URL and ID parameter."""
    params = GetEpisodeDetailsParams(id=16795090)

    url = build_episode_details_url(params)

    assert url.startswith("https://api.podcastindex.org/api/1.0/episodes/byid")
    assert "id=16795090" in url


def test_build_episode_details_url_with_fulltext():
    """Episode details URL should include fulltext parameter when enabled."""
    params = GetEpisodeDetailsParams(id=123, fulltext=True)

    url = build_episode_details_url(params)

    assert "id=123" in url
    assert "fulltext=true" in url.lower()


@pytest.mark.asyncio
async def test_get_episode_details_returns_successful_response():
    """get_episode_details should return parsed response data."""
    api_key = "test_key"
    api_secret = "test_secret"
    params = GetEpisodeDetailsParams(id=16795090)

    expected_response = {
        "status": "true",
        "episode": {
            "id": 16795090,
            "title": "Special Episode",
            "description": "An amazing episode",
            "feedId": 920666,
        },
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

        result = await get_episode_details(api_key, api_secret, params)

        assert result == expected_response
        assert result["episode"]["id"] == 16795090


@pytest.mark.asyncio
async def test_get_episode_details_handles_http_errors():
    """get_episode_details should raise exception for HTTP errors."""
    api_key = "test_key"
    api_secret = "test_secret"
    params = GetEpisodeDetailsParams(id=123)

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get.side_effect = httpx.HTTPError("Network error")
        mock_client_class.return_value = mock_client

        with pytest.raises(httpx.HTTPError):
            await get_episode_details(api_key, api_secret, params)
