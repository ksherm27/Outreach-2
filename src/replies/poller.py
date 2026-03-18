from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select

from src.db.models.contact import Contact
from src.db.models.outreach import OutreachMessage
from src.db.models.reply import Reply
from src.db.session import get_session
from src.outreach.instantly import InstantlyClient
from src.outreach.lemlist import LemlistClient
from src.shared.logging import get_logger

logger = get_logger(__name__)


@dataclass
class RawReply:
    platform: str  # "instantly" or "lemlist"
    platform_message_id: str
    email: str
    subject: str
    body: str
    received_at: datetime
    campaign_id: str | None = None


class ReplyPoller:
    """Polls Instantly and Lemlist inboxes for new replies."""

    def poll_all(self) -> list[RawReply]:
        """Poll all platforms and return deduplicated raw replies."""
        replies: list[RawReply] = []

        instantly_replies = self._poll_instantly()
        replies.extend(instantly_replies)

        lemlist_replies = self._poll_lemlist()
        replies.extend(lemlist_replies)

        # Deduplicate by platform_message_id
        seen: set[str] = set()
        unique: list[RawReply] = []
        for r in replies:
            if r.platform_message_id not in seen:
                seen.add(r.platform_message_id)
                unique.append(r)

        logger.info(
            "replies_polled",
            instantly=len(instantly_replies),
            lemlist=len(lemlist_replies),
            unique=len(unique),
        )
        return unique

    def _poll_instantly(self) -> list[RawReply]:
        """Poll Instantly for new replies."""
        replies: list[RawReply] = []
        try:
            client = InstantlyClient()
            campaigns = client.list_campaigns()

            for campaign in campaigns:
                campaign_id = campaign.get("id", "")
                if not campaign_id:
                    continue

                try:
                    raw_replies = client.get_campaign_replies(campaign_id)
                    for r in raw_replies:
                        msg_id = r.get("id", "") or r.get("message_id", "")
                        if not msg_id:
                            continue

                        received_str = r.get("timestamp", "") or r.get("created_at", "")
                        try:
                            received_at = datetime.fromisoformat(
                                received_str.replace("Z", "+00:00")
                            )
                        except (ValueError, AttributeError):
                            received_at = datetime.now(timezone.utc)

                        replies.append(RawReply(
                            platform="instantly",
                            platform_message_id=f"instantly:{msg_id}",
                            email=r.get("from_email", "") or r.get("email", ""),
                            subject=r.get("subject", ""),
                            body=r.get("body", "") or r.get("text", ""),
                            received_at=received_at,
                            campaign_id=campaign_id,
                        ))
                except Exception:
                    logger.warning("instantly_campaign_poll_failed", campaign_id=campaign_id)

        except Exception:
            logger.error("instantly_poll_failed")

        return replies

    def _poll_lemlist(self) -> list[RawReply]:
        """Poll Lemlist for new replies."""
        replies: list[RawReply] = []
        try:
            client = LemlistClient()
            campaigns = client.list_campaigns()

            for campaign in campaigns:
                campaign_id = campaign.get("_id", "")
                if not campaign_id:
                    continue

                try:
                    activities = client.get_campaign_activities(campaign_id)
                    for activity in activities:
                        if activity.get("type") != "emailsReplied":
                            continue

                        msg_id = activity.get("_id", "")
                        if not msg_id:
                            continue

                        received_str = activity.get("createdAt", "")
                        try:
                            received_at = datetime.fromisoformat(
                                received_str.replace("Z", "+00:00")
                            )
                        except (ValueError, AttributeError):
                            received_at = datetime.now(timezone.utc)

                        replies.append(RawReply(
                            platform="lemlist",
                            platform_message_id=f"lemlist:{msg_id}",
                            email=activity.get("email", ""),
                            subject=activity.get("subject", ""),
                            body=activity.get("replyText", "") or activity.get("text", ""),
                            received_at=received_at,
                            campaign_id=campaign_id,
                        ))
                except Exception:
                    logger.warning("lemlist_campaign_poll_failed", campaign_id=campaign_id)

        except Exception:
            logger.error("lemlist_poll_failed")

        return replies

    def is_already_processed(self, platform_message_id: str) -> bool:
        """Check if a reply has already been saved to the DB."""
        with get_session() as session:
            stmt = (
                select(Reply.id)
                .where(Reply.platform_message_id == platform_message_id)
                .limit(1)
            )
            return session.execute(stmt).scalar_one_or_none() is not None

    def resolve_contact(self, email: str) -> int | None:
        """Find a contact ID by email address."""
        with get_session() as session:
            stmt = select(Contact.id).where(Contact.email == email).limit(1)
            return session.execute(stmt).scalar_one_or_none()

    def resolve_outreach_message(
        self, contact_id: int, platform: str, campaign_id: str | None
    ) -> int | None:
        """Find the outreach message for a contact on a given platform."""
        with get_session() as session:
            stmt = (
                select(OutreachMessage.id)
                .where(OutreachMessage.contact_id == contact_id)
                .where(OutreachMessage.platform == platform)
            )
            if campaign_id:
                stmt = stmt.where(OutreachMessage.campaign_id == campaign_id)
            stmt = stmt.order_by(OutreachMessage.created_at.desc()).limit(1)
            return session.execute(stmt).scalar_one_or_none()
