from __future__ import annotations

from src.config.settings import get_settings
from src.db.models.company import Company
from src.db.models.job import ScrapedJob


class ExclusionFilter:
    """Filters out jobs that match exclusion criteria."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.exclude_signals = [s.lower() for s in self.settings.icp.exclude_signals]

    def should_exclude(
        self, job: ScrapedJob, company: Company | None = None
    ) -> tuple[bool, str | None]:
        """Returns (should_exclude, reason) tuple."""
        text = f"{job.company_name} {job.title} {job.description or ''}".lower()

        for signal in self.exclude_signals:
            if signal in text:
                return True, f"Matched exclusion signal: {signal}"

        if company:
            if company.is_public:
                return True, "Public company"

            if company.employee_count:
                if company.employee_count < self.settings.icp.min_employees:
                    return True, f"Too few employees: {company.employee_count}"
                if company.employee_count > self.settings.icp.max_employees:
                    return True, f"Too many employees: {company.employee_count}"

        return False, None
