from functools import lru_cache

import httpx

from src.config.settings import get_settings
from src.notifications.templates import TEMPLATES
from src.shared.exceptions import SlackError
from src.shared.logging import get_logger

logger = get_logger(__name__)


class SlackNotifier:
    """Sends Slack notifications via webhook and Bot API."""

    def __init__(self, webhook_url: str, bot_token: str) -> None:
        self.webhook_url = webhook_url
        self.bot_token = bot_token

    def send_webhook(self, template_name: str, **kwargs) -> None:
        """Send a message to the default webhook channel."""
        if not self.webhook_url:
            logger.warning("slack_webhook_not_configured")
            return

        message = self._render(template_name, **kwargs)

        try:
            with httpx.Client(timeout=10) as client:
                response = client.post(self.webhook_url, json={"text": message})
                if response.status_code != 200:
                    raise SlackError(f"Webhook returned {response.status_code}: {response.text}")
        except httpx.RequestError as e:
            raise SlackError(f"Webhook request failed: {e}") from e

        logger.info("slack_webhook_sent", template=template_name)

    def send_to_channel(self, channel: str, template_name: str, **kwargs) -> None:
        """Send a message to a specific Slack channel via Bot API."""
        if not self.bot_token:
            logger.warning("slack_bot_token_not_configured")
            return

        if not channel:
            logger.warning("slack_channel_not_configured", template=template_name)
            return

        message = self._render(template_name, **kwargs)

        try:
            with httpx.Client(timeout=10) as client:
                response = client.post(
                    "https://slack.com/api/chat.postMessage",
                    headers={"Authorization": f"Bearer {self.bot_token}"},
                    json={
                        "channel": channel,
                        "text": message,
                        "mrkdwn": True,
                    },
                )
                data = response.json()
                if not data.get("ok"):
                    raise SlackError(f"Slack API error: {data.get('error', 'unknown')}")
        except httpx.RequestError as e:
            raise SlackError(f"Slack API request failed: {e}") from e

        logger.info("slack_channel_message_sent", channel=channel, template=template_name)

    def _render(self, template_name: str, **kwargs) -> str:
        """Render a Slack message template with variables."""
        template = TEMPLATES.get(template_name)
        if template is None:
            raise SlackError(f"Unknown template: {template_name}")

        try:
            return template.format(**kwargs)
        except KeyError as e:
            raise SlackError(f"Missing template variable {e} for {template_name}") from e


@lru_cache(maxsize=1)
def get_slack_notifier() -> SlackNotifier:
    settings = get_settings()
    return SlackNotifier(
        webhook_url=settings.slack_webhook_url,
        bot_token=settings.slack_bot_token,
    )
