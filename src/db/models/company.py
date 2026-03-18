from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.models.base import Base, TimestampMixin


class Company(TimestampMixin, Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    domain: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True)
    crunchbase_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True)
    funding_stage: Mapped[Optional[str]] = mapped_column(String(50))
    total_raised: Mapped[Optional[int]] = mapped_column(BigInteger)
    employee_count: Mapped[Optional[int]] = mapped_column(Integer)
    founded_year: Mapped[Optional[int]] = mapped_column(SmallInteger)
    hq_location: Mapped[Optional[str]] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_saas: Mapped[Optional[bool]] = mapped_column(Boolean)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    industry: Mapped[Optional[str]] = mapped_column(String(255))
    enriched_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    jobs = relationship("ScrapedJob", back_populates="company")
    contacts = relationship("Contact", back_populates="company")
