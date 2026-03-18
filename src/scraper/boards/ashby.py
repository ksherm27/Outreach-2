from __future__ import annotations

from src.scraper.base import BaseScraper, RawJobData
from src.scraper.registry import register_scraper
from src.shared.logging import get_logger

logger = get_logger(__name__)


@register_scraper("ashby")
class AshbyScraper(BaseScraper):
    """Scrapes Ashby job boards via their public API.

    Ashby exposes jobs at:
    https://api.ashbyhq.com/posting-api/job-board/{board_slug}
    """

    API_URL = "https://api.ashbyhq.com/posting-api/job-board/{board_slug}"

    def scrape(self, search_queries: list[str]) -> list[RawJobData]:
        logger.info("ashby_scraper_started", queries=search_queries)
        return []

    def scrape_board(self, board_slug: str, title_keywords: list[str]) -> list[RawJobData]:
        url = self.API_URL.format(board_slug=board_slug)
        jobs: list[RawJobData] = []

        with self._get_http_client() as client:
            try:
                response = self._fetch(url, client)
                data = response.json()
            except Exception:
                logger.error("ashby_fetch_failed", board_slug=board_slug)
                return jobs

            for job_data in data.get("jobs", []):
                title = job_data.get("title", "")
                if not any(kw.lower() in title.lower() for kw in title_keywords):
                    continue

                location = job_data.get("location", "")
                job_url = job_data.get("jobUrl", "")
                if not job_url:
                    continue

                jobs.append(RawJobData(
                    title=title,
                    company_name=job_data.get("departmentName", board_slug),
                    source_url=job_url,
                    board_name=self.board_name,
                    location=location,
                    description=job_data.get("descriptionPlain", ""),
                    raw_data=job_data,
                ))

        logger.info("ashby_board_scraped", board_slug=board_slug, jobs_found=len(jobs))
        return jobs
