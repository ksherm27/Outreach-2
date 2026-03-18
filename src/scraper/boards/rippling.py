from __future__ import annotations

from src.scraper.base import BaseScraper, RawJobData
from src.scraper.registry import register_scraper
from src.shared.logging import get_logger

logger = get_logger(__name__)


@register_scraper("rippling")
class RipplingScraper(BaseScraper):
    """Scrapes Rippling ATS job boards.

    Rippling career pages are at:
    https://{company}.rippling-ats.com/careers
    """

    BASE_URL = "https://{company}.rippling-ats.com"
    JOBS_URL = "https://{company}.rippling-ats.com/careers"

    def scrape(self, search_queries: list[str]) -> list[RawJobData]:
        logger.info("rippling_scraper_started", queries=search_queries)
        # Rippling may require JS rendering; placeholder for implementation
        return []
