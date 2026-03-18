from datetime import date, datetime, timezone

import factory

from src.db.models.company import Company
from src.db.models.contact import Contact
from src.db.models.job import ScrapedJob
from src.db.models.outreach import OutreachMessage
from src.db.models.reply import Reply


class CompanyFactory(factory.Factory):
    class Meta:
        model = Company

    name = factory.Sequence(lambda n: f"Company {n}")
    domain = factory.Sequence(lambda n: f"company{n}.com")
    funding_stage = "Series B"
    employee_count = 200
    is_saas = True
    is_public = False


class ScrapedJobFactory(factory.Factory):
    class Meta:
        model = ScrapedJob

    source_url = factory.Sequence(lambda n: f"https://boards.greenhouse.io/company/jobs/{n}")
    board_name = "greenhouse"
    title = "VP of Sales"
    company_name = factory.Sequence(lambda n: f"Company {n}")
    location = "San Francisco, CA"
    description = "We are a Series B SaaS company looking for a VP of Sales."
    posted_date = factory.LazyFunction(lambda: date.today())


class ContactFactory(factory.Factory):
    class Meta:
        model = Contact

    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    email = factory.LazyAttribute(
        lambda o: f"{o.first_name.lower()}.{o.last_name.lower()}@example.com"
    )
    email_confidence = 0.95
    title = "VP of Sales"
    source = "hunter"
    company_id = 1


class OutreachMessageFactory(factory.Factory):
    class Meta:
        model = OutreachMessage

    contact_id = 1
    job_id = 1
    platform = "instantly"
    campaign_id = "camp_test123"
    status = "launched"
    variables = factory.LazyFunction(lambda: {"first_name": "Test"})


class ReplyFactory(factory.Factory):
    class Meta:
        model = Reply

    contact_id = 1
    platform = "instantly"
    platform_message_id = factory.Sequence(lambda n: f"instantly:msg_{n}")
    subject = "Re: Exciting opportunity"
    body = "Thanks for reaching out! I'd love to learn more."
    received_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))
