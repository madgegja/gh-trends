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
- Autoresearch: `/autoresearch`, `/autoresearch:fix`, `/autoresearch:security`, `/autoresearch:learn`
  - 자연어 트리거: "자동 개선", "auto improve", "autoresearch", "자율 루프", "밤새 개선", "코드 개선 루프", "자동 수정", "auto fix", "보안 감사", "security audit"
  - 벤치마크: `uv run pytest --tb=no -q`

## MCP server

`gh-trends serve` launches the MCP server exposing `fetch_trending(language, window) -> snapshot dict`.

### stdio (local MCP clients)

```bash
gh-trends serve            # default: stdio
```

Configure an MCP client (Claude Desktop, Claude Code, etc.):

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

### streamable-http (network / remote clients)

```bash
gh-trends serve -t streamable-http   # uvicorn on 0.0.0.0:8000/mcp
```

Public endpoint via Cloudflare Tunnel:

```
https://gh-trends.csy-p.com/mcp
https://mcp.csy-p.com/mcp
```

Configure a remote MCP client:

```json
{
  "mcpServers": {
    "gh-trends": {
      "type": "streamable-http",
      "url": "https://gh-trends.csy-p.com/mcp"
    }
  }
}
```

The server only exposes raw structured data — summarization is intentionally left to the calling client's own model. DNS rebinding protection is disabled because external auth is handled at the Cloudflare/Caddy edge.

## Infrastructure

All infra lives outside this repo (nothing to commit):

| Service | systemd unit | What it does |
|---|---|---|
| `gh-trends-mcp` | enabled | MCP HTTP on `:8000` (auto-restart on failure) |
| `cloudflared` | enabled | Cloudflare Tunnel `gh-trends` → `:8000` |
| `caddy` | enabled | HTTPS termination for `*.csy-p.duckdns.org` (local access) |

```
Internet → Cloudflare Edge (HTTPS) → Tunnel → 127.0.0.1:8000 (MCP)
LAN      → Caddy :443 (Let's Encrypt wildcard) → 127.0.0.1:8000
```

Domain `csy-p.com` is registered on Cloudflare. Duck DNS `csy-p.duckdns.org` handles dynamic IP for the local Caddy path. ISP (LG U+) blocks inbound ports, hence the Cloudflare Tunnel.

## Out of scope (for now)

- Persisting snapshots to a database. JSON/markdown only.
- Authentication with the GitHub API — public trending pages don't require it.
- Additional MCP tools beyond `fetch_trending` (e.g. `evaluate_repo`) — add only when a concrete client need appears.
