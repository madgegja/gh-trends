"""Tests for the async GitHub trending fetcher."""

from __future__ import annotations

import httpx
import pytest

from gh_trends.fetcher import _build_url, _parse_int, fetch_trending


def test_parse_int_handles_commas_and_garbage() -> None:
    assert _parse_int("12,345") == 12345
    assert _parse_int("  789  ") == 789
    assert _parse_int("not a number") == 0
    assert _parse_int("") == 0


def test_build_url_overall_default() -> None:
    assert _build_url(None, "daily") == "https://github.com/trending?since=daily"
    assert _build_url("all", "weekly") == "https://github.com/trending?since=weekly"


def test_build_url_with_language() -> None:
    assert _build_url("python", "weekly") == "https://github.com/trending/python?since=weekly"
    assert _build_url("rust", "monthly") == "https://github.com/trending/rust?since=monthly"


@pytest.mark.asyncio
async def test_fetch_trending_parses_fixture(mock_client: httpx.AsyncClient) -> None:
    snapshot = await fetch_trending(language="python", window="weekly", client=mock_client)

    assert snapshot.window == "weekly"
    assert snapshot.language == "python"
    assert len(snapshot.repos) == 3

    alpha = snapshot.repos[0]
    assert alpha.full_name == "test-owner/alpha-repo"
    assert alpha.language == "Python"
    assert alpha.stars_total == 12345
    assert alpha.stars_window == 789
    assert alpha.description == "A first fake trending repo for unit tests."
    assert alpha.url == "https://github.com/test-owner/alpha-repo"

    beta = snapshot.repos[1]
    assert beta.full_name == "another-owner/beta-repo"
    assert beta.language is None
    assert beta.stars_total == 42
    assert beta.stars_window == 7

    gamma = snapshot.repos[2]
    assert gamma.full_name == "third/gamma"
    assert gamma.language == "Rust"
    assert gamma.description is None


@pytest.mark.asyncio
async def test_fetch_trending_caller_owns_client_lifetime(mock_client: httpx.AsyncClient) -> None:
    """When the caller passes a client, fetch_trending must NOT close it."""
    await fetch_trending(client=mock_client)
    # second call on the same client should still work
    snapshot = await fetch_trending(client=mock_client)
    assert len(snapshot.repos) == 3
    await mock_client.aclose()
