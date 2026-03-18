from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from src.db.models.job import ScrapedJob
from src.db.session import get_session


def is_duplicate(source_url: str, window_days: int = 30) -> bool:
    """Check if a job URL was already scraped within the dedup window."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)
    with get_session() as session:
        stmt = (
            select(ScrapedJob.id)
            .where(ScrapedJob.source_url == source_url)
            .where(ScrapedJob.created_at >= cutoff)
            .limit(1)
        )
        result = session.execute(stmt).scalar_one_or_none()
        return result is not None


def bulk_dedup(source_urls: list[str], window_days: int = 30) -> set[str]:
    """Return the set of URLs that are NOT duplicates (i.e., new URLs)."""
    if not source_urls:
        return set()

    cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)
    with get_session() as session:
        stmt = (
            select(ScrapedJob.source_url)
            .where(ScrapedJob.source_url.in_(source_urls))
            .where(ScrapedJob.created_at >= cutoff)
        )
        existing = {row[0] for row in session.execute(stmt).all()}

    return set(source_urls) - existing
