from __future__ import annotations

from bs4 import BeautifulSoup

from src.scraper.base import BaseScraper, RawJobData
from src.scraper.registry import register_scraper
from src.shared.logging import get_logger

logger = get_logger(__name__)


@register_scraper("jobvite")
class JobviteScraper(BaseScraper):
    """Scrapes Jobvite job boards.

    Jobvite boards are at: https://jobs.jobvite.com/{company}/search
    """

    BASE_URL = "https://jobs.jobvite.com/{company}/search"

    def scrape(self, search_queries: list[str], company_slugs: list[str] | None = None) -> list[RawJobData]:
        jobs: list[RawJobData] = []
        logger.info("jobvite_scraper_started", queries=search_queries, slugs=company_slugs)

        if not company_slugs:
            from src.scraper.registry import get_board_config
            cfg = get_board_config("jobvite")
            company_slugs = cfg.company_slugs if cfg else []

        for slug in company_slugs:
            try:
                found = self.scrape_company(slug, search_queries)
                jobs.extend(found)
            except Exception:
                logger.error("jobvite_slug_failed", slug=slug)

        logger.info("jobvite_scraper_done", total_jobs=len(jobs))
        return jobs

    def scrape_company(self, company_slug: str, title_keywords: list[str]) -> list[RawJobData]:
        jobs: list[RawJobData] = []

        with self._get_http_client() as client:
            for query in title_keywords:
                url = f"{self.BASE_URL.format(company=company_slug)}?q={query}"
                try:
                    response = self._fetch(url, client)
                except Exception:
                    logger.error("jobvite_fetch_failed", company=company_slug, query=query)
                    continue

                soup = BeautifulSoup(response.text, "lxml")
                listings = soup.select(".jv-job-list tr, .job-listing, .jv-page-body a")

                for listing in listings:
                    title_el = listing.select_one("a") if listing.name == "tr" else listing
                    if not title_el:
                        continue

                    title = title_el.get_text(strip=True)
                    href = title_el.get("href", "")
                    if not href or not title:
                        continue

                    if not href.startswith("http"):
                        href = f"https://jobs.jobvite.com{href}"

                    jobs.append(RawJobData(
                        title=title,
                        company_name=company_slug,
                        source_url=href,
                        board_name=self.board_name,
                    ))

        logger.info("jobvite_scraped", company=company_slug, jobs_found=len(jobs))
        return jobs
