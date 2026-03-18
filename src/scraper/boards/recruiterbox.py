from __future__ import annotations

from src.scraper.base import BaseScraper, RawJobData
from src.scraper.registry import register_scraper
from src.shared.logging import get_logger

logger = get_logger(__name__)


@register_scraper("recruiterbox")
class RecruiterboxScraper(BaseScraper):
    """Scrapes Recruiterbox (now Trakstar Hire) job boards.

    Career pages at: https://{company}.recruiterbox.com/jobs
    """

    API_URL = "https://{company}.recruiterbox.com/api/v1/openings"

    def scrape(self, search_queries: list[str], company_slugs: list[str] | None = None) -> list[RawJobData]:
        jobs: list[RawJobData] = []
        logger.info("recruiterbox_scraper_started", queries=search_queries, slugs=company_slugs)

        if not company_slugs:
            from src.scraper.registry import get_board_config
            cfg = get_board_config("recruiterbox")
            company_slugs = cfg.company_slugs if cfg else []

        for slug in company_slugs:
            try:
                found = self.scrape_company(slug, search_queries)
                jobs.extend(found)
            except Exception:
                logger.error("recruiterbox_slug_failed", slug=slug)

        logger.info("recruiterbox_scraper_done", total_jobs=len(jobs))
        return jobs

    def scrape_company(self, company_slug: str, title_keywords: list[str]) -> list[RawJobData]:
        url = self.API_URL.format(company=company_slug)
        jobs: list[RawJobData] = []

        with self._get_http_client() as client:
            try:
                response = self._fetch_api(url, client)
                data = response.json()
            except Exception:
                logger.error("recruiterbox_fetch_failed", company=company_slug)
                return jobs

            openings = data if isinstance(data, list) else data.get("objects", [])
            for opening in openings:
                title = opening.get("title", "")
                if not any(kw.lower() in title.lower() for kw in title_keywords):
                    continue

                location = opening.get("location", {})
                if isinstance(location, dict):
                    location = location.get("city", "")

                job_url = opening.get("hosted_url", "")
                if not job_url:
                    continue

                jobs.append(RawJobData(
                    title=title,
                    company_name=company_slug,
                    source_url=job_url,
                    board_name=self.board_name,
                    location=location if isinstance(location, str) else "",
                    description=opening.get("description", ""),
                    raw_data=opening,
                ))

        logger.info("recruiterbox_scraped", company=company_slug, jobs_found=len(jobs))
        return jobs
