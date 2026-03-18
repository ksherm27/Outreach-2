from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from src.celery_app import celery_app
from src.config.constants import CRMDealStage, OutreachPlatform, OutreachStatus
from src.config.settings import get_settings
from src.db.models.company import Company
from src.db.models.contact import Contact
from src.db.models.job import ScrapedJob
from src.db.models.outreach import OutreachMessage
from src.db.models.system import SuppressionList
from src.db.session import get_session
from src.outreach.campaign_mapper import get_campaign_ids
from src.outreach.hubspot import HubSpotClient
from src.outreach.instantly import InstantlyClient
from src.outreach.lemlist import LemlistClient
from src.outreach.variables import build_instantly_variables, build_lemlist_variables
from src.shared.logging import get_logger

logger = get_logger(__name__)


@celery_app.task(
    name="src.outreach.tasks.push_to_campaigns",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
)
def push_to_campaigns(self, contact_id: int, job_id: int) -> dict:
    """Push a contact into Instantly and Lemlist campaigns + create HubSpot deal."""
    settings = get_settings()

    with get_session() as session:
        contact = session.get(Contact, contact_id)
        if not contact:
            return {"status": "contact_not_found"}

        # Check suppression list
        suppressed = session.execute(
            select(SuppressionList).where(SuppressionList.email == contact.email)
        ).scalar_one_or_none()
        if suppressed:
            logger.info("contact_suppressed", email=contact.email)
            return {"status": "suppressed"}

        job = session.get(ScrapedJob, job_id)
        if not job:
            return {"status": "job_not_found"}

        company = session.get(Company, contact.company_id)
        if not company:
            return {"status": "company_not_found"}

        gtm_category = job.gtm_category or "default"
        campaign_ids = get_campaign_ids(gtm_category)

        if settings.system.dry_run:
            logger.info("dry_run_skip_outreach", email=contact.email)
            return {"status": "dry_run"}

    now = datetime.now(timezone.utc)

    # Push to Instantly
    instantly_msg_id = None
    if campaign_ids.instantly_campaign_id:
        try:
            with get_session() as session:
                contact = session.get(Contact, contact_id)
                company = session.get(Company, contact.company_id)
                job = session.get(ScrapedJob, job_id)
                variables = build_instantly_variables(contact, company, job)

            instantly = InstantlyClient()
            instantly.add_lead(
                campaign_id=campaign_ids.instantly_campaign_id,
                email=contact.email,
                first_name=contact.first_name,
                last_name=contact.last_name,
                company_name=company.name,
                variables=variables,
            )

            with get_session() as session:
                msg = OutreachMessage(
                    contact_id=contact_id,
                    job_id=job_id,
                    platform=OutreachPlatform.INSTANTLY,
                    campaign_id=campaign_ids.instantly_campaign_id,
                    status=OutreachStatus.LAUNCHED,
                    variables=variables,
                    launched_at=now,
                )
                session.add(msg)
                session.flush()
                instantly_msg_id = msg.id

        except Exception as exc:
            logger.error("instantly_push_failed", email=contact.email, error=str(exc))
            raise self.retry(exc=exc)

    # Push to Lemlist
    lemlist_msg_id = None
    if campaign_ids.lemlist_campaign_id:
        try:
            with get_session() as session:
                contact = session.get(Contact, contact_id)
                company = session.get(Company, contact.company_id)
                job = session.get(ScrapedJob, job_id)
                variables = build_lemlist_variables(contact, company, job)

            lemlist = LemlistClient()
            lemlist.add_lead(
                campaign_id=campaign_ids.lemlist_campaign_id,
                email=contact.email,
                first_name=contact.first_name,
                last_name=contact.last_name,
                company_name=company.name,
                variables=variables,
            )

            with get_session() as session:
                msg = OutreachMessage(
                    contact_id=contact_id,
                    job_id=job_id,
                    platform=OutreachPlatform.LEMLIST,
                    campaign_id=campaign_ids.lemlist_campaign_id,
                    status=OutreachStatus.LAUNCHED,
                    variables=variables,
                    launched_at=now,
                )
                session.add(msg)
                session.flush()
                lemlist_msg_id = msg.id

        except Exception as exc:
            logger.error("lemlist_push_failed", email=contact.email, error=str(exc))
            # Don't fail the whole task if Lemlist fails but Instantly succeeded

    # Create HubSpot deal
    create_hubspot_deal.delay(contact_id, job_id)

    # Schedule call reminder
    schedule_call_reminder.delay(contact_id, now.isoformat())

    logger.info(
        "outreach_launched",
        contact_id=contact_id,
        instantly_msg=instantly_msg_id,
        lemlist_msg=lemlist_msg_id,
    )

    return {
        "status": "launched",
        "instantly_msg_id": instantly_msg_id,
        "lemlist_msg_id": lemlist_msg_id,
    }


