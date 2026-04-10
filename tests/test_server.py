"""Tests for the FastMCP server module."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from gh_trends import server
from gh_trends.models import TrendingSnapshot


def test_mcp_instance_metadata() -> None:
    assert server.mcp.name == "gh-trends"


@pytest.mark.asyncio
async def test_mcp_lists_fetch_trending_tool() -> None:
    tools = await server.mcp.list_tools()
    names = [t.name for t in tools]
    assert "fetch_trending" in names
    tool = next(t for t in tools if t.name == "fetch_trending")
    props = tool.inputSchema.get("properties", {})
    assert "language" in props
    assert "window" in props


@pytest.mark.asyncio
async def test_fetch_trending_tool_returns_serialized_snapshot(
    sample_snapshot: TrendingSnapshot,
) -> None:
    async def fake_fetch(language=None, window="daily", *, client=None):
        return sample_snapshot

    with patch.object(server, "_fetch_trending", new=AsyncMock(side_effect=fake_fetch)):
        result = await server.fetch_trending(language="python", window="weekly")

    assert result["window"] == "weekly"
    assert result["language"] == "python"
    assert result["repos"][0]["owner"] == "NousResearch"
    assert result["repos"][0]["stars_window"] == 19765
