# Troubleshooting

Real issues encountered during development, with root causes and fixes. Useful if you hit the same thing.

---

## Voice / XTTS

### Corrupted model checkpoint

```
RuntimeError: PytorchStreamReader failed reading file data/4: invalid header or archive is corrupted
```

The XTTS v2 model download was interrupted. The cache holds a partial `model.pth`.

**Fix:** delete the cache and re-download (~1.87 GB):

```powershell
Remove-Item "$env:LOCALAPPDATA\tts\tts_models--multilingual--multi-dataset--xtts_v2" -Recurse -Force
.venv-xtts\Scripts\python.exe -c "from TTS.api import TTS; TTS('tts_models/multilingual/multi-dataset/xtts_v2')"
```

---

### XTTS subprocess fails silently (exit code 1, no details)

Before PR #56, `capture_output=True` in `_default_runner` swallowed stderr entirely. You'd see:

```
subprocess.CalledProcessError: Command [...] returned non-zero exit status 1.
```

**Fix (PR #56):** `_default_runner` now captures stderr and raises `RuntimeError` with the full output, so the real cause is visible in logs.

---

### XTTS script not found (relative path)

```
FileNotFoundError: [Errno 2] No such file or directory: 'scripts/xtts_speak.py'
```

`MOURICE_XTTS_SCRIPT` defaults to a relative path. When the Telegram bot is started from a directory other than the repo root, the path resolves incorrectly.

**Fix (PR #56):** `factory.py` now resolves relative `xtts_script` paths to absolute, anchored at the repo root. Or set an absolute path in `.env`:

```
MOURICE_XTTS_SCRIPT=C:/path/to/Mourice/scripts/xtts_speak.py
```

---

### XTTS dependency conflicts

```
ImportError: cannot import name 'isin_mps_friendly' from 'transformers'
# or
ImportError: torchcodec
```

coqui-tts is incompatible with `transformers>=5` and `torch>=2.9`.

**Fix:** pin both in `.venv-xtts`:

```powershell
.venv-xtts\Scripts\pip install "transformers>=4.57,<5" "torch<2.9" --upgrade
```

---

## Telegram bot

### Voice and file extras missing after `uv sync`

Running `uv sync` without extras removes `aiogram`, `faster-whisper`, `piper-tts`, and other optional deps.

**Fix:** always sync with all extras:

```powershell
uv sync --extra dev --extra voice --extra telegram
```

---

### Mourice denies having file/shell tools

Mourice says "I don't have access to your files" despite the tools being registered.

**Root cause:** the system prompt didn't mention the tools explicitly — the LLM fell back on its training where it has no PC access.

**Fix (PR #54):** the system prompt now explicitly lists every tool with its name and purpose.

---

### Mourice denies being able to send voice messages

Mourice responds "I can't send voice messages" — while simultaneously sending one.

**Root cause 1:** the system prompt said "if voice is enabled" without confirming it actually is enabled right now.  
**Root cause 2:** the bot sent both a text message and an audio file, creating a contradiction.

**Fix (PR #57, #58):**
- `build_system_prompt(voice_enabled=True)` now injects an explicit line: "voice is ON right now, your text IS being spoken."
- When voice synthesis succeeds, the text message is skipped entirely.

---

### WriteFileTool overwrites binary files with text

When asked to "send a file to Telegram," the LLM had no send tool and fell back on `write_file`, replacing a `.mp3` with 92 bytes of text.

**Fix (PR #59):**
- `WriteFileTool` now blocks writes to binary extensions (`.mp3`, `.wav`, `.jpg`, `.png`, `.exe`, `.zip`, and ~25 more) and returns an error.
- `SendFileTool` added: Mourice can now call `send_file(path)` to deliver a file as a Telegram attachment.

---

### Mourice doesn't call tools on its own (qwen2.5:14b)

qwen2.5:14b is reluctant to invoke tools without being explicitly told to do so.

**Workaround:** phrase requests with action verbs — "look at the Downloads folder" rather than "do I have anything in Downloads?"

**Fix:** `ModelRouter` now routes file/folder/shell requests to `llama3.1:8b`, which follows tool-calling instructions much more reliably. Set `MOURICE_TOOL_MODEL=llama3.1:8b` in `.env`.

---

## General

### History not persisting across restarts

Conversation history was lost on every bot restart.

**Fix (PR #55):** `Orchestrator` now loads history from `data/conversation.json` on startup and saves after every turn. Configure with `MOURICE_HISTORY_FILE` (set to `""` to disable).
