from celery import Celery
from celery.schedules import crontab

from src.config.settings import get_settings


def create_celery_app() -> Celery:
    settings = get_settings()

    app = Celery("outreach")
    app.conf.update(
        broker_url=settings.redis_url,
        result_backend=settings.redis_url,
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone=settings.system.timezone,
        enable_utc=True,
        task_track_started=True,
        task_acks_late=True,
        worker_prefetch_multiplier=1,
    )

    app.conf.beat_schedule = {
        "scrape-all-boards": {
            "task": "src.scraper.tasks.scrape_all_boards",
            "schedule": crontab(
                minute=0,
                hour=f"*/{settings.scraping.schedule_every_hours}",
            ),
        },
        "score-new-jobs": {
            "task": "src.scoring.tasks.score_unscored_jobs",
            "schedule": crontab(minute=15, hour="*"),
        },
        "poll-replies": {
            "task": "src.replies.tasks.poll_replies",
            "schedule": settings.reply_monitoring.poll_interval_minutes * 60.0,
        },
        "cleanup-enrichment-cache": {
            "task": "src.enrichment.tasks.cleanup_cache",
            "schedule": crontab(minute=0, hour=3),
        },
    }

    app.autodiscover_tasks([
        "src.scraper",
        "src.scoring",
        "src.enrichment",
        "src.outreach",
        "src.replies",
    ])

    return app


celery_app = create_celery_app()
