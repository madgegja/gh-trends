---
name: debug
description: Systematic debugging — root cause investigation before any fix
---

# Systematic Debugging

## The Iron Law

NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST.

If you haven't completed Phase 1, you cannot propose fixes.

## Phase 1: Root Cause Investigation

1. **Read error messages fully** — stack traces, line numbers, actual vs expected
2. **Reproduce consistently** — if not reproducible, gather more data, don't guess
3. **Check recent changes** — `git diff`, `git log --oneline -10`, new deps
4. **Trace data flow** — where does the bad value originate? Keep tracing upstream

## Phase 2: Pattern Analysis

- Find working examples in the same codebase
- Compare working vs broken — list every difference
- Check if the pattern worked before (git blame/log)

## Phase 3: Hypothesis and Testing

- Single hypothesis at a time
- SMALLEST possible change to test it
- ONE variable at a time
- Didn't work? Form NEW hypothesis. Don't pile fixes on top.

## Phase 4: Implementation

- If fix count >= 3: **STOP and question the architecture**
- After fix: run full test suite, not just the broken test
- Document what the root cause was in the commit message

## For This Project (async Python)

```bash
# Reproduce
uv run python -c "import asyncio; from gh_trends.fetcher import fetch_trending; asyncio.run(fetch_trending())"

# Trace with verbose logging
HTTPX_LOG_LEVEL=debug uv run gh-trends fetch

# Check parsing
uv run python -c "from selectolax.parser import HTMLParser; ..."
```
