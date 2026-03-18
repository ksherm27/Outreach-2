"""Tests for Slack notification system."""

import pytest

from src.notifications.slack import SlackNotifier
from src.shared.exceptions import SlackError


class TestSlackNotifier:
    def test_render_template(self):
        notifier = SlackNotifier(webhook_url="", bot_token="")
        message = notifier._render(
            "scrape_board_complete",
            board_name="greenhouse",
            run_id=42,
            jobs_found=100,
            jobs_new=25,
        )
        assert "greenhouse" in message
        assert "42" in message
        assert "100" in message
        assert "25" in message

    def test_render_unknown_template_raises(self):
        notifier = SlackNotifier(webhook_url="", bot_token="")
        with pytest.raises(SlackError, match="Unknown template"):
            notifier._render("nonexistent_template")

    def test_render_missing_variable_raises(self):
        notifier = SlackNotifier(webhook_url="", bot_token="")
        with pytest.raises(SlackError, match="Missing template variable"):
            notifier._render("scrape_board_complete", board_name="greenhouse")
