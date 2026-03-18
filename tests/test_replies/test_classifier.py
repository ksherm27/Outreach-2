"""Tests for reply classifier."""

import json
from datetime import date

import pytest

from src.config.constants import ReplyType


class TestClassifierParsing:
    def test_parse_positive_response(self):
        from src.replies.classifier import ReplyClassifier

        classifier = ReplyClassifier.__new__(ReplyClassifier)
        classifier.min_confidence = 0.75

        content = json.dumps({
            "category": "positive",
            "confidence": 0.95,
            "ooo_return_date": None,
            "reasoning": "The person expressed interest in learning more.",
        })

        result = classifier._parse_response(content)
        assert result.reply_type == ReplyType.POSITIVE
        assert result.confidence == 0.95
        assert result.ooo_return_date is None

    def test_parse_ooo_with_date(self):
        from src.replies.classifier import ReplyClassifier

        classifier = ReplyClassifier.__new__(ReplyClassifier)
        classifier.min_confidence = 0.75

        content = json.dumps({
            "category": "ooo_with_date",
            "confidence": 0.99,
            "ooo_return_date": "2026-04-01",
            "reasoning": "Auto-reply with return date.",
        })

        result = classifier._parse_response(content)
        assert result.reply_type == ReplyType.OOO_WITH_DATE
        assert result.ooo_return_date == date(2026, 4, 1)

    def test_low_confidence_becomes_other(self):
        from src.replies.classifier import ReplyClassifier

        classifier = ReplyClassifier.__new__(ReplyClassifier)
        classifier.min_confidence = 0.75

        content = json.dumps({
            "category": "positive",
            "confidence": 0.3,
            "ooo_return_date": None,
            "reasoning": "Unclear intent.",
        })

        result = classifier._parse_response(content)
        assert result.reply_type == ReplyType.OTHER

    def test_parse_markdown_wrapped_json(self):
        from src.replies.classifier import ReplyClassifier

        classifier = ReplyClassifier.__new__(ReplyClassifier)
        classifier.min_confidence = 0.75

        content = """```json
{"category": "unsubscribe", "confidence": 0.98, "ooo_return_date": null, "reasoning": "Asked to stop emails."}
```"""

        result = classifier._parse_response(content)
        assert result.reply_type == ReplyType.UNSUBSCRIBE

    def test_parse_invalid_json_returns_other(self):
        from src.replies.classifier import ReplyClassifier

        classifier = ReplyClassifier.__new__(ReplyClassifier)
        classifier.min_confidence = 0.75

        result = classifier._parse_response("this is not json")
        assert result.reply_type == ReplyType.OTHER
        assert result.confidence == 0.0
