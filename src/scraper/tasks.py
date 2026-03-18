from __future__ import annotations

import time
from datetime import datetime, timezone

from src.celery_app import celery_app
from src.config.settings import get_settings
from src.db.models.job import ScrapedJob
from src.db.models.system import ScrapeRun
from src.db.session import get_session
from src.scraper.dedup import bulk_dedup
from src.scraper.registry import get_enabled_boards, get_scraper
from src.shared.logging import get_logger

logger = get_logger(__name__)


@celery_app.task(name="src.scraper.tasks.scrape_all_boards")
def scrape_all_boards() -> dict:
    """Orchestrator: dispatches scrape tasks for each enabled board."""
    settings = get_settings()
    boards = get_enabled_boards()
    stagger = settings.scraping.board_stagger_minutes * 60  # convert to seconds

    logger.info("scrape_all_boards_started", boards=boards)

    for i, board_name in enumerate(boards):
        countdown = i * stagger
        scrape_board.apply_async(args=[board_name], countdown=countdown)
        logger.info("scrape_board_scheduled", board=board_name, countdown_seconds=countdown)

    return {"boards_dispatched": len(boards)}


@celery_app.task(
    name="src.scraper.tasks.scrape_board",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def scrape_board(self, board_name: str) -> dict:
    """Scrape a single board and save results to DB."""
    settings = get_settings()
    started_at = datetime.now(timezone.utc)

    # Create scrape run record
    with get_session() as session:
        run = ScrapeRun(
            board_name=board_name,
            status="running",
            started_at=started_at,
        )
        session.add(run)
        session.flush()
        run_id = run.id

    try:
        scraper = get_scraper(board_name)
        board_cfg = settings.scraping.boards.get(board_name)
        slugs = board_cfg.company_slugs if board_cfg else []
        raw_jobs = scraper.scrape(settings.scraping.search_queries, company_slugs=slugs)

        # Dedup
        all_urls = [j.source_url for j in raw_jobs]
        new_urls = bulk_dedup(all_urls, settings.scraping.dedup_window_days)
        new_jobs = [j for j in raw_jobs if j.source_url in new_urls]

        # Save to DB
        saved_count = 0
        with get_session() as session:
            for job_data in new_jobs:
                job = ScrapedJob(
                    source_url=job_data.source_url,
                    board_name=job_data.board_name,
                    title=job_data.title,
                    company_name=job_data.company_name,
                    location=job_data.location,
                    description=job_data.description,
                    posted_date=job_data.posted_date,
                    raw_data=job_data.raw_data,
                    scrape_run_id=run_id,
                )
                session.add(job)
                saved_count += 1

        # Update run record
        with get_session() as session:
            run = session.get(ScrapeRun, run_id)
            if run:
                run.status = "completed"
                run.jobs_found = len(raw_jobs)
                run.jobs_new = saved_count
                run.jobs_duplicate = len(raw_jobs) - saved_count
                run.completed_at = datetime.now(timezone.utc)

        logger.info(
            "scrape_board_completed",
            board=board_name,
            jobs_found=len(raw_jobs),
            jobs_new=saved_count,
            jobs_duplicate=len(raw_jobs) - saved_count,
        )

        # Send Slack notification
        _notify_scrape_complete(board_name, len(raw_jobs), saved_count, run_id)

        return {
            "board": board_name,
            "jobs_found": len(raw_jobs),
            "jobs_new": saved_count,
        }

    except Exception as exc:
        # Update run as failed
        with get_session() as session:
            run = session.get(ScrapeRun, run_id)
            if run:
                run.status = "failed"
                run.error_message = str(exc)
                run.completed_at = datetime.now(timezone.utc)

        logger.error("scrape_board_failed", board=board_name, error=str(exc))
        raise self.retry(exc=exc)


def _notify_scrape_complete(
    board_name: str, jobs_found: int, jobs_new: int, run_id: int
) -> None:
    """Send Slack notification for scrape completion."""
    try:
        from src.notifications.slack import get_slack_notifier
        settings = get_settings()
        if settings.slack_alerts.notify_on_scrape_complete:
            notifier = get_slack_notifier()
            notifier.send_webhook(
                "scrape_board_complete",
                board_name=board_name,
                jobs_found=jobs_found,
                jobs_new=jobs_new,
                run_id=run_id,
            )
    except Exception:
        logger.warning("slack_notification_failed", board=board_name)
