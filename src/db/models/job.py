from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Integer, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.models.base import Base, TimestampMixin


class ScrapedJob(TimestampMixin, Base):
    __tablename__ = "scraped_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_url: Mapped[str] = mapped_column(String(2048), nullable=False, index=True)
    board_name: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    company_name: Mapped[str] = mapped_column(String(500), nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String(500))
    description: Mapped[Optional[str]] = mapped_column(Text)
    posted_date: Mapped[Optional[date]] = mapped_column(Date)
    raw_data: Mapped[Optional[dict]] = mapped_column(JSONB)

    # Scoring
    icp_score: Mapped[Optional[int]] = mapped_column(SmallInteger)
    gtm_category: Mapped[Optional[str]] = mapped_column(String(50))
    is_qualified: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_excluded: Mapped[bool] = mapped_column(Boolean, default=False)
    exclusion_reason: Mapped[Optional[str]] = mapped_column(String(255))

    # Relations
    scrape_run_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("scrape_runs.id"))
    company_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("companies.id"))

    company = relationship("Company", back_populates="jobs")
    scrape_run = relationship("ScrapeRun", back_populates="jobs")
    outreach_messages = relationship("OutreachMessage", back_populates="job")

    __table_args__ = (
        Index("ix_scraped_jobs_dedup", "source_url", "created_at"),
        Index("ix_scraped_jobs_qualified", "is_qualified", "created_at"),
    )
