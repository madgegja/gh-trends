"""Shared pytest fixtures."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import httpx
import pytest

from gh_trends.models import TrendingRepo, TrendingSnapshot

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def trending_html() -> str:
    return (FIXTURES / "trending_minimal.html").read_text(encoding="utf-8")


@pytest.fixture
def mock_client(trending_html: str) -> httpx.AsyncClient:
    """An httpx.AsyncClient that always returns the trending fixture."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=trending_html)

    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


@pytest.fixture
def sample_repo() -> TrendingRepo:
    return TrendingRepo(
        owner="NousResearch",
        name="hermes-agent",
        url="https://github.com/NousResearch/hermes-agent",
        description="The agent that grows with you",
        language="Python",
        stars_total=46193,
        stars_window=19765,
    )


@pytest.fixture
def sample_snapshot(sample_repo: TrendingRepo) -> TrendingSnapshot:
    return TrendingSnapshot(
        fetched_on=date(2026, 4, 10),
        window="weekly",
        language="python",
        repos=[sample_repo],
    )
