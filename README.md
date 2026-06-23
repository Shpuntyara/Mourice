# Mourice

> A personal AI assistant orchestrator — self-hosted, multi-LLM, grounded in a personal knowledge base.

[![CI](https://github.com/Shpuntyara/Mourice/actions/workflows/ci.yml/badge.svg)](https://github.com/Shpuntyara/Mourice/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.13-blue)
![License](https://img.shields.io/badge/license-MIT-green)

Mourice is **not** just an LLM wrapper. It's a hand-written **orchestrator** that selects and switches between multiple LLMs depending on the task, has direct access to a personal knowledge base (Obsidian + ChromaDB), and grows through pluggable skill modules.

Inspired by J.A.R.V.I.S. — a long-term project that also serves as a learning ground and portfolio for a DevOps/MLOps career.

## ✨ Vision

- 🧠 **Orchestrator core** — routes tasks to the right model/tool, not a single hard-wired LLM.
- 📚 **Knowledge-grounded** — direct access to an Obsidian vault and a ChromaDB vector store (RAG).
- 🔌 **Modular skills** — abilities added as modules, the core stays thin.
- 🏠 **Local-first & private** — runs locally (Ollama, ChromaDB); cloud models are optional.
- 🗣️ **Multi-interface** — terminal → voice → Telegram → desktop UI.

## 🗺️ Roadmap

| Phase | Goal | Status |
|-------|------|--------|
| 0 | Foundation: repo, Docker, CI, structure | 🚧 in progress |
| 1 | Terminal MVP — chat with knowledge base (RAG) | 🔜 |
| 2 | Voice (STT + TTS) | ⬜ |
| 3 | Telegram bot | ⬜ |
| 4 | Desktop UI with settings | ⬜ |
| 5 | Skills: reminders, calendar, smart home, job search | ⬜ |
| 6 | Physical body (robot) | ⬜ (long-term) |

## 🏗️ Architecture (high level)

```
Interfaces (CLI / voice / Telegram / UI)
        │
   Orchestrator  ──►  LLM Router  ──►  Ollama / cloud
        │
        ├─►  Memory   (Obsidian + ChromaDB, RAG)
        └─►  Modules  (pluggable skills)
```

## 🛠️ Tech stack

Python 3.13 · uv · Ollama · ChromaDB · Obsidian · Docker · GitHub Actions · pytest · ruff · mypy · pre-commit

## 🚀 Getting started

> ⚠️ Early development — Phase 0. Not functional yet.

```bash
# Install uv: https://docs.astral.sh/uv/
uv sync --extra dev
cp .env.example .env   # then edit values

# Run (placeholder for now)
uv run mourice
```

## 🧪 Development

```bash
uv run ruff check .
uv run ruff format .
uv run mypy
uv run pytest
```

## 📁 Repository layout

```
src/mourice/      # application code
  core/           # orchestrator
  llm/            # LLM providers & router
  memory/         # Obsidian + ChromaDB
  modules/        # pluggable skills
  interfaces/     # CLI, voice, telegram, ui adapters
tests/            # tests
docs/             # architecture & design docs
scripts/          # utilities (e.g. obsidian → chroma sync)
```

## 📄 License

MIT
