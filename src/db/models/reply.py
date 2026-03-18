from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.models.base import Base, TimestampMixin


class Reply(TimestampMixin, Base):
    __tablename__ = "replies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    outreach_message_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("outreach_messages.id")
    )
    contact_id: Mapped[int] = mapped_column(Integer, ForeignKey("contacts.id"), nullable=False)
    platform: Mapped[str] = mapped_column(String(20), nullable=False)
    platform_message_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    subject: Mapped[Optional[str]] = mapped_column(String(1000))
    body: Mapped[str] = mapped_column(Text, nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Classification
    reply_type: Mapped[Optional[str]] = mapped_column(String(30))
    classification_confidence: Mapped[Optional[float]] = mapped_column(Float)
    classification_reasoning: Mapped[Optional[str]] = mapped_column(Text)
    ooo_return_date: Mapped[Optional[date]] = mapped_column(Date)

    # Action tracking
    action_taken: Mapped[Optional[str]] = mapped_column(String(50))
    action_taken_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    assigned_recruiter: Mapped[Optional[str]] = mapped_column(String(255))

    outreach_message = relationship("OutreachMessage", back_populates="replies")
    contact = relationship("Contact", back_populates="replies")
