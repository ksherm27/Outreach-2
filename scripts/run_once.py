#!/usr/bin/env python3
"""Manual one-shot pipeline run for testing.

Usage:
    python scripts/run_once.py scrape          # Run scraper for all enabled boards
    python scripts/run_once.py score           # Score all unscored jobs
    python scripts/run_once.py enrich <job_id> # Enrich a specific job
    python scripts/run_once.py poll            # Poll replies once
    python scripts/run_once.py full            # Full pipeline: scrape -> score
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.settings import get_settings
from src.shared.logging import setup_logging


def run_scrape():
    """Run scraper synchronously (no Celery)."""
    from src.scraper.registry import get_enabled_boards, get_scraper
    from src.scraper.dedup import bulk_dedup
    from src.db.models.job import ScrapedJob
    from src.db.models.system import ScrapeRun
    from src.db.session import get_session
    from datetime import datetime, timezone

    settings = get_settings()
    boards = get_enabled_boards()
    print(f"Scraping {len(boards)} enabled boards...")

    for board_name in boards:
        board_cfg = settings.scraping.boards.get(board_name)
        slugs = board_cfg.company_slugs if board_cfg else []
        print(f"\n  Scraping {board_name} ({len(slugs)} company slugs)...")
        try:
            scraper = get_scraper(board_name)
            jobs = scraper.scrape(settings.scraping.search_queries, company_slugs=slugs)
            print(f"    Found {len(jobs)} raw jobs")

            if jobs:
                urls = [j.source_url for j in jobs]
                new_urls = bulk_dedup(urls, settings.scraping.dedup_window_days)
                new_jobs = [j for j in jobs if j.source_url in new_urls]
                print(f"    New (non-duplicate): {len(new_jobs)}")

                with get_session() as session:
                    run = ScrapeRun(
                        board_name=board_name,
                        status="completed",
                        jobs_found=len(jobs),
                        jobs_new=len(new_jobs),
                        jobs_duplicate=len(jobs) - len(new_jobs),
                        started_at=datetime.now(timezone.utc),
                        completed_at=datetime.now(timezone.utc),
                    )
                    session.add(run)
                    session.flush()

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
                            scrape_run_id=run.id,
                        )
                        session.add(job)

                    print(f"    Saved {len(new_jobs)} new jobs to DB")

        except Exception as e:
            print(f"    ERROR: {e}")


def run_score():
    """Score all unscored jobs synchronously."""
    from sqlalchemy import select, func
    from src.db.models.job import ScrapedJob
    from src.db.session import get_session
    from src.scoring.icp import ICPScorer
    from src.scoring.filters import ExclusionFilter
    from src.scoring.categories import categorize_role

    settings = get_settings()
    scorer = ICPScorer()
    exclusion_filter = ExclusionFilter()

    with get_session() as session:
        jobs = list(
            session.execute(
                select(ScrapedJob)
                .where(ScrapedJob.icp_score.is_(None))
                .where(ScrapedJob.is_excluded.is_(False))
                .limit(500)
            ).scalars().all()
        )

    print(f"Scoring {len(jobs)} unscored jobs...")
    qualified = 0

    with get_session() as session:
        for job in jobs:
            job = session.get(ScrapedJob, job.id)
            if not job:
                continue

            is_excluded, reason = exclusion_filter.should_exclude(job)
            if is_excluded:
                job.is_excluded = True
                job.exclusion_reason = reason
                continue

            score = scorer.score(job)
            category = categorize_role(job.title)
            job.icp_score = score
            job.gtm_category = category.value if category else None
            job.is_qualified = score >= settings.icp.score_threshold and category is not None

            if job.is_qualified:
                qualified += 1

    print(f"Scored {len(jobs)} jobs, {qualified} qualified (>= {settings.icp.score_threshold})")


def run_poll():
    """Poll replies once."""
    from src.replies.poller import ReplyPoller

    poller = ReplyPoller()
    replies = poller.poll_all()
    print(f"Polled {len(replies)} replies")
    for r in replies[:10]:
        print(f"  {r.platform} | {r.email} | {r.subject[:50]}...")


def main():
    setup_logging()

    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]

    if command == "scrape":
        run_scrape()
    elif command == "score":
        run_score()
    elif command == "poll":
        run_poll()
    elif command == "full":
        run_scrape()
        run_score()
    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
