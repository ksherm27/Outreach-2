from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.config.settings import get_settings
from src.shared.exceptions import OutreachError

_RETRYABLE_EXCEPTIONS = (OutreachError, ConnectionError, TimeoutError)


def get_retry_decorator():
    """Returns a tenacity retry decorator configured from settings."""
    settings = get_settings()
    cfg = settings.retry
    return retry(
        stop=stop_after_attempt(cfg.max_attempts),
        wait=wait_exponential(
            multiplier=cfg.backoff_base_seconds,
            exp_base=cfg.backoff_multiplier,
        ),
        retry=retry_if_exception_type(_RETRYABLE_EXCEPTIONS),
        reraise=True,
    )


def get_celery_retry_kwargs() -> dict:
    """Returns kwargs for Celery task autoretry configuration."""
    settings = get_settings()
    cfg = settings.retry
    return {
        "autoretry_for": (Exception,),
        "retry_backoff": cfg.backoff_base_seconds,
        "retry_backoff_max": cfg.backoff_base_seconds * (cfg.backoff_multiplier ** cfg.max_attempts),
        "max_retries": cfg.max_attempts,
        "retry_jitter": True,
    }
