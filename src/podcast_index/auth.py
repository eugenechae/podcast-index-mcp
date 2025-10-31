"""Authentication utilities for Podcast Index API."""

import hashlib
import time


def generate_auth_headers(
    api_key: str, api_secret: str, user_agent: str | None = None
) -> dict[str, str]:
    """
    Generate authentication headers for Podcast Index API requests.

    The API requires:
    - X-Auth-Key: The API key
    - X-Auth-Date: Current unix timestamp
    - Authorization: SHA-1 hash of apiKey + apiSecret + timestamp
    - User-Agent: Application identifier

    Args:
        api_key: Podcast Index API key
        api_secret: Podcast Index API secret
        user_agent: Optional custom user agent string

    Returns:
        Dictionary of HTTP headers for authentication
    """
    timestamp = str(int(time.time()))

    auth_string = f"{api_key}{api_secret}{timestamp}"
    auth_hash = hashlib.sha1(auth_string.encode()).hexdigest()

    default_user_agent = "podcast-index-mcp/0.1.0"

    return {
        "X-Auth-Key": api_key,
        "X-Auth-Date": timestamp,
        "Authorization": auth_hash,
        "User-Agent": user_agent if user_agent is not None else default_user_agent,
    }
