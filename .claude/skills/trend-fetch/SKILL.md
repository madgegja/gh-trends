---
name: trend-fetch
description: Fetch GitHub trending repos and return a thematic digest. Use when the user asks what's trending, hot, popular this week, or wants a roundup of new OSS. Accepts an optional language and window. Examples - /trend-fetch, /trend-fetch python weekly, /trend-fetch rust daily.
argument-hint: [language] [daily|weekly|monthly]
context: fork
agent: trend-researcher
allowed-tools: WebFetch Bash
---

# Trend fetch

Run a GitHub trending digest and return a structured summary.

## Arguments

- `$0` — language filter (optional; e.g. `python`, `rust`, `typescript`, `go`). If empty or `all`, use the overall trending page.
- `$1` — window (optional; one of `daily`, `weekly`, `monthly`). Default: `daily`.

## Task

1. Resolve the URL:
   - If `$0` is empty or `all`: `https://github.com/trending?since=$1`
   - Otherwise: `https://github.com/trending/$0?since=$1`
   - If `$1` is empty, default `since=daily`.
2. Fetch the URL. If you also need overall context, fetch `https://github.com/trending` in parallel.
3. Apply the trend-researcher digest format defined in your system prompt.
4. Save the digest to `digests/${CLAUDE_SESSION_ID}-trend.md` (create the directory if needed) AND return it inline.

ARGUMENTS: $ARGUMENTS
