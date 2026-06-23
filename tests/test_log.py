"""Tests for logging setup."""

from __future__ import annotations

from pathlib import Path

from mourice.config import Settings
from mourice.log import logger, setup_logging


def test_setup_logging_creates_file_sink(tmp_path: Path) -> None:
    settings = Settings(_env_file=None, log_level="DEBUG")  # type: ignore[call-arg]
    setup_logging(settings, log_dir=tmp_path)

    logger.info("hello from test")
    logger.complete()  # flush enqueued records

    log_file = tmp_path / "mourice.log"
    assert log_file.exists()
    assert "hello from test" in log_file.read_text(encoding="utf-8")


def test_setup_logging_captures_structured_fields(tmp_path: Path) -> None:
    settings = Settings(_env_file=None, log_level="INFO")  # type: ignore[call-arg]
    setup_logging(settings, log_dir=tmp_path)

    records: list[str] = []
    sink_id = logger.add(records.append, level="INFO", format="{extra[model]}")
    logger.bind(model="qwen2.5").info("model selected")
    logger.remove(sink_id)

    assert any("qwen2.5" in line for line in records)
