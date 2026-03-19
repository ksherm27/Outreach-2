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

    # Industries to exclude — hospitality, food service, etc.
    EXCLUDED_INDUSTRY_KEYWORDS = [
        # Food & Beverage / Hospitality
        "food", "restaurant", "hospitality", "hotel", "beverage", "catering",
        "kitchen", "chef", "menu", "dining", "brewery", "winery", "bakery",
        "grocery", "fast food", "food service", "foodservice",
        # Other non-tech industries
        "insurance", "construction", "manufacturing", "real estate", "mortgage",
        "automotive", "trucking", "logistics", "staffing agency", "recruiting agency",
        "oil and gas", "oil & gas", "mining", "agriculture", "farming",
        "janitorial", "cleaning service", "pest control", "lawn care",
        "plumbing", "hvac", "roofing", "flooring",
        # Education / Government / Nonprofit
        "school district", "public school", "university of", "college of",
        "county of", "city of", "state of", "government", "federal",
        "nonprofit", "non-profit", "church", "ministry",
    ]

    # Locations considered North America / US (for filtering)
    US_LOCATION_KEYWORDS = [
        "united states", "usa", "us", "u.s.", "remote",
        "new york", "san francisco", "los angeles", "chicago", "boston",
        "seattle", "austin", "denver", "atlanta", "miami", "dallas",
        "houston", "phoenix", "philadelphia", "washington", "portland",
        "san diego", "san jose", "nashville", "charlotte", "minneapolis",
        "salt lake", "raleigh", "tampa", "detroit", "pittsburgh",
        "columbus", "indianapolis", "kansas city", "st. louis", "st louis",
        "baltimore", "milwaukee", "sacramento", "san antonio",
        "california", "new jersey", "texas", "florida", "illinois",
        "massachusetts", "washington", "colorado", "georgia", "virginia",
        "north carolina", "pennsylvania", "ohio", "michigan", "arizona",
        "oregon", "maryland", "tennessee", "minnesota", "wisconsin",
        "utah", "connecticut", "indiana", "missouri",
        "ny", "ca", "tx", "fl", "il", "ma", "wa", "co", "ga", "va", "nc", "pa",
        # Canada
        "canada", "toronto", "vancouver", "montreal", "calgary", "ottawa",
        # General
        "americas", "amer", "north america",
    ]

    def _is_gtm_title(self, title: str) -> bool:
        """Check if a job title is GTM-relevant using broad keyword matching."""
        title_lower = title.lower()
        return any(kw in title_lower for kw in self.GTM_TITLE_KEYWORDS)

    # Early-career / junior title indicators to exclude
    EARLY_CAREER_KEYWORDS = [
        "intern", "internship", "co-op", "coop",
        "junior", "jr.", "jr ",
        "entry level", "entry-level",
        "associate",  # e.g. "Associate Account Executive"
        "early career", "early-career",
        "new grad", "new graduate", "recent graduate",
        "coordinator",  # typically junior-level
        "assistant",
    ]

    def _is_early_career(self, title: str) -> bool:
        """Check if a job title indicates an early-career / junior role."""
        title_lower = title.lower()
        return any(kw in title_lower for kw in self.EARLY_CAREER_KEYWORDS)

    def _is_excluded_industry(self, title: str, company_name: str) -> bool:
        """Check if a job/company belongs to an excluded industry."""
        combined = f"{title} {company_name}".lower()
        return any(kw in combined for kw in self.EXCLUDED_INDUSTRY_KEYWORDS)

    def _is_north_america(self, location: str) -> bool:
        """Check if a location is in North America (US/Canada).

        Returns True if:
        - Location matches a US/Canada keyword
        - Location is empty/unspecified (benefit of the doubt)
        """
        if not location or not location.strip():
            return True  # No location specified — include it

        loc_lower = location.lower().strip()

        # Exclude obvious non-US locations
        non_us_indicators = [
            "united kingdom", "uk", "london", "germany", "berlin", "munich",
            "france", "paris", "japan", "tokyo", "india", "bangalore", "mumbai",
            "hyderabad", "bengaluru", "china", "beijing", "shanghai", "shenzhen",
            "australia", "sydney", "melbourne", "singapore", "hong kong",
            "brazil", "são paulo", "sao paulo", "mexico city",
            "ireland", "dublin", "netherlands", "amsterdam", "spain", "madrid",
            "italy", "milan", "rome", "sweden", "stockholm", "norway", "oslo",
            "denmark", "copenhagen", "finland", "helsinki", "poland", "warsaw",
            "czech", "prague", "austria", "vienna", "switzerland", "zurich",
            "israel", "tel aviv", "south korea", "seoul", "taiwan", "taipei",
            "indonesia", "jakarta", "philippines", "manila", "vietnam",
            "thailand", "bangkok", "malaysia", "kuala lumpur",
            "south africa", "cape town", "johannesburg", "nigeria", "lagos",
            "egypt", "cairo", "kenya", "nairobi", "uae", "dubai", "abu dhabi",
            "saudi", "riyadh", "qatar", "doha", "argentina", "buenos aires",
            "colombia", "bogota", "chile", "santiago", "peru", "lima",
            "new zealand", "auckland", "emea", "apac", "latam",
        ]

        # If it explicitly mentions a non-US region, exclude
        if any(non_us in loc_lower for non_us in non_us_indicators):
            return False

        # If it matches a US/Canada keyword, include
        if any(us in loc_lower for us in self.US_LOCATION_KEYWORDS):
            return True

        # If we can't determine — include (will be filtered by ICP scoring later)
        return True

    def _should_include_job(self, title: str, company_name: str, location: str | None) -> bool:
        """Combined filter: GTM title + not early career + not excluded industry + North America."""
        if not self._is_gtm_title(title):
            return False
        if self._is_early_career(title):
            return False
        if self._is_excluded_industry(title, company_name):
            return False
        if not self._is_north_america(location or ""):
            return False
        return True

    @abstractmethod
    def scrape(self, search_queries: list[str], company_slugs: list[str] | None = None) -> list[RawJobData]:
        """Scrape the board for jobs matching the search queries."""
        ...
