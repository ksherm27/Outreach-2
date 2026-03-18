from src.db.models.company import Company
from src.db.models.contact import Contact
from src.db.models.job import ScrapedJob


def build_instantly_variables(
    contact: Contact, company: Company, job: ScrapedJob
) -> dict:
    """Build merge variables for Instantly campaigns."""
    return {
        "first_name": contact.first_name or "",
        "company": company.name,
        "funding_stage": company.funding_stage or "",
        "role_title": contact.title or job.title,
        "gtm_role_category": job.gtm_category or "",
        "source_job_url": job.source_url,
        "icp_score": str(job.icp_score or 0),
    }


def build_lemlist_variables(
    contact: Contact, company: Company, job: ScrapedJob
) -> dict:
    """Build merge variables for Lemlist campaigns."""
    return {
        "firstName": contact.first_name or "",
        "company": company.name,
        "jobTitle": contact.title or job.title,
        "fundingStage": company.funding_stage or "",
        "gtmCategory": job.gtm_category or "",
    }
