#!/usr/bin/env python3.11
"""
Mine Claude Code session transcripts for user prompts.
Builds ~/.claude/prompt-library/prompts.db
"""
import json
import os
import sqlite3
import hashlib
import glob
import sys
from datetime import datetime

DB_PATH = os.path.expanduser("~/.claude/prompt-library/prompts.db")
PROJECTS_DIR = os.path.expanduser("~/.claude/projects")

MIN_LEN = 30  # skip very short messages
MAX_LEN = 4000  # skip walls of text (pasted code etc)

SKIP_PREFIXES = [
    "Manuel's instruction:", "## ", "# ", "IMPORTANT:", "You are ",
    "What you remember", "Recent conversation", "A background task",
    "Standing scan:", "Check the background", "Below are NEW inbox",
    "Run ONE ", "Route Manuel", "You manage Manuel", "Run the ",
    "Tick at ", "COS tick", "Closer tick", "Run your ",
    "Continue the ", "Continue gate", "Base directory for this skill",
    "continue with the /goal", "wake again",
    "[Image:", "[Image #",
]

SKIP_PATTERNS = [
    "<command-", "<local-command-", "<system-reminder", "loop</command",
    "/loop ", "command-message", "command-name", "command-args",
    "<task-notification>", "standing orders", "triage each",
    "Run ONE Closer", "Run ONE COS", "background daemon",
    "Below are NEW", "inbox emails as JSON",
    # API key patterns
    "api_key=", "apikey=", "api key:", "API_KEY=",
    "re_", "sk-", "_key:", "token:", "secret:",
    # Image and file dump patterns
    "[Image #", "[Image:", "source: /Users/",
    # Continuation/loop patterns
    "keep going", "continue the /goal", "in /loop",
    "wake every", "wake again",
]

# Short phrases that are not useful prompts
SKIP_EXACT = {
    "yes", "no", "ok", "okay", "sure", "go", "done",
    "yes that's the /goal", "that's the /goal", "keep going",
}


def init_db(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS prompts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            project TEXT,
            session_id TEXT,
            ts TEXT,
            hash TEXT UNIQUE,
            used_count INTEGER DEFAULT 0,
            last_suggested TEXT,
            intent_tags TEXT
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_hash ON prompts(hash)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_project ON prompts(project)")
    conn.commit()


def extract_text(content):
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
            elif isinstance(block, str):
                parts.append(block)
        return " ".join(parts).strip()
    return ""


def is_junk(text):
    if len(text) < MIN_LEN or len(text) > MAX_LEN:
        return True
    stripped = text.strip().lower()
    if stripped in SKIP_EXACT:
        return True
    for pfx in SKIP_PREFIXES:
        if text.startswith(pfx) or text.lower().startswith(pfx.lower()):
            return True
    for pat in SKIP_PATTERNS:
        if pat.lower() in text.lower():
            return True
    # skip if mostly non-alpha (code dumps, json, etc)
    alpha = sum(c.isalpha() or c.isspace() for c in text)
    if alpha / max(len(text), 1) < 0.45:
        return True
    # skip if looks like an API key line (short + contains hex/token)
    if len(text) < 80 and ("=" in text or ":" in text):
        import re
        if re.search(r'[a-z0-9_]{20,}', text.lower()):
            words = text.split()
            if len(words) <= 3:
                return True
    return False


def mine_file(path, project):
    prompts = []
    session_id = os.path.basename(path).replace(".jsonl", "")
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                if obj.get("type") != "user":
                    continue
                msg = obj.get("message", {})
                if msg.get("role") != "user":
                    continue
                text = extract_text(msg.get("content", ""))
                if is_junk(text):
                    continue
                ts = obj.get("timestamp", "")
                h = hashlib.sha256(text.encode()).hexdigest()[:16]
                prompts.append((text, project, session_id, ts, h))
    except Exception as e:
        pass
    return prompts


def run(verbose=False):
    conn = sqlite3.connect(DB_PATH)
    init_db(conn)

    all_jsonl = glob.glob(os.path.join(PROJECTS_DIR, "**", "*.jsonl"), recursive=True)
    inserted = 0
    seen = 0

    for path in all_jsonl:
        parts = path.split(os.sep)
        project = parts[-2] if len(parts) >= 2 else "unknown"
        rows = mine_file(path, project)
        for (text, proj, sid, ts, h) in rows:
            seen += 1
            try:
                conn.execute(
                    "INSERT OR IGNORE INTO prompts (text, project, session_id, ts, hash) VALUES (?,?,?,?,?)",
                    (text, proj, sid, ts, h)
                )
                if conn.execute("SELECT changes()").fetchone()[0]:
                    inserted += 1
            except Exception:
                pass

    conn.commit()
    total = conn.execute("SELECT COUNT(*) FROM prompts").fetchone()[0]
    conn.close()

    print(f"Mined {seen} messages, inserted {inserted} new → {total} total in library")
    return total


if __name__ == "__main__":
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    run(verbose)
