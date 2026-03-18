from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from src.config.constants import CRMDealStage, OutreachStatus, ReplyType, SuppressionReason
from src.config.settings import get_settings
from src.db.models.company import Company
from src.db.models.contact import Contact
from src.db.models.job import ScrapedJob
from src.db.models.outreach import OutreachMessage
from src.db.models.reply import Reply
from src.db.models.system import SuppressionList
from src.db.session import get_session
from src.notifications.slack import get_slack_notifier
from src.outreach.hubspot import HubSpotClient
from src.outreach.instantly import InstantlyClient
from src.outreach.lemlist import LemlistClient
from src.replies.assignment import RecruiterAssigner
from src.shared.logging import get_logger

logger = get_logger(__name__)


class ReplyActionExecutor:
    """Executes automated actions based on reply classification."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.assigner = RecruiterAssigner()

    def execute(self, reply_id: int) -> dict:
        """Execute the appropriate action for a classified reply."""
        with get_session() as session:
            reply = session.get(Reply, reply_id)
            if not reply:
                return {"status": "reply_not_found"}

            reply_type = ReplyType(reply.reply_type) if reply.reply_type else ReplyType.OTHER
            contact = session.get(Contact, reply.contact_id)
            if not contact:
                return {"status": "contact_not_found"}

            contact_id = reply.contact_id

        # Assign recruiter
        recruiter_id = self.assigner.assign(contact_id)

        # Dispatch to handler
        handlers = {
            ReplyType.POSITIVE: self._handle_positive,
            ReplyType.OBJECTION: self._handle_objection,
            ReplyType.OOO_WITH_DATE: self._handle_ooo_with_date,
            ReplyType.OOO_NO_DATE: self._handle_ooo_no_date,
            ReplyType.UNSUBSCRIBE: self._handle_unsubscribe,
            ReplyType.OTHER: self._handle_other,
        }

        handler = handlers.get(reply_type, self._handle_other)
        result = handler(reply_id, recruiter_id)

        # Mark action taken
        with get_session() as session:
            reply = session.get(Reply, reply_id)
            if reply:
                reply.action_taken = reply_type.value
                reply.action_taken_at = datetime.now(timezone.utc)
                reply.assigned_recruiter = recruiter_id

        return result

    def _handle_positive(self, reply_id: int, recruiter_id: str) -> dict:
        """Handle positive reply: send booking link, pause campaigns, update CRM, notify."""
        ctx = self._load_context(reply_id)
        if not ctx:
            return {"status": "context_not_found"}

        # Pause all campaigns for this contact
        self._pause_campaigns(ctx["contact_id"])

        # Update CRM deal stage
        self._update_crm_stage(ctx["contact_id"], CRMDealStage.REPLIED_POSITIVE)

        # Send Slack notification
        try:
            notifier = get_slack_notifier()
            channel = self.settings.routing.slack_channels.get("positive_replies", "")
            if channel:
                notifier.send_to_channel(
                    channel,
                    "reply_positive",
                    first_name=ctx["first_name"],
                    last_name=ctx["last_name"],
                    title=ctx["title"],
                    company=ctx["company_name"],
                    funding_stage=ctx["funding_stage"],
                    icp_score=ctx["icp_score"],
                    gtm_role_category=ctx["gtm_category"],
                    reply_excerpt=ctx["reply_excerpt"],
                    prospect_email=ctx["email"],
                    crm_deal_stage=CRMDealStage.REPLIED_POSITIVE,
                    recruiter_slack_id=recruiter_id,
                    crm_deal_link=ctx.get("crm_deal_link", ""),
                    linkedin_url=ctx.get("linkedin_url", ""),
                )
        except Exception:
            logger.warning("slack_positive_notification_failed", reply_id=reply_id)

        logger.info("positive_reply_handled", reply_id=reply_id)
        return {"status": "positive_handled"}

    def _handle_objection(self, reply_id: int, recruiter_id: str) -> dict:
        """Handle objection: pause campaigns, notify for human review."""
        ctx = self._load_context(reply_id)
        if not ctx:
            return {"status": "context_not_found"}

        self._pause_campaigns(ctx["contact_id"])
        self._update_crm_stage(ctx["contact_id"], CRMDealStage.REPLIED_OBJECTION)

        try:
            notifier = get_slack_notifier()
            channel = self.settings.routing.slack_channels.get("objections", "")
            if channel:
                notifier.send_to_channel(
                    channel,
                    "reply_objection",
                    first_name=ctx["first_name"],
                    last_name=ctx["last_name"],
                    title=ctx["title"],
                    company=ctx["company_name"],
                    funding_stage=ctx["funding_stage"],
                    icp_score=ctx["icp_score"],
                    reply_excerpt=ctx["reply_excerpt"],
                    confidence_pct=int(ctx["confidence"] * 100),
                    recruiter_slack_id=recruiter_id,
                    crm_deal_link=ctx.get("crm_deal_link", ""),
                )
        except Exception:
            logger.warning("slack_objection_notification_failed", reply_id=reply_id)

        logger.info("objection_reply_handled", reply_id=reply_id)
        return {"status": "objection_handled"}

    def _handle_ooo_with_date(self, reply_id: int, recruiter_id: str) -> dict:
        """Handle OOO with date: pause, schedule resume, reschedule call."""
        ctx = self._load_context(reply_id)
        if not ctx:
            return {"status": "context_not_found"}

        self._pause_campaigns(ctx["contact_id"])

        # Calculate resume date
        ooo_return_date = ctx.get("ooo_return_date")
        resume_days = self.settings.routing.ooo.resume_days_after_return
        resume_date = None
        if ooo_return_date:
            resume_date = ooo_return_date + timedelta(days=resume_days)

            # Schedule campaign resume
            from src.replies.tasks import resume_campaigns_after_ooo
            resume_dt = datetime.combine(resume_date, datetime.min.time()).replace(
                tzinfo=timezone.utc, hour=9
            )
            resume_campaigns_after_ooo.apply_async(
                args=[ctx["contact_id"]],
                eta=resume_dt,
            )

        try:
            notifier = get_slack_notifier()
            channel = self.settings.routing.slack_channels.get("out_of_office", "")
            if channel:
                notifier.send_to_channel(
                    channel,
                    "reply_ooo_with_date",
                    first_name=ctx["first_name"],
                    last_name=ctx["last_name"],
                    company=ctx["company_name"],
                    return_date=str(ooo_return_date) if ooo_return_date else "Unknown",
                    resume_date=str(resume_date) if resume_date else "Manual",
                    new_call_reminder_date=str(resume_date) if resume_date else "TBD",
                )
        except Exception:
            logger.warning("slack_ooo_notification_failed", reply_id=reply_id)

        logger.info("ooo_with_date_handled", reply_id=reply_id)
        return {"status": "ooo_with_date_handled"}

    def _handle_ooo_no_date(self, reply_id: int, recruiter_id: str) -> dict:
        """Handle OOO without date: pause, flag for manual review."""
        ctx = self._load_context(reply_id)
        if not ctx:
            return {"status": "context_not_found"}

        self._pause_campaigns(ctx["contact_id"])

        try:
            notifier = get_slack_notifier()
            channel = self.settings.routing.slack_channels.get("out_of_office", "")
            if channel:
                notifier.send_to_channel(
                    channel,
                    "reply_ooo_no_date",
                    first_name=ctx["first_name"],
                    last_name=ctx["last_name"],
                    company=ctx["company_name"],
                    recruiter_slack_id=recruiter_id,
                    crm_deal_link=ctx.get("crm_deal_link", ""),
                )
        except Exception:
            logger.warning("slack_ooo_no_date_notification_failed", reply_id=reply_id)

        logger.info("ooo_no_date_handled", reply_id=reply_id)
        return {"status": "ooo_no_date_handled"}

    def _handle_unsubscribe(self, reply_id: int, recruiter_id: str) -> dict:
        """Handle unsubscribe: suppress everywhere, update CRM."""
        ctx = self._load_context(reply_id)
        if not ctx:
            return {"status": "context_not_found"}

        email = ctx["email"]

        # Add to suppression list
        with get_session() as session:
            existing = session.execute(
                select(SuppressionList).where(SuppressionList.email == email)
            ).scalar_one_or_none()

            if not existing:
                suppression = SuppressionList(
                    email=email,
                    reason=SuppressionReason.UNSUBSCRIBE,
                    suppressed_at=datetime.now(timezone.utc),
                    source_reply_id=reply_id,
                )
                session.add(suppression)

            # Mark contact as suppressed
            contact = session.get(Contact, ctx["contact_id"])
            if contact:
                contact.is_suppressed = True

        # Pause and remove from all campaigns
        self._pause_campaigns(ctx["contact_id"])

        # Update CRM
        self._update_crm_stage(ctx["contact_id"], CRMDealStage.UNSUBSCRIBED)

        try:
            notifier = get_slack_notifier()
            channel = self.settings.routing.slack_channels.get("unsubscribes", "")
            if channel:
                notifier.send_to_channel(
                    channel,
                    "reply_unsubscribe",
                    first_name=ctx["first_name"],
                    last_name=ctx["last_name"],
                    company=ctx["company_name"],
                    prospect_email=email,
                )
        except Exception:
            logger.warning("slack_unsubscribe_notification_failed", reply_id=reply_id)

        logger.info("unsubscribe_handled", reply_id=reply_id, email=email)
        return {"status": "unsubscribed"}

    def _handle_other(self, reply_id: int, recruiter_id: str) -> dict:
        """Handle unknown/unclassified: flag for human review."""
        ctx = self._load_context(reply_id)
        if not ctx:
            return {"status": "context_not_found"}

        try:
            notifier = get_slack_notifier()
            channel = self.settings.routing.slack_channels.get("unknown_replies", "")
            if channel:
                notifier.send_to_channel(
                    channel,
                    "reply_other",
                    first_name=ctx["first_name"],
                    last_name=ctx["last_name"],
                    company=ctx["company_name"],
                    confidence_pct=int(ctx["confidence"] * 100),
                    reply_excerpt=ctx["reply_excerpt"],
                    recruiter_slack_id=recruiter_id,
                    crm_deal_link=ctx.get("crm_deal_link", ""),
                )
        except Exception:
            logger.warning("slack_other_notification_failed", reply_id=reply_id)

        logger.info("other_reply_handled", reply_id=reply_id)
        return {"status": "other_handled"}

    # -- Helpers --

    def _load_context(self, reply_id: int) -> dict | None:
        """Load all context needed for reply actions."""
        with get_session() as session:
            reply = session.get(Reply, reply_id)
            if not reply:
                return None

            contact = session.get(Contact, reply.contact_id)
            if not contact:
                return None

            company = session.get(Company, contact.company_id) if contact.company_id else None

            # Get the job/outreach context
            outreach_msg = None
            if reply.outreach_message_id:
                outreach_msg = session.get(OutreachMessage, reply.outreach_message_id)

            job = None
            if outreach_msg and outreach_msg.job_id:
                job = session.get(ScrapedJob, outreach_msg.job_id)

            return {
                "reply_id": reply.id,
                "contact_id": contact.id,
                "email": contact.email,
                "first_name": contact.first_name or "",
                "last_name": contact.last_name or "",
                "title": contact.title or "",
                "company_name": company.name if company else "",
                "funding_stage": company.funding_stage if company else "",
                "icp_score": job.icp_score if job else 0,
                "gtm_category": job.gtm_category if job else "",
                "reply_excerpt": reply.body[:300] if reply.body else "",
                "confidence": reply.classification_confidence or 0.0,
                "ooo_return_date": reply.ooo_return_date,
                "linkedin_url": contact.linkedin_url or "",
                "crm_deal_link": (
                    f"https://app.hubspot.com/contacts/deals/{outreach_msg.hubspot_deal_id}"
                    if outreach_msg and outreach_msg.hubspot_deal_id
                    else ""
                ),
            }

    def _pause_campaigns(self, contact_id: int) -> None:
        """Pause all active campaigns for a contact."""
        with get_session() as session:
            msgs = list(
                session.execute(
                    select(OutreachMessage)
                    .where(OutreachMessage.contact_id == contact_id)
                    .where(OutreachMessage.status == OutreachStatus.LAUNCHED)
                ).scalars().all()
            )

            contact = session.get(Contact, contact_id)
            if not contact:
                return

            email = contact.email

            for msg in msgs:
                try:
                    if msg.platform == "instantly":
                        InstantlyClient().pause_lead(msg.campaign_id, email)
                    elif msg.platform == "lemlist":
                        LemlistClient().pause_lead(msg.campaign_id, email)

                    msg.status = OutreachStatus.PAUSED
                    msg.paused_at = datetime.now(timezone.utc)
                except Exception:
                    logger.warning(
                        "campaign_pause_failed",
                        platform=msg.platform,
                        campaign=msg.campaign_id,
                        email=email,
                    )

    def _update_crm_stage(self, contact_id: int, stage: CRMDealStage) -> None:
        """Update CRM deal stage for all outreach messages of a contact."""
        with get_session() as session:
            msgs = list(
                session.execute(
                    select(OutreachMessage)
                    .where(OutreachMessage.contact_id == contact_id)
                    .where(OutreachMessage.hubspot_deal_id.isnot(None))
                ).scalars().all()
            )

            deal_ids = {msg.hubspot_deal_id for msg in msgs if msg.hubspot_deal_id}

        try:
            hubspot = HubSpotClient()
            for deal_id in deal_ids:
                hubspot.update_deal_stage(deal_id, stage.value)
        except Exception:
            logger.warning("crm_stage_update_failed", stage=stage.value)
