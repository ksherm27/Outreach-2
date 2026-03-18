from __future__ import annotations

from typing import Optional

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.models.base import Base, TimestampMixin


class Contact(TimestampMixin, Base):
    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"), nullable=False)
    first_name: Mapped[Optional[str]] = mapped_column(String(255))
    last_name: Mapped[Optional[str]] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    email_confidence: Mapped[Optional[float]] = mapped_column(Float)
    title: Mapped[Optional[str]] = mapped_column(String(500))
    linkedin_url: Mapped[Optional[str]] = mapped_column(String(2048))
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    hubspot_contact_id: Mapped[Optional[str]] = mapped_column(String(255))
    is_suppressed: Mapped[bool] = mapped_column(Boolean, default=False)
    assigned_recruiter: Mapped[Optional[str]] = mapped_column(String(255))

    company = relationship("Company", back_populates="contacts")
    outreach_messages = relationship("OutreachMessage", back_populates="contact")
    replies = relationship("Reply", back_populates="contact")

    __table_args__ = (
        UniqueConstraint("email", "company_id", name="uq_contact_email_company"),
    )
