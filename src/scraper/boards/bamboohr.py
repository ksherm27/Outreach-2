from __future__ import annotations

from src.scraper.base import BaseScraper, RawJobData
from src.scraper.registry import register_scraper
from src.shared.logging import get_logger

logger = get_logger(__name__)


@register_scraper("bamboohr")
class BambooHRScraper(BaseScraper):
    """Scrapes BambooHR job boards.

    BambooHR boards expose jobs at:
    https://{company}.bamboohr.com/careers/list
    """

    API_URL = "https://{company}.bamboohr.com/careers/list"

    def scrape(self, search_queries: list[str]) -> list[RawJobData]:
        logger.info("bamboohr_scraper_started", queries=search_queries)
        return []

    def scrape_company(self, company_slug: str, title_keywords: list[str]) -> list[RawJobData]:
        url = self.API_URL.format(company=company_slug)
        jobs: list[RawJobData] = []

        with self._get_http_client() as client:
            try:
                response = self._fetch(url, client)
                data = response.json()
            except Exception:
                logger.error("bamboohr_fetch_failed", company=company_slug)
                return jobs

            for result in data.get("result", []):
                title = result.get("jobOpeningName", "")
                if not any(kw.lower() in title.lower() for kw in title_keywords):
                    continue

                location = result.get("location", {}).get("city", "")
                job_id = result.get("id", "")
                job_url = f"https://{company_slug}.bamboohr.com/careers/{job_id}"

                jobs.append(RawJobData(
                    title=title,
                    company_name=company_slug,
                    source_url=job_url,
                    board_name=self.board_name,
                    location=location,
                    raw_data=result,
                ))

        logger.info("bamboohr_scraped", company=company_slug, jobs_found=len(jobs))
        return jobs
