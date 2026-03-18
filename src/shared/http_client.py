from __future__ import annotations

import random

import httpx

from src.config.settings import get_settings


def create_http_client(
    timeout: int = 30,
    headers: dict[str, str] | None = None,
    with_random_ua: bool = False,
) -> httpx.Client:
    """Create an httpx client with sensible defaults."""
    default_headers = headers or {}

    if with_random_ua:
        settings = get_settings()
        ua = random.choice(settings.scraping.user_agents)
        default_headers.setdefault("User-Agent", ua)

    return httpx.Client(
        timeout=httpx.Timeout(timeout),
        headers=default_headers,
        follow_redirects=True,
    )


def create_api_client(
    base_url: str,
    api_key: str,
    auth_header: str = "Authorization",
    auth_prefix: str = "Bearer ",
    timeout: int = 30,
) -> httpx.Client:
    """Create an httpx client pre-configured for API calls."""
    return httpx.Client(
        base_url=base_url,
        timeout=httpx.Timeout(timeout),
        headers={auth_header: f"{auth_prefix}{api_key}"},
        follow_redirects=True,
    )
