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
  models.py      # TrendingRepo, TrendingSnapshot, Window
  fetcher.py     # async fetch_trending(language, window)
  summarizer.py  # Anthropic-backed thematic digest (ko/en)
  server.py      # FastMCP stdio server exposing fetch_trending
  cli.py         # `gh-trends fetch | digest | serve | version`
digests/         # generated markdown digests (gitignored except .gitkeep)
.claude/
  agents/        # trend-researcher, repo-deep-dive
  skills/        # trend-fetch, repo-eval, daily-digest
```

## Conventions

- All HTTP code is async. The CLI wraps with `asyncio.run` only at the entry point.
- Pydantic v2 syntax (`BaseModel`, `Field`, `model_dump`). Don't fall back to v1 patterns.
- Use the `trend-researcher` subagent for any "what's trending" question — don't WebFetch from the main loop.
- Use the `repo-deep-dive` subagent for any single-repo evaluation.
- Slash commands: `/trend-fetch [lang] [window]`, `/repo-eval owner/repo`, `/daily-digest [extra-lang]`.

## MCP server

`gh-trends serve` launches a stdio MCP server (`mcp.server.fastmcp.FastMCP`) that exposes `fetch_trending(language, window) -> snapshot dict`. Configure an MCP client (Claude Desktop, Claude Code, etc.) like:

```json
{
  "mcpServers": {
    "gh-trends": {
      "command": "uv",
      "args": ["--directory", "/home/jooyu/claude-projects", "run", "gh-trends", "serve"]
    }
  }
}
```

The server only exposes raw structured data — summarization is intentionally left to the calling client's own model.

## Out of scope (for now)

- Persisting snapshots to a database. JSON/markdown only.
- Authentication with the GitHub API — public trending pages don't require it.
- Additional MCP tools beyond `fetch_trending` (e.g. `evaluate_repo`) — add only when a concrete client need appears.
