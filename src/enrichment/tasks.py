from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import urlparse

from sqlalchemy import select

from src.celery_app import celery_app
from src.config.constants import ContactSource
from src.config.settings import get_settings
from src.db.models.company import Company
from src.db.models.contact import Contact
from src.db.models.job import ScrapedJob
from src.db.session import get_session
from src.enrichment.cache import cache_cleanup
from src.enrichment.crunchbase import CrunchbaseClient
from src.enrichment.hunter import HunterClient
from src.enrichment.rocketreach import RocketReachClient
from src.enrichment.team_scraper import TeamPageScraper
from src.shared.logging import get_logger

logger = get_logger(__name__)


@celery_app.task(
    name="src.enrichment.tasks.enrich_company",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
)
def enrich_company(self, job_id: int) -> dict:
    """Enrich company data for a qualified job using Crunchbase."""
    settings = get_settings()

    with get_session() as session:
        job = session.get(ScrapedJob, job_id)
        if not job:
            return {"status": "job_not_found"}

        # Try to extract domain from company name or job URL
        domain = _extract_domain(job.source_url, job.company_name)
        if not domain:
            logger.warning("no_domain_found", job_id=job_id, company=job.company_name)
            return {"status": "no_domain"}

        # Check if company already exists
        existing_company = session.execute(
            select(Company).where(Company.domain == domain)
        ).scalar_one_or_none()

        if existing_company and existing_company.enriched_at:
            # Already enriched, just link the job
            job.company_id = existing_company.id
            discover_contacts.delay(existing_company.id, job_id)
            return {"status": "already_enriched", "company_id": existing_company.id}

    # Fetch from Crunchbase
    try:
        cb_client = CrunchbaseClient()
        company_data = cb_client.get_company(domain)
    except Exception as exc:
        logger.error("crunchbase_enrichment_failed", domain=domain, error=str(exc))
        raise self.retry(exc=exc)

    with get_session() as session:
        job = session.get(ScrapedJob, job_id)
        if not job:
            return {"status": "job_not_found"}

        # Create or update company
        company = session.execute(
            select(Company).where(Company.domain == domain)
        ).scalar_one_or_none()

        if not company:
            company = Company(name=job.company_name, domain=domain)
            session.add(company)
            session.flush()

        if company_data:
            company.name = company_data.name or company.name
            company.crunchbase_id = company_data.crunchbase_id
            company.funding_stage = company_data.funding_stage
            company.total_raised = company_data.total_raised
            company.employee_count = company_data.employee_count
            company.founded_year = company_data.founded_year
            company.hq_location = company_data.hq_location
            company.description = company_data.description
            company.is_public = company_data.is_public
            company.industry = company_data.industry

            # Detect SaaS from description
            if company_data.description:
                saas_signals = settings.icp.saas_signals
                desc_lower = company_data.description.lower()
                company.is_saas = any(s.lower() in desc_lower for s in saas_signals)

        company.enriched_at = datetime.now(timezone.utc)
        job.company_id = company.id
        company_id = company.id

    # Dispatch contact discovery
    discover_contacts.delay(company_id, job_id)

    logger.info("company_enriched", company_id=company_id, domain=domain)
    return {"status": "enriched", "company_id": company_id}


