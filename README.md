# Prompt Library for Claude Code

A self-building prompt library that mines your own Claude Code session history and surfaces the right past prompts based on what you're trying to do.

**No cloud. No setup. Just your own history, ranked by intent.**

---

## How it works

```
Your Claude Code sessions  →  mine.py  →  prompts.db  →  search.py + Fable 5  →  /prompts skill
```

1. `mine.py` scans every `.jsonl` session transcript in `~/.claude/projects/` and extracts user prompts into a local SQLite database, deduped by hash.
2. `search.py` runs a TF-IDF pre-filter (fast, no API cost) to get 20 candidates, then re-ranks them with **claude-fable-5** for intent-aware ordering.
3. The `/prompts` skill for Claude Code ties it together — type `/prompts review the funnel` and get a numbered dropdown of your closest past prompts, ready to reuse or edit.

---

## Requirements

- Python 3.11+
- Claude Code installed (`~/.claude/projects/` must exist with session transcripts)
- `anthropic` Python package (`pip install anthropic`) — only needed for Fable 5 re-ranking; falls back to TF-IDF if not set
- `ANTHROPIC_API_KEY` environment variable set

---

## Install

```bash
git clone https://github.com/alejandroclvi/prompt-library
cd prompt-library
./install.sh
```

`install.sh` copies the scripts to `~/.claude/prompt-library/` and the skill to `~/.claude/skills/prompts/SKILL.md`.

---

## Usage

### Mine your history

```bash
python3 ~/.claude/prompt-library/mine.py
# → Mined 3,200 messages, inserted 210 new → 1,268 total in library
```

### Search from the command line

```bash
python3 ~/.claude/prompt-library/search.py "review the funnel"
python3 ~/.claude/prompt-library/search.py "deploy to vercel" --no-ai   # TF-IDF only, faster
python3 ~/.claude/prompt-library/search.py "google ads" --project agency # filter by project
python3 ~/.claude/prompt-library/search.py "auth bug" --top 5 --json    # machine-readable
```

### Use the Claude Code skill

Once installed, type in any Claude Code session:

```
/prompts review the funnel
```

You get a numbered dropdown of your best past prompts for that intent. Pick a number, get the full text back.

---

## What gets filtered out

The miner skips:
- System messages, tool outputs, image blocks
- Very short responses ("yes", "ok", "keep going")
- Code dumps and JSON blobs (< 45% alpha characters)
- Anything that looks like an API key or secret
- Loop continuation messages and daemon tick prompts

What remains: real intent-carrying prompts — the things you actually asked Claude to do.

---

## Database schema

`~/.claude/prompt-library/prompts.db` (SQLite, stays local)

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER | Primary key |
| `text` | TEXT | Full prompt text |
| `project` | TEXT | Project slug from directory name |
| `session_id` | TEXT | Source `.jsonl` filename |
| `ts` | TEXT | Timestamp from transcript |
| `hash` | TEXT UNIQUE | SHA-256 prefix for dedup |
| `used_count` | INTEGER | Incremented when you pick a prompt |
| `last_suggested` | TEXT | Last time this prompt surfaced |
| `intent_tags` | TEXT | Reserved for future tagging |

---

## Claude Code skill

Copy `SKILL.md` to `~/.claude/skills/prompts/SKILL.md`. Claude Code will pick it up automatically. The skill:

- Runs `mine.py` once per session to refresh the library
- Calls `search.py` with your query
- Presents results as a numbered dropdown
- Handles pick responses (`"3"` or `"use 2"`) by echoing the full prompt text

---

## Fable 5 re-ranking

The `fable5_rank()` function in `search.py` sends the top 20 TF-IDF candidates (truncated to 200 chars each) to `claude-fable-5` with a minimal prompt asking for re-ordering by intent. It falls back to TF-IDF if the API call fails or the key is not set.

Cost is negligible — ~20 short strings per query, well under 1k input tokens.

---

## Why this exists

Claude Code doesn't have prompt history autocomplete. Every session starts cold. If you use it heavily across many projects, you end up retyping the same intent in slightly different words.

This tool builds that memory from your own history — not from training data, not from a cloud service — just from the transcripts already on your machine.

The library grows automatically. Every session makes it smarter.

---

## License

MIT
