import sys

if sys.version_info >= (3, 11):
    from enum import StrEnum
else:
    from enum import Enum

    class StrEnum(str, Enum):
        """Backport of StrEnum for Python < 3.11."""
        pass


class GTMRoleCategory(StrEnum):
    SALES_LEADERSHIP = "Sales Leadership"
    MARKETING_LEADERSHIP = "Marketing Leadership"
    CS_LEADERSHIP = "Customer Success Leadership"
    GTM_STRATEGY = "GTM Strategy"
    SDR_BDR_LEADERSHIP = "SDR BDR Leadership"


class ReplyType(StrEnum):
    POSITIVE = "positive"
    OBJECTION = "objection"
    OOO_WITH_DATE = "ooo_with_date"
    OOO_NO_DATE = "ooo_no_date"
    UNSUBSCRIBE = "unsubscribe"
    OTHER = "other"


class OutreachStatus(StrEnum):
    PENDING = "pending"
    LAUNCHED = "launched"
    PAUSED = "paused"
    COMPLETED = "completed"


class OutreachPlatform(StrEnum):
    INSTANTLY = "instantly"
    LEMLIST = "lemlist"


class ContactSource(StrEnum):
    HUNTER = "hunter"
    ROCKETREACH = "rocketreach"
    TEAM_PAGE = "team_page"
    MANUAL = "manual"


class SuppressionReason(StrEnum):
    UNSUBSCRIBE = "unsubscribe"
    BOUNCE = "bounce"
    MANUAL = "manual"


class ScrapeRunStatus(StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class JobBoard(StrEnum):
    LINKEDIN = "linkedin"
    INDEED = "indeed"
    GREENHOUSE = "greenhouse"
    LEVER = "lever"
    WORKDAY = "workday"
    BAMBOOHR = "bamboohr"
    ASHBY = "ashby"
    RIPPLING = "rippling"
    SMARTRECRUITERS = "smartrecruiters"
    JOBVITE = "jobvite"
    ICIMS = "icims"
    WORKABLE = "workable"
    JAZZHR = "jazzhr"
    RECRUITERBOX = "recruiterbox"
    WELLFOUND = "wellfound"


class CRMDealStage(StrEnum):
    OUTREACH_ACTIVE = "Outreach Active"
    REPLIED_POSITIVE = "Replied - Positive"
    REPLIED_OBJECTION = "Replied - Objection"
    MEETING_BOOKED = "Meeting Booked"
    UNSUBSCRIBED = "Unsubscribed"
