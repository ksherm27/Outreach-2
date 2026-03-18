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

    def scrape(self, search_queries: list[str], company_slugs: list[str] | None = None) -> list[RawJobData]:
        jobs: list[RawJobData] = []
        logger.info("ashby_scraper_started", queries=search_queries, slugs=company_slugs)

        if not company_slugs:
            from src.scraper.registry import get_board_config
            cfg = get_board_config("ashby")
            company_slugs = cfg.company_slugs if cfg else []

        for slug in company_slugs:
            try:
                found = self.scrape_board(slug, search_queries)
                jobs.extend(found)
            except Exception:
                logger.error("ashby_slug_failed", slug=slug)

        logger.info("ashby_scraper_done", total_jobs=len(jobs))
        return jobs

    def scrape_board(self, board_slug: str, title_keywords: list[str]) -> list[RawJobData]:
        url = self.API_URL.format(board_slug=board_slug)
        jobs: list[RawJobData] = []

        with self._get_http_client() as client:
            try:
                response = self._fetch_api(url, client)
                data = response.json()
            except Exception:
                logger.error("ashby_fetch_failed", board_slug=board_slug)
                return jobs

            for job_data in data.get("jobs", []):
                title = job_data.get("title", "")
                if not self._is_gtm_title(title):
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
