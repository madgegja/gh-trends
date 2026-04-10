"""MCP server exposing gh-trends as tools over stdio.

Wires the existing async fetcher into a FastMCP server so any MCP-compatible
client (Claude Desktop, Claude Code, IDE extensions, …) can call
`fetch_trending` as a tool.
"""

from __future__ import annotations

from typing import Any, Literal

from mcp.server.fastmcp import FastMCP

from .fetcher import fetch_trending as _fetch_trending

MCP_PORT = 8000

mcp = FastMCP(
    "gh-trends",
    instructions=(
        "Provides structured access to GitHub's trending repositories list. "
        "Use the fetch_trending tool to get a JSON snapshot of currently "
        "trending repos, optionally filtered by language and time window."
    ),
    host="127.0.0.1",
    port=MCP_PORT,
)


@mcp.tool()
async def fetch_trending(
    language: str | None = None,
    window: Literal["daily", "weekly", "monthly"] = "daily",
) -> dict[str, Any]:
    """Fetch GitHub's trending repositories list.

    Returns a parsed snapshot — the client (which has its own LLM) can do
    any further reasoning, summarization, or filtering on the structured data.

    Args:
        language: Optional language slug like "python", "rust", "go",
            "typescript". Omit for the overall trending page.
        window: Time window; one of "daily", "weekly", "monthly". Defaults
            to "daily".

    Returns:
        A snapshot dict with these fields:
        - fetched_on (ISO date string)
        - window (the requested window)
        - language (the requested language, or null)
        - repos: list of objects with owner, name, url, description,
          language, stars_total (int), stars_window (int)
    """
    snapshot = await _fetch_trending(language=language, window=window)
    return snapshot.model_dump(mode="json")


Transport = Literal["stdio", "sse", "streamable-http"]


def main(transport: Transport = "stdio") -> None:
    """Entrypoint used by `gh-trends serve`."""
    mcp.run(transport=transport)


if __name__ == "__main__":
    main()
