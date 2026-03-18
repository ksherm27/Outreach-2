from __future__ import annotations

from src.scraper.base import BaseScraper, RawJobData
from src.scraper.registry import register_scraper
from src.shared.logging import get_logger

logger = get_logger(__name__)


@register_scraper("workday")
class WorkdayScraper(BaseScraper):
    """Scrapes Workday career sites.

    Workday sites are at: https://{company}.wd5.myworkdayjobs.com/en-US/{site}
    These are heavily JS-rendered and require Playwright.
    """

    def scrape(self, search_queries: list[str], company_slugs: list[str] | None = None) -> list[RawJobData]:
        logger.info("workday_scraper_started", queries=search_queries)
        # Workday requires JS rendering via Playwright — disabled by default
        # company_slugs would need format "company:site:subdomain"
        return []

    def scrape_site(
        self, company: str, site: str, subdomain: str, title_keywords: list[str]
    ) -> list[RawJobData]:
        """Scrape a Workday career site using their internal API.

        Workday exposes a search API at:
        https://{company}.{subdomain}.myworkdayjobs.com/wday/cxs/{company}/{site}/jobs
        """
        api_url = f"https://{company}.{subdomain}.myworkdayjobs.com/wday/cxs/{company}/{site}/jobs"
        jobs: list[RawJobData] = []

        with self._get_http_client() as client:
            for query in title_keywords:
                payload = {
                    "appliedFacets": {},
                    "limit": 20,
                    "offset": 0,
                    "searchText": query,
                }
                try:
                    client.headers["Content-Type"] = "application/json"
                    response = client.post(api_url, json=payload)
                    response.raise_for_status()
                    data = response.json()
                except Exception:
                    logger.error("workday_fetch_failed", company=company, query=query)
                    continue

                for posting in data.get("jobPostings", []):
                    title = posting.get("title", "")
                    external_path = posting.get("externalPath", "")
                    if not external_path:
                        continue

                    job_url = f"https://{company}.{subdomain}.myworkdayjobs.com/en-US/{site}{external_path}"
                    location = posting.get("locationsText", "")

                    jobs.append(RawJobData(
                        title=title,
                        company_name=company,
                        source_url=job_url,
                        board_name=self.board_name,
                        location=location,
                        raw_data=posting,
                    ))

                self._rate_limit_delay()

        logger.info("workday_scraped", company=company, jobs_found=len(jobs))
        return jobs
