from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


@dataclass(frozen=True)
class BoardConfig:
    enabled: bool = True
    company_slugs: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ScrapingConfig:
    schedule_every_hours: int
    board_stagger_minutes: int
    request_delay_min_seconds: int
    request_delay_max_seconds: int
    max_requests_per_domain_per_second: float
    respect_robots_txt: bool
    job_max_age_hours: int
    dedup_window_days: int
    boards: dict[str, BoardConfig]
    search_queries: list[str]
    user_agents: list[str]


@dataclass(frozen=True)
class ScoringWeights:
    title_exact_match: int
    title_fuzzy_match: int
    funding_crunchbase_confirmed: int
    funding_keyword_in_jd: int
    saas_keyword_confirmed: int
    employee_count_25_to_500: int
    employee_count_500_to_1000: int
    posted_within_48h: int
    posted_48h_to_72h: int
    target_location: int
    staffing_agency_detected: int
    public_company_detected: int


@dataclass(frozen=True)
class RoleConfig:
    score: int
    titles: list[str]


@dataclass(frozen=True)
class ICPConfig:
    score_threshold: int
    target_funding_stages: list[str]
    min_employees: int
    max_employees: int
    target_locations: list[str]
    target_roles: dict[str, RoleConfig]
    scoring: ScoringWeights
    saas_signals: list[str]
    funding_signals: list[str]
    exclude_signals: list[str]


@dataclass(frozen=True)
class EnrichmentConfig:
    crunchbase_cache_ttl_days: int
    hunter_fallback_enabled: bool
    team_page_scrape_enabled: bool
    rocketreach_enabled: bool
    rocketreach_max_results: int
    min_contact_confidence_score: float


@dataclass(frozen=True)
class CRMConfig:
    provider: str
    re_enrollment_cooldown_days: int
    deal_stages: dict[str, str]
    hubspot: dict[str, Any]


@dataclass(frozen=True)
class InstantlyConfig:
    api_base_url: str
    default_campaign_id: str
    campaign_map: dict[str, str]
    custom_variables: list[str]


@dataclass(frozen=True)
class LemlistConfig:
    api_base_url: str
    linkedin_delay_hours: int
    campaign_map: dict[str, str]
    custom_variables: list[str]


@dataclass(frozen=True)
class CallReminderConfig:
    delay_days: int
    working_hours_start: int
    working_hours_end: int
    skip_weekends: bool


@dataclass(frozen=True)
class ReplyMonitoringConfig:
    poll_interval_minutes: int
    max_body_chars_for_ai: int
    gpt_model: str
    gpt_max_tokens: int
    gpt_temperature: float
    inbox_count: int
    min_confidence_for_auto_route: float


@dataclass(frozen=True)
class OOOConfig:
    pause_campaign_on_ooo: bool
    resume_days_after_return: int


@dataclass(frozen=True)
class RoutingConfig:
    booking_link: str
    recruiter_slack_ids: list[str]
    slack_channels: dict[str, str]
    ooo: OOOConfig


@dataclass(frozen=True)
class SlackAlertsConfig:
    notify_on_scrape_complete: bool
    notify_on_outreach_launched: bool
    notify_on_reply_routed: bool
    error_rate_alert_threshold: float
    consecutive_outreach_failures_threshold: int


@dataclass(frozen=True)
class RetryConfig:
    max_attempts: int
    backoff_base_seconds: int
    backoff_multiplier: int
    retryable_status_codes: list[int]


@dataclass(frozen=True)
class SystemConfig:
    name: str
    environment: str
    timezone: str
    log_level: str
    dry_run: bool


@dataclass(frozen=True)
class Settings:
    system: SystemConfig
    scraping: ScrapingConfig
    icp: ICPConfig
    enrichment: EnrichmentConfig
    crm: CRMConfig
    instantly: InstantlyConfig
    lemlist: LemlistConfig
    call_reminders: CallReminderConfig
    reply_monitoring: ReplyMonitoringConfig
    routing: RoutingConfig
    slack_alerts: SlackAlertsConfig
    retry: RetryConfig

    # Secrets from .env
    database_url: str = ""
    redis_url: str = ""
    crunchbase_api_key: str = ""
    hunter_api_key: str = ""
    rocketreach_api_key: str = ""
    instantly_api_key: str = ""
    lemlist_api_key: str = ""
    hubspot_api_key: str = ""
    openai_api_key: str = ""
    slack_webhook_url: str = ""
    slack_bot_token: str = ""
    calendly_link: str = ""


