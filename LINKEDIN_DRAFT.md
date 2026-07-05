# LinkedIn Post Draft

---

I built a prompt library that learns from your own Claude Code sessions.

Every time you start a Claude Code session, you're basically starting from zero. No memory of how you asked something last week. No autocomplete. No "oh, I've done this before."

So I built one.

It's two Python scripts and a Claude Code skill:

→ mine.py scans your local session transcripts and indexes every real prompt you've typed (filters out junk, dedupes by hash)
→ search.py runs TF-IDF to get candidates, then sends them to Fable 5 for intent-aware re-ranking
→ /prompts skill ties it together — type `/prompts deploy to vercel` and get a numbered dropdown of your closest past prompts

The library builds itself from your own history. No cloud. No sync. Just SQLite on your machine.

After a few weeks of heavy Claude Code use, I had 1,000+ prompts indexed. The Fable 5 re-ranking is the key part — "check the funnel" and "where are users dropping off" rank together even though they share zero words.

Full code on GitHub: https://github.com/alejandroclvi/prompt-library

---

**Hashtags:** #claudecode #ai #developer #productivity #anthropic #opensource

---

**Notes for Manuel:**
- Add your GitHub link once you push the repo (alejandroclvi/prompt-library)
- Works best after a few weeks of usage — mention your actual prompt count if it's higher than 1,000
- Consider adding a screenshot of the /prompts dropdown in action as the first comment