@celery_app.task(
    name="src.outreach.tasks.create_hubspot_deal",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
)
def create_hubspot_deal(self, contact_id: int, job_id: int) -> dict:
    """Create or update a HubSpot deal for a contact."""
    settings = get_settings()

    if settings.system.dry_run:
        return {"status": "dry_run"}

    with get_session() as session:
        contact = session.get(Contact, contact_id)
        if not contact:
            return {"status": "contact_not_found"}

        company = session.get(Company, contact.company_id)
        job = session.get(ScrapedJob, job_id)

    try:
        hubspot = HubSpotClient()

        # Create/update contact in HubSpot
        hs_properties = {
            "firstname": contact.first_name or "",
            "lastname": contact.last_name or "",
            "jobtitle": contact.title or "",
            "company": company.name if company else "",
        }
        hs_contact = hubspot.create_or_update_contact(contact.email, hs_properties)
        hs_contact_id = hs_contact["id"]

        # Save HubSpot contact ID
        with get_session() as session:
            c = session.get(Contact, contact_id)
            if c:
                c.hubspot_contact_id = hs_contact_id

        # Create deal
        deal_name = f"{contact.first_name or ''} {contact.last_name or ''} - {company.name if company else ''}".strip()
        deal = hubspot.create_deal(
            deal_name=deal_name,
            stage=CRMDealStage.OUTREACH_ACTIVE,
            contact_id=hs_contact_id,
            properties={
                "description": f"ICP Score: {job.icp_score or 0}/100 | Category: {job.gtm_category or 'Unknown'}",
            },
        )

        # Save deal ID to outreach messages
        with get_session() as session:
            msgs = list(
                session.execute(
                    select(OutreachMessage)
                    .where(OutreachMessage.contact_id == contact_id)
                    .where(OutreachMessage.job_id == job_id)
                ).scalars().all()
            )
            for msg in msgs:
                msg.hubspot_deal_id = deal["id"]

        logger.info("hubspot_deal_created", contact_id=contact_id, deal_id=deal["id"])
        return {"status": "created", "deal_id": deal["id"]}

    except Exception as exc:
        logger.error("hubspot_deal_failed", contact_id=contact_id, error=str(exc))
        raise self.retry(exc=exc)


@celery_app.task(name="src.outreach.tasks.schedule_call_reminder")
def schedule_call_reminder(contact_id: int, launched_at_iso: str) -> dict:
    """Schedule a call reminder for N business days after outreach launch."""
    settings = get_settings()
    launched_at = datetime.fromisoformat(launched_at_iso)
    delay_days = settings.call_reminders.delay_days

    # Calculate business days
    reminder_date = launched_at
    days_added = 0
    while days_added < delay_days:
        reminder_date += timedelta(days=1)
        if settings.call_reminders.skip_weekends and reminder_date.weekday() >= 5:
            continue
        days_added += 1

    # Set to working hours
    reminder_date = reminder_date.replace(
        hour=settings.call_reminders.working_hours_start,
        minute=0,
        second=0,
    )

    # Schedule the task
    send_call_reminder.apply_async(
        args=[contact_id],
        eta=reminder_date,
    )

    # Update outreach message with reminder time
    with get_session() as session:
        msgs = list(
            session.execute(
                select(OutreachMessage).where(OutreachMessage.contact_id == contact_id)
            ).scalars().all()
        )
        for msg in msgs:
            msg.call_reminder_at = reminder_date

    logger.info("call_reminder_scheduled", contact_id=contact_id, remind_at=reminder_date.isoformat())
    return {"status": "scheduled", "remind_at": reminder_date.isoformat()}


@celery_app.task(name="src.outreach.tasks.send_call_reminder")
def send_call_reminder(contact_id: int) -> dict:
    """Send a Slack reminder to call a prospect."""
    with get_session() as session:
        contact = session.get(Contact, contact_id)
        if not contact:
            return {"status": "contact_not_found"}

        company = session.get(Company, contact.company_id)

    try:
        from src.notifications.slack import get_slack_notifier
        settings = get_settings()
        notifier = get_slack_notifier()

        recruiter_id = contact.assigned_recruiter or (
            settings.routing.recruiter_slack_ids[0]
            if settings.routing.recruiter_slack_ids
            else ""
        )

        channel = settings.routing.slack_channels.get("positive_replies", "")
        if channel:
            notifier.send_to_channel(
                channel,
                "call_reminder",
                first_name=contact.first_name or "",
                last_name=contact.last_name or "",
                company=company.name if company else "",
                title=contact.title or "",
                email=contact.email,
                recruiter_slack_id=recruiter_id,
            )

    except Exception:
        logger.warning("call_reminder_notification_failed", contact_id=contact_id)

    return {"status": "sent"}
