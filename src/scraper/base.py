from __future__ import annotations

import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx

from src.config.settings import get_settings
from src.shared.exceptions import RateLimitError, RobotsBlockedError, ScraperError
from src.shared.logging import get_logger

logger = get_logger(__name__)


@dataclass
class RawJobData:
    title: str
    company_name: str
    source_url: str
    board_name: str
    location: str | None = None
    description: str | None = None
    posted_date: date | None = None
    raw_data: dict | None = None


class BaseScraper(ABC):
    """Abstract base class for all job board scrapers."""

    board_name: str = ""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._robots_cache: dict[str, RobotFileParser] = {}

    def _get_http_client(self) -> httpx.Client:
        ua = random.choice(self.settings.scraping.user_agents)
        return httpx.Client(
            timeout=httpx.Timeout(30),
            headers={"User-Agent": ua},
            follow_redirects=True,
        )

    def _rate_limit_delay(self) -> None:
        delay = random.uniform(
            self.settings.scraping.request_delay_min_seconds,
            self.settings.scraping.request_delay_max_seconds,
        )
        time.sleep(delay)

    def _check_robots_txt(self, url: str) -> bool:
        """Returns True if URL is allowed by robots.txt."""
        if not self.settings.scraping.respect_robots_txt:
            return True

        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

        if robots_url not in self._robots_cache:
            rp = RobotFileParser()
            rp.set_url(robots_url)
            try:
                rp.read()
            except Exception:
                logger.warning("failed_to_read_robots_txt", url=robots_url)
                return True
            self._robots_cache[robots_url] = rp

        rp = self._robots_cache[robots_url]
        return rp.can_fetch("*", url)

    def _fetch(self, url: str, client: httpx.Client) -> httpx.Response:
        """Fetch a URL with rate limiting and robots.txt checking."""
        if not self._check_robots_txt(url):
            raise RobotsBlockedError(f"Blocked by robots.txt: {url}")

        return self._fetch_api(url, client)

    def _fetch_api(self, url: str, client: httpx.Client) -> httpx.Response:
        """Fetch a public API URL with rate limiting but NO robots.txt check.

        Use for known public API endpoints (Greenhouse, Lever, Ashby, etc.)
        where robots.txt may block bots but the API is intended for access.
        """
        self._rate_limit_delay()

        try:
            response = client.get(url)
            if response.status_code == 429:
                raise RateLimitError(f"Rate limited by {urlparse(url).netloc}")
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as e:
            raise ScraperError(f"HTTP {e.response.status_code} for {url}") from e
        except httpx.RequestError as e:
            raise ScraperError(f"Request failed for {url}: {e}") from e

    # Broad GTM-relevant keywords for filtering job titles from company boards.
    # The full search_queries ("VP Sales SaaS") are too specific for title matching.
    GTM_TITLE_KEYWORDS = [
        "sales", "marketing", "revenue", "gtm", "go-to-market", "go to market",
        "growth", "demand gen", "demand generation", "business development",
        "partnerships", "partner", "alliances", "customer success",
        "account executive", "account manager", "sdr", "bdr",
        "field sales", "enterprise sales", "commercial", "channel",
        "enablement", "sales engineer", "solutions engineer",
        "pre-sales", "presales", "customer acquisition",
        "head of sales", "vp sales", "vp marketing", "vp revenue",
        "director of sales", "director of marketing", "director of revenue",
        "cro", "cmo", "chief revenue", "chief marketing",
    ]

    def _is_gtm_title(self, title: str) -> bool:
        """Check if a job title is GTM-relevant using broad keyword matching."""
        title_lower = title.lower()
        return any(kw in title_lower for kw in self.GTM_TITLE_KEYWORDS)

    @abstractmethod
    def scrape(self, search_queries: list[str], company_slugs: list[str] | None = None) -> list[RawJobData]:
        """Scrape the board for jobs matching the search queries."""
        ...
