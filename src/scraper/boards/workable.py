from __future__ import annotations

from src.scraper.base import BaseScraper, RawJobData
from src.scraper.registry import register_scraper
from src.shared.logging import get_logger

logger = get_logger(__name__)


@register_scraper("workable")
class WorkableScraper(BaseScraper):
    """Scrapes Workable job boards via their v3 API.

    Workable v3 API: POST https://apply.workable.com/api/v3/accounts/{company}/jobs
    The v1 widget API is deprecated and returns empty results.
    """

    API_URL = "https://apply.workable.com/api/v3/accounts/{company}/jobs"

    def scrape(self, search_queries: list[str], company_slugs: list[str] | None = None) -> list[RawJobData]:
        jobs: list[RawJobData] = []
        logger.info("workable_scraper_started", queries=search_queries, slugs=company_slugs)

        if not company_slugs:
            from src.scraper.registry import get_board_config
            cfg = get_board_config("workable")
            company_slugs = cfg.company_slugs if cfg else []

        for slug in company_slugs:
            try:
                found = self.scrape_company(slug)
                jobs.extend(found)
            except Exception:
                logger.error("workable_slug_failed", slug=slug)

        logger.info("workable_scraper_done", total_jobs=len(jobs))
        return jobs

    def scrape_company(self, company_slug: str) -> list[RawJobData]:
        url = self.API_URL.format(company=company_slug)
        jobs: list[RawJobData] = []

        with self._get_http_client() as client:
            try:
                self._rate_limit_delay()
                response = client.post(
                    url,
                    json={"query": "", "location": [], "department": [], "worktype": []},
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()
                data = response.json()
            except Exception:
                logger.error("workable_fetch_failed", company=company_slug)
                return jobs

            for job_data in data.get("results", []):
                title = job_data.get("title", "")
                if not self._is_gtm_title(title):
                    continue

                shortcode = job_data.get("shortcode", "")
                job_url = f"https://apply.workable.com/{company_slug}/j/{shortcode}/"

                location_parts = []
                if job_data.get("city"):
                    location_parts.append(job_data["city"])
                if job_data.get("country"):
                    location_parts.append(job_data["country"])
                location = ", ".join(location_parts)

                jobs.append(RawJobData(
                    title=title,
                    company_name=company_slug,
                    source_url=job_url,
                    board_name=self.board_name,
                    location=location,
                    raw_data=job_data,
                ))

            # Handle pagination
            next_token = data.get("nextPage")
            while next_token:
                try:
                    self._rate_limit_delay()
                    response = client.post(
                        url,
                        json={"query": "", "location": [], "department": [], "worktype": [], "token": next_token},
                        headers={"Content-Type": "application/json"},
                    )
                    response.raise_for_status()
                    data = response.json()
                except Exception:
                    break

                for job_data in data.get("results", []):
                    title = job_data.get("title", "")
                    if not self._is_gtm_title(title):
                        continue

                    shortcode = job_data.get("shortcode", "")
                    job_url = f"https://apply.workable.com/{company_slug}/j/{shortcode}/"

                    location_parts = []
                    if job_data.get("city"):
                        location_parts.append(job_data["city"])
                    if job_data.get("country"):
                        location_parts.append(job_data["country"])
                    location = ", ".join(location_parts)

                    jobs.append(RawJobData(
                        title=title,
                        company_name=company_slug,
                        source_url=job_url,
                        board_name=self.board_name,
                        location=location,
                        raw_data=job_data,
                    ))

                next_token = data.get("nextPage")

        logger.info("workable_company_scraped", company=company_slug, jobs_found=len(jobs))
        return jobs
