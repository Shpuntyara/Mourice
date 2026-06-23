"""Structured logging setup for Mourice.

Console output is human-readable; the file sink is JSON (structured) so logs
can later be parsed for observability (which model was used, latency, tokens,
tool calls). See the "Наблюдаемость" design note.
"""

from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger

from mourice.config import Settings

__all__ = ["logger", "setup_logging"]

_CONSOLE_FORMAT = (
    "<green>{time:HH:mm:ss}</green> "
    "<level>{level: <8}</level> "
    "<cyan>{name}</cyan> - <level>{message}</level>"
)


def setup_logging(settings: Settings, *, log_dir: Path | None = None) -> None:
    """Configure the global loguru logger from settings.

    Adds two sinks:
    - stderr: colorized, human-readable, at ``settings.log_level``.
    - ``logs/mourice.log``: JSON (serialized) for machine parsing, rotated.

    Calling this more than once resets the sinks (idempotent), which keeps
    tests and repeated startups clean.
    """
    logger.remove()

    logger.add(
        sys.stderr,
        level=settings.log_level,
        format=_CONSOLE_FORMAT,
        backtrace=False,
        diagnose=False,
    )

    target_dir = log_dir if log_dir is not None else Path("logs")
    target_dir.mkdir(parents=True, exist_ok=True)
    logger.add(
        target_dir / "mourice.log",
        level=settings.log_level,
        serialize=True,
        rotation="10 MB",
        retention="10 days",
        encoding="utf-8",
        enqueue=True,
    )

    logger.debug("Logging configured at level {}", settings.log_level)
