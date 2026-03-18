from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select

from src.celery_app import celery_app
from src.config.constants import OutreachStatus
from src.db.models.contact import Contact
from src.db.models.outreach import OutreachMessage
from src.db.models.reply import Reply
from src.db.session import get_session
from src.outreach.instantly import InstantlyClient
from src.outreach.lemlist import LemlistClient
from src.replies.actions import ReplyActionExecutor
from src.replies.classifier import ReplyClassifier
from src.replies.poller import ReplyPoller
from src.shared.logging import get_logger

logger = get_logger(__name__)


@celery_app.task(name="src.replies.tasks.poll_replies")
def poll_replies() -> dict:
    """Poll all inboxes for new replies and dispatch classification."""
    poller = ReplyPoller()
    raw_replies = poller.poll_all()

    new_count = 0
    for raw in raw_replies:
        # Skip already-processed replies
        if poller.is_already_processed(raw.platform_message_id):
            continue

        # Resolve contact
        contact_id = poller.resolve_contact(raw.email)
        if not contact_id:
            logger.debug("reply_from_unknown_contact", email=raw.email)
            continue

        # Resolve outreach message
        outreach_msg_id = poller.resolve_outreach_message(
            contact_id, raw.platform, raw.campaign_id
        )

        # Save reply to DB
        with get_session() as session:
            reply = Reply(
                outreach_message_id=outreach_msg_id,
                contact_id=contact_id,
                platform=raw.platform,
                platform_message_id=raw.platform_message_id,
                subject=raw.subject,
                body=raw.body,
                received_at=raw.received_at,
            )
            session.add(reply)
            session.flush()
            reply_id = reply.id

        # Dispatch classification
        classify_reply.delay(reply_id)
        new_count += 1

    logger.info("replies_polled", total=len(raw_replies), new=new_count)
    return {"polled": len(raw_replies), "new": new_count}


@celery_app.task(
    name="src.replies.tasks.classify_reply",
    bind=True,
    max_retries=3,
    default_retry_delay=10,
)
def classify_reply(self, reply_id: int) -> dict:
    """Classify a reply using GPT-4o and dispatch action."""
    with get_session() as session:
        reply = session.get(Reply, reply_id)
        if not reply:
            return {"status": "reply_not_found"}

        subject = reply.subject or ""
        body = reply.body or ""

    try:
        classifier = ReplyClassifier()
        result = classifier.classify(subject, body)

        # Save classification
        with get_session() as session:
            reply = session.get(Reply, reply_id)
            if reply:
                reply.reply_type = result.reply_type.value
                reply.classification_confidence = result.confidence
                reply.classification_reasoning = result.reasoning
                reply.ooo_return_date = result.ooo_return_date

        logger.info(
            "reply_classified",
            reply_id=reply_id,
            type=result.reply_type.value,
            confidence=result.confidence,
        )

        # Dispatch action
        execute_reply_action.delay(reply_id)

        return {
            "status": "classified",
            "type": result.reply_type.value,
            "confidence": result.confidence,
        }

    except Exception as exc:
        logger.error("reply_classification_failed", reply_id=reply_id, error=str(exc))
        raise self.retry(exc=exc)


@celery_app.task(
    name="src.replies.tasks.execute_reply_action",
    bind=True,
    max_retries=3,
    default_retry_delay=10,
)
def execute_reply_action(self, reply_id: int) -> dict:
    """Execute the automated action for a classified reply."""
    try:
        executor = ReplyActionExecutor()
        result = executor.execute(reply_id)

        logger.info("reply_action_executed", reply_id=reply_id, result=result)
        return result

    except Exception as exc:
        logger.error("reply_action_failed", reply_id=reply_id, error=str(exc))
        raise self.retry(exc=exc)


@celery_app.task(name="src.replies.tasks.resume_campaigns_after_ooo")
def resume_campaigns_after_ooo(contact_id: int) -> dict:
    """Resume campaigns for a contact after their OOO return date."""
    with get_session() as session:
        contact = session.get(Contact, contact_id)
        if not contact:
            return {"status": "contact_not_found"}

        email = contact.email

        msgs = list(
            session.execute(
                select(OutreachMessage)
                .where(OutreachMessage.contact_id == contact_id)
                .where(OutreachMessage.status == OutreachStatus.PAUSED)
            ).scalars().all()
        )

        resumed = 0
        for msg in msgs:
            try:
                if msg.platform == "instantly":
                    InstantlyClient().resume_lead(msg.campaign_id, email)
                elif msg.platform == "lemlist":
                    LemlistClient().resume_lead(msg.campaign_id, email)

                msg.status = OutreachStatus.LAUNCHED
                msg.paused_at = None
                resumed += 1
            except Exception:
                logger.warning(
                    "campaign_resume_failed",
                    platform=msg.platform,
                    campaign=msg.campaign_id,
                )

    logger.info("campaigns_resumed_after_ooo", contact_id=contact_id, resumed=resumed)
    return {"status": "resumed", "count": resumed}
