from __future__ import annotations

from src.scraper.base import BaseScraper, RawJobData
from src.scraper.registry import register_scraper
from src.shared.logging import get_logger

logger = get_logger(__name__)


@register_scraper("smartrecruiters")
class SmartRecruitersScraper(BaseScraper):
    """Scrapes SmartRecruiters job boards.

    Public API: https://api.smartrecruiters.com/v1/companies/{company}/postings
    """

    API_URL = "https://api.smartrecruiters.com/v1/companies/{company}/postings"

    def scrape(self, search_queries: list[str]) -> list[RawJobData]:
        logger.info("smartrecruiters_scraper_started", queries=search_queries)
        return []

    def scrape_company(self, company_id: str, title_keywords: list[str]) -> list[RawJobData]:
        jobs: list[RawJobData] = []
        offset = 0
        limit = 100

        with self._get_http_client() as client:
            while True:
                url = f"{self.API_URL.format(company=company_id)}?offset={offset}&limit={limit}"
                try:
                    response = self._fetch(url, client)
                    data = response.json()
                except Exception:
                    logger.error("smartrecruiters_fetch_failed", company=company_id)
                    break

                content = data.get("content", [])
                if not content:
                    break

                for posting in content:
                    title = posting.get("name", "")
                    if not any(kw.lower() in title.lower() for kw in title_keywords):
                        continue

                    location_data = posting.get("location", {})
                    location = location_data.get("city", "")
                    if location_data.get("country"):
                        location = f"{location}, {location_data['country']}"

                    ref_url = posting.get("ref", "")

                    jobs.append(RawJobData(
                        title=title,
                        company_name=posting.get("company", {}).get("name", company_id),
                        source_url=ref_url,
                        board_name=self.board_name,
                        location=location,
                        raw_data=posting,
                    ))

                if len(content) < limit:
                    break
                offset += limit

        logger.info("smartrecruiters_scraped", company=company_id, jobs_found=len(jobs))
        return jobs
