from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import delete, select

from src.db.models.system import EnrichmentCache
from src.db.session import get_session


def cache_get(key: str) -> dict[str, Any] | None:
    """Get cached data by key. Returns None if not found or expired."""
    with get_session() as session:
        stmt = (
            select(EnrichmentCache)
            .where(EnrichmentCache.cache_key == key)
            .where(EnrichmentCache.expires_at > datetime.now(timezone.utc))
        )
        entry = session.execute(stmt).scalar_one_or_none()
        if entry:
            return entry.data_json
    return None


def cache_set(key: str, data: dict[str, Any], ttl_days: int = 7) -> None:
    """Store data in cache with a TTL."""
    now = datetime.now(timezone.utc)
    expires = now + timedelta(days=ttl_days)

    with get_session() as session:
        # Upsert
        stmt = select(EnrichmentCache).where(EnrichmentCache.cache_key == key)
        existing = session.execute(stmt).scalar_one_or_none()

        if existing:
            existing.data_json = data
            existing.created_at = now
            existing.expires_at = expires
        else:
            entry = EnrichmentCache(
                cache_key=key,
                data_json=data,
                created_at=now,
                expires_at=expires,
            )
            session.add(entry)


def cache_cleanup() -> int:
    """Remove expired cache entries. Returns count of entries removed."""
    with get_session() as session:
        stmt = delete(EnrichmentCache).where(
            EnrichmentCache.expires_at <= datetime.now(timezone.utc)
        )
        result = session.execute(stmt)
        return result.rowcount
