# Mourice

> A personal AI assistant orchestrator — self-hosted, multi-LLM, grounded in a personal knowledge base.

[![CI](https://github.com/Shpuntyara/Mourice/actions/workflows/ci.yml/badge.svg)](https://github.com/Shpuntyara/Mourice/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.13-blue)
![License](https://img.shields.io/badge/license-MIT-green)

Mourice is **not** just an LLM wrapper. It's a hand-written **orchestrator** that selects and switches between multiple local LLMs depending on the task, has direct access to a personal knowledge base (Obsidian + ChromaDB), and grows through pluggable skill modules.

Inspired by J.A.R.V.I.S. — a long-term project that also serves as a learning ground and portfolio for a DevOps/MLOps career.

## ✨ Features

- 🧠 **Orchestrator core** — a custom agent loop with function-calling tools.
- 📚 **Knowledge-grounded (RAG)** — semantic search over an Obsidian vault via ChromaDB.
- 🌍 **Multilingual** — local `bge-m3` embeddings; strong on Russian, Polish, English.
- 🔌 **Tools** — `search_memory`, `read_note`, `write_note`, plus full-PC system tools (`list_dir`, `read_file`, `write_file`, `delete_path`, `run_command`).
- 🛡️ **Action safety** — reading/creating is free; delete/overwrite/shell ask for confirmation (in the terminal).
- 🗣️ **Personality** — friendly companion, honest ("I don't know" + reason), language-switchable.
- 🎙️ **Voice (Phase 2)** — talk to Mourice: local STT (faster-whisper) + TTS (Piper).
- 💬 **Telegram (Phase 3)** — single-owner bot: chat by text or voice message from your phone.
- 🏠 **Local-first & private** — runs entirely on local hardware via Ollama; no cloud.

## 🚀 Getting started

### Prerequisites
- [uv](https://docs.astral.sh/uv/)
- [Ollama](https://ollama.com/) running locally with:
  ```bash
  ollama pull qwen2.5:14b   # chat model
  ollama pull bge-m3        # multilingual embeddings
  ```

### Install & configure
```bash
uv sync --extra dev
cp .env.example .env        # then edit paths/models
```

`.env` (key settings):
```
MOURICE_OLLAMA_HOST=http://localhost:11434
MOURICE_DEFAULT_MODEL=qwen2.5:14b
MOURICE_EMBEDDING_MODEL=bge-m3
MOURICE_OBSIDIAN_VAULT=/path/to/your/Obsidian Vault
MOURICE_CHROMA_DIR=/path/to/ChromaDB
```

### Use it
```bash
uv run mourice sync     # index your vault into ChromaDB (--reset to rebuild)
uv run mourice chat     # talk to Mourice (commands: /lang ru|pl|en, /reset, /quit)
uv run mourice eval     # retrieval relevance hit-rate
uv run mourice          # status banner
```

Ask things like *"what did I write about my first prototype?"* — Mourice will search your notes and answer from them.

### Voice (optional)
```bash
uv sync --extra voice                       # audio + STT + TTS deps
# download a Piper voice (example: Russian), then point .env to its .onnx:
python -m piper.download_voices ru_RU-dmitri-medium --download-dir ./voices
# set MOURICE_PIPER_VOICE=./voices/ru_RU-dmitri-medium.onnx
uv run mourice voice                         # push-to-talk: Enter to talk, q to quit
```
STT (faster-whisper) runs on CPU by default; the Whisper model downloads on first use.

### Telegram (optional)
Talk to Mourice from your phone. The bot is **single-owner** — only your Telegram
account may use it, since Mourice can write to your vault.
```bash
uv sync --extra telegram                     # aiogram
# Get a token from @BotFather and your numeric id from @userinfobot, then set:
# MOURICE_TELEGRAM_TOKEN=123456:ABC...
# MOURICE_TELEGRAM_OWNER_ID=123456789
uv run mourice telegram                       # long-polling; Ctrl-C to stop
```
Send text or a voice message (voice notes are transcribed with the same
faster-whisper STT — needs the `voice` extra too). Commands: `/reset`, `/lang ru|pl|en`,
`/help`. Set `MOURICE_TELEGRAM_VOICE_REPLY=true` to also get spoken replies (needs the
`voice` extra and a configured TTS engine).

## 🗺️ Roadmap

| Phase | Goal | Status |
|-------|------|--------|
| 0 | Foundation: repo, Docker, CI | ✅ done |
| 1 | Terminal MVP — chat grounded in the knowledge base (RAG) | ✅ done |
| 2 | Voice (STT + TTS) | ✅ done |
| 3 | Telegram bot | ✅ done |
| 4 | Desktop UI with settings | ⬜ |
| 5 | Skills: reminders, calendar, smart home, job search | ⬜ |
| 6 | Physical body (robot) | ⬜ (long-term) |

## 🏗️ Architecture

```
Interfaces (CLI / voice / Telegram / UI)
        │
   Orchestrator (agent loop)
        ├─ LLM Router → Ollama (qwen2.5, qwen2.5-coder, …)
        ├─ Memory     → Obsidian + ChromaDB (RAG, bge-m3)
        └─ Modules    → search_memory / read_note / write_note
```

| Package | Responsibility |
|---------|----------------|
| `mourice.core` | Orchestrator, system prompt, context builder |
| `mourice.llm` | LLM provider (Ollama) + model router |
| `mourice.memory` | Vault reader, chunking, embeddings, ChromaDB, sync, search |
| `mourice.modules` | Tools (skills) + registry |
| `mourice.interfaces` | Terminal REPL (more to come) |

## 🛠️ Tech stack

Python 3.13 · uv · Ollama · ChromaDB · Obsidian · Docker · GitHub Actions · pytest · ruff · mypy · pre-commit

## 🧪 Development

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run pytest
```

Workflow: branch per issue → PR → green CI → squash merge.

## 📄 License

MIT
