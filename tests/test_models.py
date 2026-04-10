"""Tests for pydantic models."""

from __future__ import annotations

from datetime import date

from gh_trends.models import TrendingRepo, TrendingSnapshot


def test_full_name(sample_repo: TrendingRepo) -> None:
    assert sample_repo.full_name == "NousResearch/hermes-agent"


def test_snapshot_serializes_to_json_compatible(sample_snapshot: TrendingSnapshot) -> None:
    payload = sample_snapshot.model_dump(mode="json")
    assert payload["fetched_on"] == "2026-04-10"
    assert payload["window"] == "weekly"
    assert payload["language"] == "python"
    assert isinstance(payload["repos"], list)
    assert payload["repos"][0]["stars_window"] == 19765


def test_snapshot_defaults() -> None:
    snap = TrendingSnapshot(fetched_on=date(2026, 1, 1), window="daily")
    assert snap.repos == []
    assert snap.language is None
