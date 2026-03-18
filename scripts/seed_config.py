#!/usr/bin/env python3
"""Validate config.yaml and seed initial data."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.settings import get_settings


def main():
    print("Validating config.yaml...")
    try:
        settings = get_settings()
        print(f"  System name: {settings.system.name}")
        print(f"  Environment: {settings.system.environment}")
        print(f"  Dry run: {settings.system.dry_run}")
        print()

        # Scraping
        enabled_boards = [b for b, v in settings.scraping.boards.items() if v]
        print(f"  Enabled boards: {len(enabled_boards)}")
        for b in enabled_boards:
            print(f"    - {b}")
        print(f"  Search queries: {len(settings.scraping.search_queries)}")
        print(f"  User agents: {len(settings.scraping.user_agents)}")
        print()

        # ICP
        print(f"  ICP score threshold: {settings.icp.score_threshold}")
        print(f"  Target roles: {len(settings.icp.target_roles)}")
        for name, role in settings.icp.target_roles.items():
            print(f"    - {name}: {len(role.titles)} titles (score weight: {role.score})")
        print(f"  SaaS signals: {len(settings.icp.saas_signals)}")
        print(f"  Funding signals: {len(settings.icp.funding_signals)}")
        print(f"  Exclude signals: {len(settings.icp.exclude_signals)}")
        print()

        # Secrets check
        print("  Checking secrets (.env)...")
        secrets = {
            "DATABASE_URL": bool(settings.database_url),
            "REDIS_URL": bool(settings.redis_url),
            "CRUNCHBASE_API_KEY": bool(settings.crunchbase_api_key),
            "HUNTER_API_KEY": bool(settings.hunter_api_key),
            "INSTANTLY_API_KEY": bool(settings.instantly_api_key),
            "LEMLIST_API_KEY": bool(settings.lemlist_api_key),
            "HUBSPOT_API_KEY": bool(settings.hubspot_api_key),
            "OPENAI_API_KEY": bool(settings.openai_api_key),
            "SLACK_WEBHOOK_URL": bool(settings.slack_webhook_url),
            "SLACK_BOT_TOKEN": bool(settings.slack_bot_token),
        }
        for name, configured in secrets.items():
            status = "OK" if configured else "MISSING"
            print(f"    {name}: {status}")

        missing = [k for k, v in secrets.items() if not v]
        if missing:
            print(f"\n  WARNING: {len(missing)} secrets not configured. Set them in .env")
        else:
            print("\n  All secrets configured.")

        print("\nConfig validation PASSED.")

    except Exception as e:
        print(f"\nConfig validation FAILED: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
