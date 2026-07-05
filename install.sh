#!/usr/bin/env bash
set -e

DEST="$HOME/.claude/prompt-library"
SKILL_DEST="$HOME/.claude/skills/prompts"

echo "Installing Prompt Library for Claude Code..."

# Create dirs
mkdir -p "$DEST"
mkdir -p "$SKILL_DEST"

# Copy scripts
cp mine.py "$DEST/mine.py"
cp search.py "$DEST/search.py"
chmod +x "$DEST/mine.py"
chmod +x "$DEST/search.py"

# Copy skill
cp SKILL.md "$SKILL_DEST/SKILL.md"

echo ""
echo "Done. Files installed to:"
echo "  $DEST/mine.py"
echo "  $DEST/search.py"
echo "  $SKILL_DEST/SKILL.md"
echo ""
echo "Next steps:"
echo "  1. Set ANTHROPIC_API_KEY in your environment (for Fable 5 re-ranking)"
echo "  2. Run: python3 $DEST/mine.py    ← builds your library from session history"
echo "  3. In any Claude Code session, type: /prompts <what you want to do>"
