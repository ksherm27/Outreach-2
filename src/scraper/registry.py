from __future__ import annotations

from src.config.constants import JobBoard
from src.scraper.base import BaseScraper


_REGISTRY: dict[str, type[BaseScraper]] = {}
_BOARDS_IMPORTED = False


def register_scraper(board: str):
    """Decorator to register a scraper class for a board."""
    def decorator(cls: type[BaseScraper]):
        cls.board_name = board
        _REGISTRY[board] = cls
        return cls
    return decorator


def _ensure_boards_imported():
    """Import all board modules so scrapers register themselves."""
    global _BOARDS_IMPORTED
    if not _BOARDS_IMPORTED:
        import src.scraper.boards  # noqa: F401 — triggers @register_scraper decorators
        _BOARDS_IMPORTED = True


def get_scraper(board_name: str) -> BaseScraper:
    """Instantiate and return the scraper for the given board."""
    _ensure_boards_imported()
    cls = _REGISTRY.get(board_name)
    if cls is None:
        raise ValueError(f"No scraper registered for board: {board_name}")
    return cls()


def get_enabled_boards() -> list[str]:
    """Return list of board names that are both registered and enabled in config."""
    _ensure_boards_imported()
    from src.config.settings import get_settings
    settings = get_settings()
    return [
        board for board, cfg in settings.scraping.boards.items()
        if cfg.enabled and board in _REGISTRY
    ]


def get_board_config(board_name: str):
    """Return the BoardConfig for a given board."""
    from src.config.settings import get_settings
    settings = get_settings()
    return settings.scraping.boards.get(board_name)
