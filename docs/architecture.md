# Architecture

> High-level design of Mourice. The authoritative, evolving design notes live in the owner's Obsidian vault (in Russian); this file is the English summary for the public repo.

## Layers

```
Interfaces (CLI / voice / Telegram / UI)   ← adapters, core-agnostic
        │
   Orchestrator (agent loop)               ← the thin, hand-written core
        │
        ├─ LLM Router → Ollama / cloud      ← model is a swappable resource
        ├─ Memory      → Obsidian + ChromaDB (RAG)
        └─ Modules     → pluggable skills (tools)
```

## Principles

1. **Modularity first** — skills are modules with a clear contract; the core never learns their internals.
2. **Orchestrator, not monolith** — the core decides *what* to do and delegates the *how*.
3. **LLM is a swappable resource** — a router picks the model per task (speed / quality / privacy / cost).
4. **Local-first & private** — defaults to local (Ollama, ChromaDB, Obsidian on disk).
5. **Production hygiene from day one** — Docker, CI, tests, types, logging.
6. **Context is an asset** — the knowledge base is the long-term differentiator.
7. **Iterate, no big bang** — every phase ships a working product.
8. **Observability** — everything Mourice does is logged and measurable.
9. **Action safety** — more power ⇒ stricter confirmation for irreversible actions.

## Package layout

| Package | Responsibility |
|---------|----------------|
| `mourice.core` | Orchestrator / agent loop |
| `mourice.llm` | LLM providers + router |
| `mourice.memory` | Obsidian + ChromaDB access, RAG |
| `mourice.modules` | Pluggable skills exposed as tools |
| `mourice.interfaces` | CLI / voice / Telegram / UI adapters |

## Roadmap

See the [README](../README.md#-roadmap). Phases: foundation → terminal MVP → voice → Telegram → desktop UI → skills → robot body.
