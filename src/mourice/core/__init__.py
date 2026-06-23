"""Core orchestrator package (the agent loop). See docs/architecture.md."""

from .prompt import DEFAULT_LANGUAGE, build_system_prompt

__all__ = ["DEFAULT_LANGUAGE", "build_system_prompt"]
