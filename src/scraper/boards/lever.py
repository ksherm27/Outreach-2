from __future__ import annotations

from datetime import datetime

from src.scraper.base import BaseScraper, RawJobData
from src.scraper.registry import register_scraper
from src.shared.logging import get_logger

logger = get_logger(__name__)


@register_scraper("lever")
class LeverScraper(BaseScraper):
    """Scrapes Lever job boards via their public JSON API.

    Lever boards expose jobs at:
    https://api.lever.co/v0/postings/{company}
    """

    API_URL = "https://api.lever.co/v0/postings/{company}"

    def scrape(self, search_queries: list[str], company_slugs: list[str] | None = None) -> list[RawJobData]:
        jobs: list[RawJobData] = []
        logger.info("lever_scraper_started", queries=search_queries, slugs=company_slugs)

        if not company_slugs:
            from src.scraper.registry import get_board_config
            cfg = get_board_config("lever")
            company_slugs = cfg.company_slugs if cfg else []

        for slug in company_slugs:
            try:
                found = self.scrape_company(slug, search_queries)
                jobs.extend(found)
            except Exception:
                logger.error("lever_slug_failed", slug=slug)

        logger.info("lever_scraper_done", total_jobs=len(jobs))
        return jobs

    def scrape_company(self, company_slug: str, title_keywords: list[str]) -> list[RawJobData]:
        url = self.API_URL.format(company=company_slug)
        jobs: list[RawJobData] = []

        with self._get_http_client() as client:
            try:
                response = self._fetch_api(url, client)
                postings = response.json()
            except Exception:
                logger.error("lever_fetch_failed", company=company_slug)
                return jobs

            if not isinstance(postings, list):
                return jobs

            for posting in postings:
                title = posting.get("text", "")

                location = ""
                categories = posting.get("categories", {})
                if categories:
                    location = categories.get("location", "")

                if not self._should_include_job(title, company_slug, location):
                    continue

                posted_date = None
                created_at = posting.get("createdAt")
                if created_at:
                    try:
                        posted_date = datetime.fromtimestamp(created_at / 1000).date()
                    except (ValueError, TypeError, OSError):
                        pass

                hosted_url = posting.get("hostedUrl", "")
                if not hosted_url:
                    continue

                description_parts = []
                for list_item in posting.get("lists", []):
                    description_parts.append(list_item.get("text", ""))
                    description_parts.append(list_item.get("content", ""))
                description = posting.get("descriptionPlain", "") or "\n".join(description_parts)

                jobs.append(RawJobData(
                    title=title,
                    company_name=company_slug,
                    source_url=hosted_url,
                    board_name=self.board_name,
                    location=location,
                    description=description,
                    posted_date=posted_date,
                    raw_data=posting,
                ))

        logger.info("lever_company_scraped", company=company_slug, jobs_found=len(jobs))
        return jobs
