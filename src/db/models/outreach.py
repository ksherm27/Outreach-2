from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.models.base import Base, TimestampMixin


class OutreachMessage(TimestampMixin, Base):
    __tablename__ = "outreach_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    contact_id: Mapped[int] = mapped_column(Integer, ForeignKey("contacts.id"), nullable=False)
    job_id: Mapped[int] = mapped_column(Integer, ForeignKey("scraped_jobs.id"), nullable=False)
    platform: Mapped[str] = mapped_column(String(20), nullable=False)
    campaign_id: Mapped[str] = mapped_column(String(255), nullable=False)
    platform_lead_id: Mapped[Optional[str]] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    variables: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    launched_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    paused_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    call_reminder_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    hubspot_deal_id: Mapped[Optional[str]] = mapped_column(String(255))

    contact = relationship("Contact", back_populates="outreach_messages")
    job = relationship("ScrapedJob", back_populates="outreach_messages")
    replies = relationship("Reply", back_populates="outreach_message")
