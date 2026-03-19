from __future__ import annotations

from src.scraper.base import BaseScraper, RawJobData
from src.scraper.registry import register_scraper
from src.shared.logging import get_logger

logger = get_logger(__name__)


@register_scraper("indeed")
class IndeedScraper(BaseScraper):
    """Scrapes Indeed job listings.

    Indeed has aggressive bot detection. This scraper uses their
    public search with careful rate limiting and UA rotation.
    """

    SEARCH_URL = "https://www.indeed.com/jobs"

    def scrape(self, search_queries: list[str], company_slugs: list[str] | None = None) -> list[RawJobData]:
        logger.info("indeed_scraper_started", queries=search_queries)
        jobs: list[RawJobData] = []

        with self._get_http_client() as client:
            for query in search_queries:
                params = f"?q={query}&fromage=3&sort=date"
                try:
                    response = self._fetch(f"{self.SEARCH_URL}{params}", client)
                except Exception:
                    logger.error("indeed_fetch_failed", query=query)
                    continue

                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, "lxml")

                for card in soup.select(".job_seen_beacon, .jobsearch-ResultsList > li"):
                    title_el = card.select_one("h2.jobTitle a, .jobTitle span")
                    company_el = card.select_one("[data-testid='company-name'], .companyName")
                    location_el = card.select_one("[data-testid='text-location'], .companyLocation")

                    if not title_el:
                        continue

                    title = title_el.get_text(strip=True)
                    company = company_el.get_text(strip=True) if company_el else ""
                    location = location_el.get_text(strip=True) if location_el else ""

                    # Extract job key for URL
                    link = card.select_one("a[data-jk], h2 a")
                    if link:
                        jk = link.get("data-jk", "")
                        href = link.get("href", "")
                        if jk:
                            job_url = f"https://www.indeed.com/viewjob?jk={jk}"
                        elif href:
                            job_url = f"https://www.indeed.com{href}" if href.startswith("/") else href
                        else:
                            continue
                    else:
                        continue

                    if self._is_excluded_industry(title, company):
                        continue
                    if self._is_early_career(title):
                        continue
                    if not self._is_north_america(location):
                        continue

                    jobs.append(RawJobData(
                        title=title,
                        company_name=company,
                        source_url=job_url,
                        board_name=self.board_name,
                        location=location,
                    ))

        logger.info("indeed_scraped", jobs_found=len(jobs))
        return jobs
