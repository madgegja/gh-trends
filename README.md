# gh-trends

Fetch, analyze, and digest GitHub trending repositories — from the command line, as an MCP server, or via a public API.

## Quick start

```bash
# Install
uv sync

# Fetch today's trending Python repos
uv run gh-trends fetch -l python -w daily

# AI-summarized digest (requires ANTHROPIC_API_KEY)
export ANTHROPIC_API_KEY=sk-ant-...
uv run gh-trends digest -l python -w weekly --save
```

## CLI commands

| Command | Description |
|---|---|
| `gh-trends fetch` | Fetch trending repos as a rich table |
| `gh-trends digest` | Claude-summarized thematic digest (ko/en) |
| `gh-trends serve` | Launch MCP server (stdio) |
| `gh-trends serve -t streamable-http` | Launch MCP server (HTTP on :8000) |
| `gh-trends version` | Print version |

### fetch options

```
-l, --language    Language slug (python, rust, go, ...). Omit for overall.
-w, --window      daily | weekly | monthly (default: daily)
-n, --limit       Number of repos to display (default: 15)
```

### digest options

```
-l, --language    Language slug
-w, --window      daily | weekly | monthly (default: weekly)
--lang            Output language: ko | en (default: ko)
--model           Anthropic model (default: claude-opus-4-6)
--save            Persist to digests/<date>-<scope>-<window>.md
```

## MCP server

Exposes `fetch_trending(language, window)` as a tool for any MCP-compatible client.

### Local (stdio)

```json
{
  "mcpServers": {
    "gh-trends": {
      "command": "uv",
      "args": ["--directory", "/path/to/gh-trends", "run", "gh-trends", "serve"]
    }
  }
}
```

### Remote (streamable-http)

Public endpoint:

```
https://gh-trends.csy-p.com/mcp
```

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

## Stack

- **Python 3.11+** with `uv` + `pyproject.toml`
- **httpx** — async HTTP client
- **selectolax** — fast HTML parsing (Lexbor)
- **pydantic v2** — typed data models
- **typer + rich** — CLI and output formatting
- **anthropic SDK** — LLM-powered digest (`claude-opus-4-6`)
- **mcp (FastMCP)** — Model Context Protocol server

## Development

```bash
# Install with dev dependencies
uv sync --extra dev

# Lint
uv run ruff check src tests

# Test (19 tests, no network/API calls)
uv run pytest -v
```

## License

MIT
