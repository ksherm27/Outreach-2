from __future__ import annotations

from src.scraper.base import BaseScraper, RawJobData
from src.scraper.registry import register_scraper
from src.shared.logging import get_logger

logger = get_logger(__name__)


@register_scraper("workable")
class WorkableScraper(BaseScraper):
    """Scrapes Workable job boards.

    Workable boards are at: https://apply.workable.com/api/v1/widget/accounts/{company}
    """

    API_URL = "https://apply.workable.com/api/v1/widget/accounts/{company}"

    def scrape(self, search_queries: list[str], company_slugs: list[str] | None = None) -> list[RawJobData]:
        jobs: list[RawJobData] = []
        logger.info("workable_scraper_started", queries=search_queries, slugs=company_slugs)

        if not company_slugs:
            from src.scraper.registry import get_board_config
            cfg = get_board_config("workable")
            company_slugs = cfg.company_slugs if cfg else []

        for slug in company_slugs:
            try:
                found = self.scrape_company(slug, search_queries)
                jobs.extend(found)
            except Exception:
                logger.error("workable_slug_failed", slug=slug)

        logger.info("workable_scraper_done", total_jobs=len(jobs))
        return jobs

    def scrape_company(self, company_slug: str, title_keywords: list[str]) -> list[RawJobData]:
        url = self.API_URL.format(company=company_slug)
        jobs: list[RawJobData] = []

        with self._get_http_client() as client:
            try:
                response = self._fetch_api(url, client)
                data = response.json()
            except Exception:
                logger.error("workable_fetch_failed", company=company_slug)
                return jobs

            for job_data in data.get("jobs", []):
                title = job_data.get("title", "")
                if not self._is_gtm_title(title):
                    continue

                job_url = job_data.get("url", "")
                if not job_url:
                    job_url = f"https://apply.workable.com/{company_slug}/j/{job_data.get('shortcode', '')}/"

                jobs.append(RawJobData(
                    title=title,
                    company_name=company_slug,
                    source_url=job_url,
                    board_name=self.board_name,
                    location=job_data.get("location", {}).get("city", ""),
                    description=job_data.get("description", ""),
                    raw_data=job_data,
                ))

        logger.info("workable_company_scraped", company=company_slug, jobs_found=len(jobs))
        return jobs
