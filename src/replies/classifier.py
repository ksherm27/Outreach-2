from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date

import httpx

from src.config.constants import ReplyType
from src.config.settings import get_settings
from src.shared.exceptions import ClassificationError
from src.shared.logging import get_logger

logger = get_logger(__name__)

CLASSIFICATION_SYSTEM_PROMPT = """You are a reply classifier for a B2B sales outreach system.

Classify the email reply into exactly ONE of these categories:

1. "positive" — The person is interested, open to chatting, wants to learn more, or asks about next steps.
2. "objection" — The person pushes back (not interested, bad timing, wrong person, already has a solution) but hasn't asked to unsubscribe.
3. "ooo_with_date" — An out-of-office auto-reply that includes a return date.
4. "ooo_no_date" — An out-of-office auto-reply with no return date mentioned.
5. "unsubscribe" — The person explicitly asks to be removed, stop emails, or unsubscribe.
6. "other" — Doesn't fit the above categories (random questions, spam, forwarded, etc.).

Respond with ONLY valid JSON:
{
  "category": "<one of the 6 categories above>",
  "confidence": <float 0.0-1.0>,
  "ooo_return_date": "<YYYY-MM-DD or null>",
  "reasoning": "<1 sentence explanation>"
}"""


@dataclass
class ClassificationResult:
    reply_type: ReplyType
    confidence: float
    ooo_return_date: date | None
    reasoning: str


class ReplyClassifier:
    """Classifies email replies using GPT-4o."""

    def __init__(self) -> None:
        settings = get_settings()
        self.api_key = settings.openai_api_key
        self.model = settings.reply_monitoring.gpt_model
        self.max_tokens = settings.reply_monitoring.gpt_max_tokens
        self.temperature = settings.reply_monitoring.gpt_temperature
        self.max_body_chars = settings.reply_monitoring.max_body_chars_for_ai
        self.min_confidence = settings.reply_monitoring.min_confidence_for_auto_route

    def classify(self, subject: str, body: str) -> ClassificationResult:
        """Classify a reply into a category."""
        if not self.api_key:
            raise ClassificationError("OpenAI API key not configured")

        # Truncate body
        truncated_body = body[: self.max_body_chars]

        user_message = f"Subject: {subject}\n\nBody:\n{truncated_body}"

        try:
            with httpx.Client(timeout=30) as client:
                response = client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": CLASSIFICATION_SYSTEM_PROMPT},
                            {"role": "user", "content": user_message},
                        ],
                        "max_tokens": self.max_tokens,
                        "temperature": self.temperature,
                    },
                )

                if response.status_code != 200:
                    raise ClassificationError(
                        f"OpenAI API error {response.status_code}: {response.text}"
                    )

                data = response.json()
                content = data["choices"][0]["message"]["content"]

                return self._parse_response(content)

        except httpx.RequestError as e:
            raise ClassificationError(f"OpenAI request failed: {e}") from e

    def _parse_response(self, content: str) -> ClassificationResult:
        """Parse the JSON response from GPT-4o."""
        try:
            # Handle markdown-wrapped JSON
            cleaned = content.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
                cleaned = cleaned.rsplit("```", 1)[0]

            result = json.loads(cleaned)

            category = result.get("category", "other")
            confidence = float(result.get("confidence", 0.0))
            reasoning = result.get("reasoning", "")

            # Parse OOO return date
            ooo_return_date = None
            raw_date = result.get("ooo_return_date")
            if raw_date and raw_date != "null":
                try:
                    ooo_return_date = date.fromisoformat(raw_date)
                except ValueError:
                    pass

            # Map to ReplyType enum
            type_map = {
                "positive": ReplyType.POSITIVE,
                "objection": ReplyType.OBJECTION,
                "ooo_with_date": ReplyType.OOO_WITH_DATE,
                "ooo_no_date": ReplyType.OOO_NO_DATE,
                "unsubscribe": ReplyType.UNSUBSCRIBE,
                "other": ReplyType.OTHER,
            }
            reply_type = type_map.get(category, ReplyType.OTHER)

            # If confidence is below threshold, downgrade to OTHER
            if confidence < self.min_confidence and reply_type != ReplyType.OTHER:
                logger.info(
                    "low_confidence_classification",
                    original=reply_type,
                    confidence=confidence,
                )
                reply_type = ReplyType.OTHER

            return ClassificationResult(
                reply_type=reply_type,
                confidence=confidence,
                ooo_return_date=ooo_return_date,
                reasoning=reasoning,
            )

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.error("classification_parse_failed", content=content, error=str(e))
            return ClassificationResult(
                reply_type=ReplyType.OTHER,
                confidence=0.0,
                ooo_return_date=None,
                reasoning=f"Failed to parse classifier response: {e}",
            )
