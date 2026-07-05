#!/usr/bin/env python3.11
"""
Search the prompt library for semantically similar prompts.
Uses TF-IDF for fast candidate retrieval, then Fable 5 for smart ranking.

Usage:
  python3 search.py "query text" [--top N] [--project slug] [--no-ai]
"""
import os
import sys
import json
import sqlite3
import argparse
import math
import re
from collections import Counter

DB_PATH = os.path.expanduser("~/.claude/prompt-library/prompts.db")


def tokenize(text):
    return re.findall(r"[a-z0-9]+", text.lower())


def tfidf_scores(query, docs):
    """Return (index, score) pairs sorted by TF-IDF cosine similarity."""
    q_tokens = Counter(tokenize(query))
    if not q_tokens:
        return []

    N = len(docs)
    doc_tokens = [Counter(tokenize(d)) for d in docs]

    # IDF
    df = Counter()
    for dt in doc_tokens:
        for t in dt:
            df[t] += 1
    idf = {t: math.log((N + 1) / (df[t] + 1)) + 1 for t in df}

    def vec(counter):
        return {t: (1 + math.log(c)) * idf.get(t, 1) for t, c in counter.items()}

    q_vec = vec(q_tokens)
    q_norm = math.sqrt(sum(v**2 for v in q_vec.values())) or 1

    scores = []
    for i, dt in enumerate(doc_tokens):
        d_vec = vec(dt)
        d_norm = math.sqrt(sum(v**2 for v in d_vec.values())) or 1
        dot = sum(q_vec.get(t, 0) * d_vec.get(t, 0) for t in d_vec)
        scores.append((i, dot / (q_norm * d_norm)))

    return sorted(scores, key=lambda x: x[1], reverse=True)


def fable5_rank(query, candidates):
    """Re-rank candidates using claude-fable-5 for intent-aware scoring."""
    try:
        import anthropic
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return None
        client = anthropic.Anthropic(api_key=api_key)

        numbered = "\n".join(f"{i+1}. {c['text'][:200]}" for i, c in enumerate(candidates))
        prompt = f"""You are a prompt-library assistant. A user is starting to type a prompt and wants to see similar past prompts they've used.

Current partial prompt / intent:
"{query}"

Past prompts (numbered):
{numbered}

Return a JSON array of the numbers (1-based) of the 8 most relevant past prompts, ordered best-first.
Consider: same domain/project, similar action verb, similar goal. Ignore purely cosmetic wording differences.
Output ONLY the JSON array, e.g.: [3, 1, 7, 2, 5, 4, 8, 6]"""

        resp = client.messages.create(
            model="claude-fable-5",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = resp.content[0].text.strip()
        # extract JSON array
        match = re.search(r"\[[\d,\s]+\]", raw)
        if match:
            order = json.loads(match.group())
            return [candidates[i - 1] for i in order if 1 <= i <= len(candidates)]
    except Exception as e:
        pass
    return None


def search(query, top=10, project=None, use_ai=True):
    if not os.path.exists(DB_PATH):
        return []

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    where = "WHERE 1=1"
    params = []
    if project:
        where += " AND project LIKE ?"
        params.append(f"%{project}%")

    rows = conn.execute(
        f"SELECT id, text, project, ts FROM prompts {where} ORDER BY ts DESC LIMIT 5000",
        params,
    ).fetchall()
    conn.close()

    if not rows:
        return []

    docs = [r["text"] for r in rows]
    scored = tfidf_scores(query, docs)

    # take top 20 candidates for AI re-rank
    candidates = []
    for idx, score in scored[:20]:
        r = rows[idx]
        candidates.append({
            "id": r["id"],
            "text": r["text"],
            "project": r["project"],
            "ts": r["ts"],
            "score": score,
        })

    if use_ai and candidates:
        reranked = fable5_rank(query, candidates)
        if reranked:
            return reranked[:top]

    return candidates[:top]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("query", nargs="?", default="")
    ap.add_argument("--top", type=int, default=10)
    ap.add_argument("--project", default=None)
    ap.add_argument("--no-ai", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    query = args.query.strip()
    if not query:
        print("Usage: search.py \"query text\" [--top N] [--no-ai]")
        sys.exit(1)

    results = search(query, top=args.top, project=args.project, use_ai=not args.no_ai)

    if args.json:
        print(json.dumps(results, indent=2))
        return

    if not results:
        print("No matching prompts found. Run mine.py first.")
        return

    print(f"\n{'='*60}")
    print(f"Prompt library — top matches for: \"{query}\"")
    print(f"{'='*60}")
    for i, r in enumerate(results, 1):
        proj = r.get("project", "?").replace("-Users-manuel-", "").replace("-Users-manuel-Dev-", "")
        ts = (r.get("ts") or "")[:10]
        print(f"\n[{i}] {r['text'][:300]}")
        print(f"    ↳ {proj}  {ts}")
    print(f"\n{'='*60}")
    print(f"Pick a number to use that prompt, or just type your own.")


if __name__ == "__main__":
    main()
