from __future__ import annotations

from bs4 import BeautifulSoup

from src.scraper.base import BaseScraper, RawJobData
from src.scraper.registry import register_scraper
from src.shared.logging import get_logger

logger = get_logger(__name__)


@register_scraper("jazzhr")
class JazzHRScraper(BaseScraper):
    """Scrapes JazzHR job boards.

    JazzHR boards are at: https://{company}.applytojob.com/apply
    """

    BASE_URL = "https://{company}.applytojob.com/apply"

    def scrape(self, search_queries: list[str]) -> list[RawJobData]:
        logger.info("jazzhr_scraper_started", queries=search_queries)
        return []

    def scrape_company(self, company_slug: str, title_keywords: list[str]) -> list[RawJobData]:
        url = self.BASE_URL.format(company=company_slug)
        jobs: list[RawJobData] = []

        with self._get_http_client() as client:
            try:
                response = self._fetch(url, client)
            except Exception:
                logger.error("jazzhr_fetch_failed", company=company_slug)
                return jobs

            soup = BeautifulSoup(response.text, "lxml")
            job_links = soup.select("a.job-title, .job-listing a, .position-title a")

            for link in job_links:
                title = link.get_text(strip=True)
                if not any(kw.lower() in title.lower() for kw in title_keywords):
                    continue

                href = link.get("href", "")
                if not href:
                    continue
                if not href.startswith("http"):
                    href = f"https://{company_slug}.applytojob.com{href}"

                jobs.append(RawJobData(
                    title=title,
                    company_name=company_slug,
                    source_url=href,
                    board_name=self.board_name,
                ))

        logger.info("jazzhr_scraped", company=company_slug, jobs_found=len(jobs))
        return jobs
