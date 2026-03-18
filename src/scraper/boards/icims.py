from __future__ import annotations

from bs4 import BeautifulSoup

from src.scraper.base import BaseScraper, RawJobData
from src.scraper.registry import register_scraper
from src.shared.logging import get_logger

logger = get_logger(__name__)


@register_scraper("icims")
class ICIMSScraper(BaseScraper):
    """Scrapes iCIMS job boards.

    iCIMS career portals are at:
    https://careers-{company}.icims.com/jobs/search
    """

    SEARCH_URL = "https://careers-{company}.icims.com/jobs/search"

    def scrape(self, search_queries: list[str], company_slugs: list[str] | None = None) -> list[RawJobData]:
        jobs: list[RawJobData] = []
        logger.info("icims_scraper_started", queries=search_queries, slugs=company_slugs)

        if not company_slugs:
            from src.scraper.registry import get_board_config
            cfg = get_board_config("icims")
            company_slugs = cfg.company_slugs if cfg else []

        for slug in company_slugs:
            try:
                found = self.scrape_company(slug, search_queries)
                jobs.extend(found)
            except Exception:
                logger.error("icims_slug_failed", slug=slug)

        logger.info("icims_scraper_done", total_jobs=len(jobs))
        return jobs

    def scrape_company(self, company_slug: str, title_keywords: list[str]) -> list[RawJobData]:
        jobs: list[RawJobData] = []

        with self._get_http_client() as client:
            for query in title_keywords:
                url = f"{self.SEARCH_URL.format(company=company_slug)}?ss=1&searchKeyword={query}"
                try:
                    response = self._fetch(url, client)
                except Exception:
                    logger.error("icims_fetch_failed", company=company_slug, query=query)
                    continue

                soup = BeautifulSoup(response.text, "lxml")
                listings = soup.select(".iCIMS_JobsTable .row, .col-xs-12.title a")

                for listing in listings:
                    link = listing if listing.name == "a" else listing.select_one("a.iCIMS_Anchor")
                    if not link:
                        continue

                    title = link.get_text(strip=True)
                    href = link.get("href", "")
                    if not href or not title:
                        continue

                    jobs.append(RawJobData(
                        title=title,
                        company_name=company_slug,
                        source_url=href,
                        board_name=self.board_name,
                    ))

        logger.info("icims_scraped", company=company_slug, jobs_found=len(jobs))
        return jobs