def _build_role_config(raw: dict[str, Any]) -> dict[str, RoleConfig]:
    return {
        name: RoleConfig(score=data["score"], titles=data["titles"])
        for name, data in raw.items()
    }


def _build_board_configs(raw: dict[str, Any]) -> dict[str, BoardConfig]:
    """Parse board config supporting both old (bool) and new (dict) formats."""
    boards: dict[str, BoardConfig] = {}
    for name, value in raw.items():
        if isinstance(value, bool):
            # Legacy format: board_name: true/false
            boards[name] = BoardConfig(enabled=value, company_slugs=[])
        elif isinstance(value, dict):
            boards[name] = BoardConfig(
                enabled=value.get("enabled", True),
                company_slugs=value.get("company_slugs", []),
            )
        else:
            boards[name] = BoardConfig(enabled=bool(value), company_slugs=[])
    return boards


def _load_settings(config_path: str | None = None) -> Settings:
    load_dotenv()

    if config_path is None:
        config_path = str(Path(__file__).parent.parent.parent / "config.yaml")

    with open(config_path) as f:
        cfg = yaml.safe_load(f)

    system = cfg["system"]
    scraping = cfg["scraping"]
    icp = cfg["icp"]
    enrichment = cfg["enrichment"]
    crm_cfg = cfg["crm"]
    instantly = cfg["instantly"]
    lemlist = cfg["lemlist"]
    call_reminders = cfg["call_reminders"]
    reply_mon = cfg["reply_monitoring"]
    routing = cfg["routing"]
    slack_alerts = cfg["slack_alerts"]
    retry = cfg["retry"]

    return Settings(
        system=SystemConfig(
            name=system["name"],
            environment=system["environment"],
            timezone=system["timezone"],
            log_level=system["log_level"],
            dry_run=system["dry_run"],
        ),
        scraping=ScrapingConfig(
            schedule_every_hours=scraping["schedule_every_hours"],
            board_stagger_minutes=scraping["board_stagger_minutes"],
            request_delay_min_seconds=scraping["request_delay_min_seconds"],
            request_delay_max_seconds=scraping["request_delay_max_seconds"],
            max_requests_per_domain_per_second=scraping["max_requests_per_domain_per_second"],
            respect_robots_txt=scraping["respect_robots_txt"],
            job_max_age_hours=scraping["job_max_age_hours"],
            dedup_window_days=scraping["dedup_window_days"],
            boards=_build_board_configs(scraping["boards"]),
            search_queries=scraping["search_queries"],
            user_agents=scraping["user_agents"],
        ),
        icp=ICPConfig(
            score_threshold=icp["score_threshold"],
            target_funding_stages=icp["target_funding_stages"],
            min_employees=icp["min_employees"],
            max_employees=icp["max_employees"],
            target_locations=icp["target_locations"],
            target_roles=_build_role_config(icp["target_roles"]),
            scoring=ScoringWeights(**icp["scoring"]),
            saas_signals=icp["saas_signals"],
            funding_signals=icp["funding_signals"],
            exclude_signals=icp["exclude_signals"],
        ),
        enrichment=EnrichmentConfig(
            crunchbase_cache_ttl_days=enrichment["crunchbase_cache_ttl_days"],
            hunter_fallback_enabled=enrichment["hunter_fallback_enabled"],
            team_page_scrape_enabled=enrichment["team_page_scrape_enabled"],
            rocketreach_enabled=enrichment.get("rocketreach_enabled", False),
            rocketreach_max_results=enrichment.get("rocketreach_max_results", 10),
            min_contact_confidence_score=enrichment["min_contact_confidence_score"],
        ),
        crm=CRMConfig(
            provider=crm_cfg["provider"],
            re_enrollment_cooldown_days=crm_cfg["re_enrollment_cooldown_days"],
            deal_stages=crm_cfg["deal_stages"],
            hubspot=crm_cfg["hubspot"],
        ),
        instantly=InstantlyConfig(
            api_base_url=instantly["api_base_url"],
            default_campaign_id=os.getenv("INSTANTLY_CAMPAIGN_ID_DEFAULT", ""),
            campaign_map=instantly["campaign_map"],
            custom_variables=instantly["custom_variables"],
        ),
        lemlist=LemlistConfig(
            api_base_url=lemlist["api_base_url"],
            linkedin_delay_hours=lemlist["linkedin_delay_hours"],
            campaign_map=lemlist["campaign_map"],
            custom_variables=lemlist["custom_variables"],
        ),
        call_reminders=CallReminderConfig(
            delay_days=call_reminders["delay_days"],
            working_hours_start=call_reminders["working_hours_start"],
            working_hours_end=call_reminders["working_hours_end"],
            skip_weekends=call_reminders["skip_weekends"],
        ),
        reply_monitoring=ReplyMonitoringConfig(
            poll_interval_minutes=reply_mon["poll_interval_minutes"],
            max_body_chars_for_ai=reply_mon["max_body_chars_for_ai"],
            gpt_model=reply_mon["gpt_model"],
            gpt_max_tokens=reply_mon["gpt_max_tokens"],
            gpt_temperature=reply_mon["gpt_temperature"],
            inbox_count=reply_mon["inbox_count"],
            min_confidence_for_auto_route=reply_mon["min_confidence_for_auto_route"],
        ),
        routing=RoutingConfig(
            booking_link=os.getenv("CALENDLY_LINK", ""),
            recruiter_slack_ids=routing["recruiter_slack_ids"],
            slack_channels={
                k: os.getenv(f"SLACK_CHANNEL_{k.upper()}", v)
                for k, v in routing["slack_channels"].items()
            },
            ooo=OOOConfig(
                pause_campaign_on_ooo=routing["ooo"]["pause_campaign_on_ooo"],
                resume_days_after_return=routing["ooo"]["resume_days_after_return"],
            ),
        ),
        slack_alerts=SlackAlertsConfig(
            notify_on_scrape_complete=slack_alerts["notify_on_scrape_complete"],
            notify_on_outreach_launched=slack_alerts["notify_on_outreach_launched"],
            notify_on_reply_routed=slack_alerts["notify_on_reply_routed"],
            error_rate_alert_threshold=slack_alerts["error_rate_alert_threshold"],
            consecutive_outreach_failures_threshold=slack_alerts[
                "consecutive_outreach_failures_threshold"
            ],
        ),
        retry=RetryConfig(
            max_attempts=retry["max_attempts"],
            backoff_base_seconds=retry["backoff_base_seconds"],
            backoff_multiplier=retry["backoff_multiplier"],
            retryable_status_codes=retry["retryable_status_codes"],
        ),
        database_url=os.getenv("DATABASE_URL", "postgresql://outreach:outreach@localhost:5432/outreach"),
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        crunchbase_api_key=os.getenv("CRUNCHBASE_API_KEY", ""),
        hunter_api_key=os.getenv("HUNTER_API_KEY", ""),
        rocketreach_api_key=os.getenv("ROCKETREACH_API_KEY", ""),
        instantly_api_key=os.getenv("INSTANTLY_API_KEY", ""),
        lemlist_api_key=os.getenv("LEMLIST_API_KEY", ""),
        hubspot_api_key=os.getenv("HUBSPOT_API_KEY", ""),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        slack_webhook_url=os.getenv("SLACK_WEBHOOK_URL", ""),
        slack_bot_token=os.getenv("SLACK_BOT_TOKEN", ""),
        calendly_link=os.getenv("CALENDLY_LINK", ""),
    )


@lru_cache(maxsize=1)
def get_settings(config_path: str | None = None) -> Settings:
    return _load_settings(config_path)
