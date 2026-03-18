from __future__ import annotations

import re
from datetime import date, datetime, timedelta, timezone

from src.config.settings import get_settings
from src.db.models.company import Company
from src.db.models.job import ScrapedJob
from src.shared.logging import get_logger

logger = get_logger(__name__)


class ICPScorer:
    """Scores scraped jobs against the Ideal Customer Profile."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.icp = self.settings.icp
        self.weights = self.icp.scoring

    def score(self, job: ScrapedJob, company: Company | None = None) -> int:
        """Calculate ICP score (0-100) for a job + optional company data."""
        total = 0
        total += self._title_score(job.title)
        total += self._funding_score(job.description or "", company)
        total += self._saas_score(job.description or "", company)
        total += self._employee_score(company)
        total += self._recency_score(job.posted_date)
        total += self._location_score(job.location or "")
        total += self._exclusion_penalties(job.description or "", job.company_name)
        return max(0, min(100, total))

    def _title_score(self, title: str) -> int:
        """Score based on title match against ICP target roles."""
        title_lower = title.lower().strip()

        # Exact match
        for _category, role_config in self.icp.target_roles.items():
            for target_title in role_config.titles:
                if target_title.lower() == title_lower:
                    return self.weights.title_exact_match

        # Fuzzy match (title contains a target title or vice versa)
        for _category, role_config in self.icp.target_roles.items():
            for target_title in role_config.titles:
                if (
                    target_title.lower() in title_lower
                    or title_lower in target_title.lower()
                ):
                    return self.weights.title_fuzzy_match

        return 0

    def _funding_score(self, description: str, company: Company | None) -> int:
        """Score based on funding stage signals."""
        # Crunchbase-confirmed funding stage
        if company and company.funding_stage:
            if company.funding_stage in self.icp.target_funding_stages:
                return self.weights.funding_crunchbase_confirmed

        # Keyword in job description
        desc_lower = description.lower()
        for signal in self.icp.funding_signals:
            if signal.lower() in desc_lower:
                return self.weights.funding_keyword_in_jd

        return 0

    def _saas_score(self, description: str, company: Company | None) -> int:
        """Score based on SaaS signal detection."""
        if company and company.is_saas:
            return self.weights.saas_keyword_confirmed

        desc_lower = description.lower()
        for signal in self.icp.saas_signals:
            if signal.lower() in desc_lower:
                return self.weights.saas_keyword_confirmed

        return 0

    def _employee_score(self, company: Company | None) -> int:
        """Score based on employee count range."""
        if not company or not company.employee_count:
            return 0

        count = company.employee_count
        if 25 <= count <= 500:
            return self.weights.employee_count_25_to_500
        elif 500 < count <= 1000:
            return self.weights.employee_count_500_to_1000

        return 0

    def _recency_score(self, posted_date: date | None) -> int:
        """Score based on job posting recency."""
        if not posted_date:
            return 0

        today = datetime.now(timezone.utc).date()
        days_old = (today - posted_date).days

        if days_old <= 2:
            return self.weights.posted_within_48h
        elif days_old <= 3:
            return self.weights.posted_48h_to_72h

        return 0

    def _location_score(self, location: str) -> int:
        """Score based on target location match."""
        if not location:
            return 0

        location_lower = location.lower()
        for target_loc in self.icp.target_locations:
            if target_loc.lower() in location_lower:
                return self.weights.target_location

        return 0

    def _exclusion_penalties(self, description: str, company_name: str) -> int:
        """Apply negative scores for exclusion signals."""
        penalty = 0
        text = f"{company_name} {description}".lower()

        staffing_keywords = ["staffing agency", "recruiting firm", "talent agency"]
        if any(kw in text for kw in staffing_keywords):
            penalty += self.weights.staffing_agency_detected

        public_keywords = ["NYSE:", "NASDAQ:", "publicly traded", "publicly listed"]
        if any(kw.lower() in text for kw in public_keywords):
            penalty += self.weights.public_company_detected

        return penalty
