from __future__ import annotations

from src.config.constants import JobBoard
from src.scraper.base import BaseScraper


_REGISTRY: dict[str, type[BaseScraper]] = {}


def register_scraper(board: str):
    """Decorator to register a scraper class for a board."""
    def decorator(cls: type[BaseScraper]):
        cls.board_name = board
        _REGISTRY[board] = cls
        return cls
    return decorator


def get_scraper(board_name: str) -> BaseScraper:
    """Instantiate and return the scraper for the given board."""
    cls = _REGISTRY.get(board_name)
    if cls is None:
        raise ValueError(f"No scraper registered for board: {board_name}")
    return cls()


def get_enabled_boards() -> list[str]:
    """Return list of board names that are both registered and enabled in config."""
    from src.config.settings import get_settings
    settings = get_settings()
    return [
        board for board, enabled in settings.scraping.boards.items()
        if enabled and board in _REGISTRY
    ]