@celery_app.task(
    name="src.enrichment.tasks.discover_contacts",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
)
def discover_contacts(self, company_id: int, job_id: int) -> dict:
    """Discover contacts for a company using Hunter.io, RocketReach, and team page scraping."""
    settings = get_settings()

    with get_session() as session:
        company = session.get(Company, company_id)
        if not company or not company.domain:
            return {"status": "no_company_or_domain"}

        domain = company.domain
        company_name = company.name

        # Get the job's GTM category for RocketReach title search
        job = session.get(ScrapedJob, job_id)
        gtm_category = job.gtm_category if job else None

    contacts_found = 0

    # Hunter.io domain search
    try:
        hunter = HunterClient()
        email_results = hunter.domain_search(domain, limit=10)

        with get_session() as session:
            for result in email_results:
                if result.confidence < settings.enrichment.min_contact_confidence_score:
                    continue

                existing = session.execute(
                    select(Contact).where(
                        Contact.email == result.email,
                        Contact.company_id == company_id,
                    )
                ).scalar_one_or_none()

                if not existing:
                    contact = Contact(
                        company_id=company_id,
                        first_name=result.first_name,
                        last_name=result.last_name,
                        email=result.email,
                        email_confidence=result.confidence,
                        title=result.position,
                        linkedin_url=result.linkedin_url,
                        source=ContactSource.HUNTER,
                    )
                    session.add(contact)
                    contacts_found += 1

    except Exception:
        logger.warning("hunter_search_failed", domain=domain)

    # RocketReach person search
    if settings.enrichment.rocketreach_enabled:
        try:
            title_keywords = _gtm_category_to_titles(gtm_category)
            rr_client = RocketReachClient()
            rr_results = rr_client.person_search(
                company_name=company_name,
                title_keywords=title_keywords,
                max_results=settings.enrichment.rocketreach_max_results,
            )

            with get_session() as session:
                for person in rr_results:
                    if not person.email:
                        continue
                    if person.email_confidence < settings.enrichment.min_contact_confidence_score:
                        continue

                    existing = session.execute(
                        select(Contact).where(
                            Contact.email == person.email,
                            Contact.company_id == company_id,
                        )
                    ).scalar_one_or_none()

                    if not existing:
                        contact = Contact(
                            company_id=company_id,
                            first_name=person.first_name,
                            last_name=person.last_name,
                            email=person.email,
                            email_confidence=person.email_confidence,
                            title=person.title,
                            linkedin_url=person.linkedin_url,
                            source=ContactSource.ROCKETREACH,
                        )
                        session.add(contact)
                        contacts_found += 1

            logger.info(
                "rocketreach_search_completed",
                company=company_name,
                results=len(rr_results),
            )

        except Exception:
            logger.warning("rocketreach_search_failed", company=company_name)

    # Team page scraping
    if settings.enrichment.team_page_scrape_enabled:
        try:
            team_scraper = TeamPageScraper()
            candidates = team_scraper.scrape(domain)

            with get_session() as session:
                for candidate in candidates:
                    if candidate.confidence < settings.enrichment.min_contact_confidence_score:
                        continue
                    if not candidate.email:
                        continue

                    existing = session.execute(
                        select(Contact).where(
                            Contact.email == candidate.email,
                            Contact.company_id == company_id,
                        )
                    ).scalar_one_or_none()

                    if not existing:
                        name_parts = candidate.name.split(maxsplit=1)
                        contact = Contact(
                            company_id=company_id,
                            first_name=name_parts[0] if name_parts else None,
                            last_name=name_parts[1] if len(name_parts) > 1 else None,
                            email=candidate.email,
                            email_confidence=candidate.confidence,
                            title=candidate.title,
                            linkedin_url=candidate.linkedin_url,
                            source=ContactSource.TEAM_PAGE,
                        )
                        session.add(contact)
                        contacts_found += 1

        except Exception:
            logger.warning("team_page_scrape_failed", domain=domain)

    # Dispatch outreach for discovered contacts
    if contacts_found > 0:
        with get_session() as session:
            contacts = list(
                session.execute(
                    select(Contact)
                    .where(Contact.company_id == company_id)
                    .where(Contact.is_suppressed.is_(False))
                ).scalars().all()
            )
            for contact in contacts:
                from src.outreach.tasks import push_to_campaigns
                push_to_campaigns.delay(contact.id, job_id)

    logger.info(
        "contacts_discovered",
        company_id=company_id,
        contacts_found=contacts_found,
    )
    return {"status": "done", "contacts_found": contacts_found}


@celery_app.task(name="src.enrichment.tasks.cleanup_cache")
def cleanup_cache_task() -> dict:
    """Remove expired enrichment cache entries."""
    removed = cache_cleanup()
    logger.info("enrichment_cache_cleaned", entries_removed=removed)
    return {"removed": removed}


_GTM_TITLE_MAP: dict[str, list[str]] = {
    "Sales Leadership": ["VP Sales", "Head of Sales", "Director of Sales", "CRO"],
    "Marketing Leadership": ["VP Marketing", "Head of Marketing", "CMO", "Director of Marketing"],
    "Customer Success Leadership": ["VP Customer Success", "Head of CS", "Director of Customer Success"],
    "GTM Strategy": ["Head of GTM", "VP GTM", "VP Growth", "Director of GTM"],
    "SDR BDR Leadership": ["SDR Manager", "BDR Manager", "Director of Sales Development"],
}


def _gtm_category_to_titles(gtm_category: str | None) -> list[str] | None:
    """Convert a GTM category to title keywords for RocketReach search."""
    if not gtm_category:
        return None
    return _GTM_TITLE_MAP.get(gtm_category)


def _extract_domain(source_url: str, company_name: str) -> str | None:
    """Extract a company domain from the job URL or company name."""
    parsed = urlparse(source_url)
    hostname = parsed.hostname or ""

    # For ATS-hosted boards, try to extract company domain
    ats_hosts = [
        "boards.greenhouse.io",
        "jobs.lever.co",
        "jobs.ashbyhq.com",
        "apply.workable.com",
        "www.linkedin.com",
        "www.indeed.com",
    ]

    if hostname in ats_hosts:
        # Try to get domain from path segments
        path_parts = [p for p in parsed.path.split("/") if p]
        if path_parts:
            slug = path_parts[0]
            # This is a company slug, not a domain — would need further resolution
            return None

    # Direct company career page
    if hostname and hostname not in ats_hosts:
        # Remove www. prefix
        domain = hostname.removeprefix("www.")
        return domain

    return None
