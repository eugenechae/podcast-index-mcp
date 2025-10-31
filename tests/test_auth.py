from unittest.mock import patch


from podcast_index.auth import generate_auth_headers


def test_generate_auth_headers_includes_required_headers():
    """Auth headers should include X-Auth-Key, X-Auth-Date, Authorization, and User-Agent."""
    api_key = "test_key_123"
    api_secret = "test_secret_456"

    headers = generate_auth_headers(api_key, api_secret)

    assert "X-Auth-Key" in headers
    assert "X-Auth-Date" in headers
    assert "Authorization" in headers
    assert "User-Agent" in headers


def test_generate_auth_headers_uses_provided_api_key():
    """X-Auth-Key header should contain the provided API key."""
    api_key = "my_unique_key"
    api_secret = "secret"

    headers = generate_auth_headers(api_key, api_secret)

    assert headers["X-Auth-Key"] == api_key


def test_generate_auth_headers_uses_current_timestamp():
    """X-Auth-Date should be current unix timestamp as string."""
    api_key = "key"
    api_secret = "secret"

    with patch("time.time", return_value=1234567890.0):
        headers = generate_auth_headers(api_key, api_secret)

    assert headers["X-Auth-Date"] == "1234567890"


def test_generate_auth_headers_creates_valid_authorization_hash():
    """Authorization header should be SHA-1 hash of apiKey+apiSecret+timestamp."""
    api_key = "test_key"
    api_secret = "test_secret"
    timestamp = "1234567890"

    # Expected: SHA-1 of "test_keytest_secret1234567890"
    # Using Python's hashlib to compute expected value
    import hashlib

    expected_hash = hashlib.sha1(
        f"{api_key}{api_secret}{timestamp}".encode()
    ).hexdigest()

    with patch("time.time", return_value=1234567890.0):
        headers = generate_auth_headers(api_key, api_secret)

    assert headers["Authorization"] == expected_hash


def test_generate_auth_headers_includes_user_agent():
    """User-Agent header should identify the application."""
    api_key = "key"
    api_secret = "secret"

    headers = generate_auth_headers(api_key, api_secret)

    assert "podcast-index-mcp" in headers["User-Agent"].lower()


def test_generate_auth_headers_with_custom_user_agent():
    """Should allow custom user agent to be specified."""
    api_key = "key"
    api_secret = "secret"
    custom_user_agent = "MyApp/1.0"

    headers = generate_auth_headers(api_key, api_secret, user_agent=custom_user_agent)

    assert headers["User-Agent"] == custom_user_agent


def test_generate_auth_headers_different_timestamps_produce_different_hashes():
    """Different timestamps should produce different authorization hashes."""
    api_key = "key"
    api_secret = "secret"

    with patch("time.time", return_value=1000.0):
        headers1 = generate_auth_headers(api_key, api_secret)

    with patch("time.time", return_value=2000.0):
        headers2 = generate_auth_headers(api_key, api_secret)

    assert headers1["Authorization"] != headers2["Authorization"]
    assert headers1["X-Auth-Date"] != headers2["X-Auth-Date"]
