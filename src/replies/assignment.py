from datetime import datetime, timezone

from sqlalchemy import select

from src.config.settings import get_settings
from src.db.models.contact import Contact
from src.db.models.system import RecruiterAssignment
from src.db.session import get_session
from src.shared.logging import get_logger

logger = get_logger(__name__)


class RecruiterAssigner:
    """Handles round-robin recruiter assignment for replies."""

    def __init__(self) -> None:
        self.settings = get_settings()

    def assign(self, contact_id: int) -> str:
        """Assign a recruiter to a contact. Returns the Slack user ID."""
        # Check if contact already has an assigned recruiter
        with get_session() as session:
            contact = session.get(Contact, contact_id)
            if contact and contact.assigned_recruiter:
                return contact.assigned_recruiter

        # Round-robin assignment
        recruiter_id = self._next_recruiter()

        # Save assignment
        with get_session() as session:
            contact = session.get(Contact, contact_id)
            if contact:
                contact.assigned_recruiter = recruiter_id

        logger.info("recruiter_assigned", contact_id=contact_id, recruiter=recruiter_id)
        return recruiter_id

    def _next_recruiter(self) -> str:
        """Pick the next recruiter in round-robin order."""
        slack_ids = self.settings.routing.recruiter_slack_ids
        if not slack_ids:
            return ""

        with get_session() as session:
            # Ensure all recruiters exist in the assignments table
            for slack_id in slack_ids:
                existing = session.execute(
                    select(RecruiterAssignment).where(
                        RecruiterAssignment.recruiter_slack_id == slack_id
                    )
                ).scalar_one_or_none()

                if not existing:
                    assignment = RecruiterAssignment(
                        recruiter_name=slack_id,
                        recruiter_slack_id=slack_id,
                        is_active=True,
                        assignment_count=0,
                    )
                    session.add(assignment)

        # Find the recruiter with the fewest assignments (or earliest last_assigned_at)
        with get_session() as session:
            stmt = (
                select(RecruiterAssignment)
                .where(RecruiterAssignment.is_active.is_(True))
                .where(
                    RecruiterAssignment.recruiter_slack_id.in_(slack_ids)
                )
                .order_by(
                    RecruiterAssignment.assignment_count.asc(),
                    RecruiterAssignment.last_assigned_at.asc().nulls_first(),
                )
                .limit(1)
            )
            next_recruiter = session.execute(stmt).scalar_one_or_none()

            if next_recruiter:
                next_recruiter.assignment_count += 1
                next_recruiter.last_assigned_at = datetime.now(timezone.utc)
                return next_recruiter.recruiter_slack_id

        # Fallback to first in list
        return slack_ids[0]
