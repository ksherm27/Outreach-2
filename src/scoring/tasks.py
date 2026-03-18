from __future__ import annotations

from sqlalchemy import select

from src.celery_app import celery_app
from src.config.settings import get_settings
from src.db.models.job import ScrapedJob
from src.db.session import get_session
from src.scoring.categories import categorize_role
from src.scoring.filters import ExclusionFilter
from src.scoring.icp import ICPScorer
from src.shared.logging import get_logger

logger = get_logger(__name__)


@celery_app.task(name="src.scoring.tasks.score_unscored_jobs")
def score_unscored_jobs() -> dict:
    """Score all jobs that haven't been scored yet."""
    with get_session() as session:
        stmt = (
            select(ScrapedJob)
            .where(ScrapedJob.icp_score.is_(None))
            .where(ScrapedJob.is_excluded.is_(False))
            .limit(500)
        )
        jobs = list(session.execute(stmt).scalars().all())

    if not jobs:
        return {"scored": 0, "qualified": 0}

    job_ids = [j.id for j in jobs]
    return score_jobs_batch(job_ids)


@celery_app.task(name="src.scoring.tasks.score_jobs_batch")
def score_jobs_batch(job_ids: list[int]) -> dict:
    """Score a batch of jobs by their IDs."""
    settings = get_settings()
    scorer = ICPScorer()
    exclusion_filter = ExclusionFilter()

    scored = 0
    qualified = 0

    with get_session() as session:
        for job_id in job_ids:
            job = session.get(ScrapedJob, job_id)
            if not job:
                continue

            # Check exclusions first
            company = job.company if job.company_id else None
            is_excluded, reason = exclusion_filter.should_exclude(job, company)

            if is_excluded:
                job.is_excluded = True
                job.exclusion_reason = reason
                job.is_qualified = False
                scored += 1
                continue

            # Score the job
            score = scorer.score(job, company)
            category = categorize_role(job.title)

            job.icp_score = score
            job.gtm_category = category.value if category else None
            job.is_qualified = score >= settings.icp.score_threshold and category is not None
            scored += 1

            if job.is_qualified:
                qualified += 1
                # Dispatch enrichment for qualified jobs
                from src.enrichment.tasks import enrich_company
                enrich_company.delay(job.id)

    logger.info(
        "scoring_batch_complete",
        total=len(job_ids),
        scored=scored,
        qualified=qualified,
    )

    return {"scored": scored, "qualified": qualified}
