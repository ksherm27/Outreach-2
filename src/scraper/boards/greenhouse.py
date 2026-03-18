from __future__ import annotations

from datetime import datetime, date

from src.scraper.base import BaseScraper, RawJobData
from src.scraper.registry import register_scraper
from src.shared.logging import get_logger

logger = get_logger(__name__)


@register_scraper("greenhouse")
class GreenhouseScraper(BaseScraper):
    """Scrapes Greenhouse job boards via their public JSON API.

    Greenhouse boards expose jobs at:
    https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs
    """

    SEARCH_URL = "https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs"

    def scrape(self, search_queries: list[str]) -> list[RawJobData]:
        jobs: list[RawJobData] = []
        # Greenhouse doesn't support keyword search on their API directly.
        # We fetch all jobs from known board tokens and filter by title keywords.
        # In production, board tokens would be discovered or configured.
        # For now, this demonstrates the pattern.
        logger.info("greenhouse_scraper_started", queries=search_queries)
        return jobs

    def scrape_board_token(self, board_token: str, title_keywords: list[str]) -> list[RawJobData]:
        """Scrape a specific Greenhouse board by its token."""
        url = self.SEARCH_URL.format(board_token=board_token)
        jobs: list[RawJobData] = []

        with self._get_http_client() as client:
            try:
                response = self._fetch(url, client)
                data = response.json()
            except Exception:
                logger.error("greenhouse_fetch_failed", board_token=board_token)
                return jobs

            for job_data in data.get("jobs", []):
                title = job_data.get("title", "")
                if not self._matches_keywords(title, title_keywords):
                    continue

                location = ""
                if job_data.get("location"):
                    location = job_data["location"].get("name", "")

                posted_date = None
                if job_data.get("updated_at"):
                    try:
                        posted_date = datetime.fromisoformat(
                            job_data["updated_at"].replace("Z", "+00:00")
                        ).date()
                    except (ValueError, TypeError):
                        pass

                job_url = job_data.get("absolute_url", "")
                if not job_url:
                    continue

                jobs.append(RawJobData(
                    title=title,
                    company_name=board_token,
                    source_url=job_url,
                    board_name=self.board_name,
                    location=location,
                    description=self._extract_description(job_data),
                    posted_date=posted_date,
                    raw_data=job_data,
                ))

        logger.info("greenhouse_board_scraped", board_token=board_token, jobs_found=len(jobs))
        return jobs

    def _matches_keywords(self, title: str, keywords: list[str]) -> bool:
        title_lower = title.lower()
        return any(kw.lower() in title_lower for kw in keywords)

    def _extract_description(self, job_data: dict) -> str:
        content = job_data.get("content", "")
        # Greenhouse returns HTML content; strip basic tags
        from bs4 import BeautifulSoup
        if content:
            soup = BeautifulSoup(content, "lxml")
            return soup.get_text(separator="\n", strip=True)
        return ""
