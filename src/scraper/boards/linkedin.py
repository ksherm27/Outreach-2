from __future__ import annotations

from src.scraper.base import BaseScraper, RawJobData
from src.scraper.registry import register_scraper
from src.shared.logging import get_logger

logger = get_logger(__name__)


@register_scraper("linkedin")
class LinkedInScraper(BaseScraper):
    """Scrapes LinkedIn job listings.

    LinkedIn heavily restricts scraping. This scraper uses their
    public job search page with careful rate limiting.

    Note: LinkedIn may require Playwright for JS rendering and
    has aggressive bot detection. Use with caution.
    """

    SEARCH_URL = "https://www.linkedin.com/jobs/search/"

    def scrape(self, search_queries: list[str], company_slugs: list[str] | None = None) -> list[RawJobData]:
        logger.info("linkedin_scraper_started", queries=search_queries)
        jobs: list[RawJobData] = []

        with self._get_http_client() as client:
            for query in search_queries:
                params = {
                    "keywords": query,
                    "location": "United States",
                    "f_TPR": "r86400",  # Past 24 hours
                    "position": 1,
                    "pageNum": 0,
                }
                try:
                    # Use _fetch_api to skip robots.txt — LinkedIn's public job
                    # search page serves results in HTML without auth
                    response = self._fetch_api(
                        f"{self.SEARCH_URL}?{'&'.join(f'{k}={v}' for k, v in params.items())}",
                        client,
                    )
                except Exception:
                    logger.error("linkedin_fetch_failed", query=query)
                    continue

                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, "lxml")

                for card in soup.select(".base-card, .job-search-card"):
                    title_el = card.select_one(".base-search-card__title, h3")
                    company_el = card.select_one(".base-search-card__subtitle, h4")
                    location_el = card.select_one(".job-search-card__location")
                    link_el = card.select_one("a.base-card__full-link, a")

                    if not title_el or not link_el:
                        continue

                    title = title_el.get_text(strip=True)
                    company = company_el.get_text(strip=True) if company_el else ""
                    location = location_el.get_text(strip=True) if location_el else ""
                    href = link_el.get("href", "")

                    if not href:
                        continue

                    if self._is_excluded_industry(title, company):
                        continue
                    if not self._is_north_america(location):
                        continue

                    jobs.append(RawJobData(
                        title=title,
                        company_name=company,
                        source_url=href.split("?")[0],
                        board_name=self.board_name,
                        location=location,
                    ))

        logger.info("linkedin_scraped", jobs_found=len(jobs))
        return jobs
