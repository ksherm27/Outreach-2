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

    def scrape(self, search_queries: list[str], company_slugs: list[str] | None = None) -> list[RawJobData]:
        jobs: list[RawJobData] = []
        logger.info("bamboohr_scraper_started", queries=search_queries, slugs=company_slugs)

        if not company_slugs:
            from src.scraper.registry import get_board_config
            cfg = get_board_config("bamboohr")
            company_slugs = cfg.company_slugs if cfg else []

        for slug in company_slugs:
            try:
                found = self.scrape_company(slug, search_queries)
                jobs.extend(found)
            except Exception:
                logger.error("bamboohr_slug_failed", slug=slug)

        logger.info("bamboohr_scraper_done", total_jobs=len(jobs))
        return jobs

    def scrape_company(self, company_slug: str, title_keywords: list[str]) -> list[RawJobData]:
        url = self.API_URL.format(company=company_slug)
        jobs: list[RawJobData] = []

        with self._get_http_client() as client:
            try:
                response = self._fetch_api(url, client)
                data = response.json()
            except Exception:
                logger.error("bamboohr_fetch_failed", company=company_slug)
                return jobs

            for result in data.get("result", []):
                title = result.get("jobOpeningName", "")
                if not self._is_gtm_title(title):
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
