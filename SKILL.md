---
name: prompts
description: Surface past prompts from your own Claude Code sessions that match what you're trying to do. Powered by TF-IDF pre-filter + Fable 5 intent re-ranking. Invoke when the user types `/prompts [partial text]` or asks to search their prompt history.
---

# Prompt Library — `/prompts`

Surface past prompts from your Claude Code session history that match what you're about to type. The library learns automatically from every session across all projects.

## Trigger

Invoke when the user types `/prompts [partial text]` or `/p [partial text]`.

Also trigger when the user asks:
- "show me similar prompts"
- "what prompts have I used for X"
- "search my prompt history"
- "autocomplete my prompt"
- "what did I ask about X before"

## Steps

1. **Mine (once per session, skip if already done):** Refresh the library with any new sessions:
   ```bash
   python3 ~/.claude/prompt-library/mine.py
   ```

2. **Search:** Run semantic search with the user's query. If no query text is given, ask what they're trying to do (one short question):
   ```bash
   python3 ~/.claude/prompt-library/search.py "QUERY_TEXT" --top 10
   ```

   The search uses TF-IDF for speed, then calls **claude-fable-5** to re-rank by intent. If AI ranking fails, TF-IDF results are shown.

3. **Present as a numbered dropdown.** Show the full prompt text and which project it came from. Format:

   ```
   ══════════════════════════════════════
   Prompt Library — matches for: "QUERY"
   ══════════════════════════════════════

   [1] <prompt text up to 300 chars>
       ↳ project-name  date

   [2] ...

   Pick a number to reuse that prompt, or just type your own.
   ```

4. **Handle picks:** If the user responds with a number (e.g. "3") or says "use 2" / "pick 4", echo back the full text of that prompt so they can send or edit it.

5. **Update usage count** (optional, fire-and-forget):
   ```bash
   python3 -c "import sqlite3,os; c=sqlite3.connect(os.path.expanduser('~/.claude/prompt-library/prompts.db')); c.execute('UPDATE prompts SET used_count=used_count+1, last_suggested=datetime(\"now\") WHERE id=?', (CHOSEN_ID,)); c.commit()"
   ```

## Flags for search.py

| Flag | Effect |
|---|---|
| `--top N` | Show N results (default 10) |
| `--project slug` | Filter by project name substring |
| `--no-ai` | Skip Fable 5 re-ranking (faster) |
| `--json` | Machine-readable output |

## Notes

- The library grows automatically from every Claude Code session across all projects
- Fable 5 understands **intent** — "check the funnel" and "where are users dropping off" rank together
- DB lives at `~/.claude/prompt-library/prompts.db` (stays local, never shared)
- If `ANTHROPIC_API_KEY` is not set, falls back to TF-IDF ranking only
