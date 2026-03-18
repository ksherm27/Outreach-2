class OutreachError(Exception):
    """Base exception for the outreach system."""


# Scraper errors
class ScraperError(OutreachError):
    """Error during scraping."""


class RateLimitError(ScraperError):
    """Rate limited by target site."""


class RobotsBlockedError(ScraperError):
    """Blocked by robots.txt."""


# Enrichment errors
class EnrichmentError(OutreachError):
    """Error during enrichment."""


class CrunchbaseError(EnrichmentError):
    """Crunchbase API error."""


class HunterError(EnrichmentError):
    """Hunter.io API error."""


class RocketReachError(EnrichmentError):
    """RocketReach API error."""


# Outreach errors
class OutreachAPIError(OutreachError):
    """Error calling outreach platform API."""


class InstantlyError(OutreachAPIError):
    """Instantly API error."""


class LemlistError(OutreachAPIError):
    """Lemlist API error."""


class HubSpotError(OutreachAPIError):
    """HubSpot API error."""


# Reply errors
class ClassificationError(OutreachError):
    """Error classifying a reply."""


# Notification errors
class SlackError(OutreachError):
    """Slack notification error."""
