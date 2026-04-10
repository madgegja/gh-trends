# gh-trends

A Python tool that fetches GitHub trending repositories, parses them into typed models, and produces LLM-assisted thematic digests. The project itself rides the 2026 wave around AI agents, Claude Code skills, and MCP-style tooling.

## Stack

- **Runtime:** Python 3.11+
- **Packaging:** `uv` + `pyproject.toml` (hatchling backend)
- **HTTP:** `httpx` (async)
- **Parsing:** `selectolax` (fast Lexbor-based HTML parser)
- **Models:** `pydantic` v2
- **CLI:** `typer` + `rich`
- **LLM:** `anthropic` SDK, default model `claude-opus-4-6`

## Layout

```
src/gh_trends/
  __init__.py
  models.py     # TrendingRepo, TrendingSnapshot, Window
  fetcher.py    # async fetch_trending(language, window)
  cli.py        # `gh-trends fetch ...`, `gh-trends version`
digests/        # generated markdown digests (gitignored except .gitkeep)
.claude/
  agents/       # trend-researcher, repo-deep-dive
  skills/       # trend-fetch, repo-eval, daily-digest
```

## Conventions

- All HTTP code is async. The CLI wraps with `asyncio.run` only at the entry point.
- Pydantic v2 syntax (`BaseModel`, `Field`, `model_dump`). Don't fall back to v1 patterns.
- Use the `trend-researcher` subagent for any "what's trending" question — don't WebFetch from the main loop.
- Use the `repo-deep-dive` subagent for any single-repo evaluation.
- Slash commands: `/trend-fetch [lang] [window]`, `/repo-eval owner/repo`, `/daily-digest [extra-lang]`.

## Out of scope (for now)

- MCP server export (planned, not built).
- Persisting snapshots to a database. JSON/markdown only.
- Authentication with the GitHub API — public trending pages don't require it.
