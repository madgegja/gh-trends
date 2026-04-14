"""Tests for thematic clustering."""

from __future__ import annotations

from datetime import date

import pytest

from gh_trends.clusterer import cluster_repos, gather_repos
from gh_trends.models import TrendingRepo, TrendingSnapshot

sklearn = pytest.importorskip("sklearn")


def _repo(name: str, desc: str, lang: str = "Python", stars: int = 100) -> TrendingRepo:
    return TrendingRepo(
        owner="acme",
        name=name,
        url=f"https://github.com/acme/{name}",
        description=desc,
        language=lang,
        stars_total=stars,
    )


def test_gather_repos_dedupes_by_full_name() -> None:
    r_old = _repo("a", "old", stars=10)
    r_new = _repo("a", "new", stars=20)
    snaps = [
        TrendingSnapshot(fetched_on=date(2026, 4, 10), window="weekly", repos=[r_old]),
        TrendingSnapshot(fetched_on=date(2026, 4, 11), window="weekly", repos=[r_new]),
    ]
    result = gather_repos(snaps)
    assert len(result) == 1
    assert result[0].stars_total == 20  # latest wins


def test_cluster_repos_groups_similar_descriptions() -> None:
    repos = [
        _repo("agent-one", "AI agent framework for autonomous task execution"),
        _repo("agent-two", "Multi-agent orchestration with LLM tool calling"),
        _repo("agent-three", "Build AI agents with memory and planning"),
        _repo("vision-one", "Computer vision library for object detection"),
        _repo("vision-two", "Image segmentation and detection toolkit"),
        _repo("vision-three", "Real-time object tracking with deep learning"),
    ]
    result = cluster_repos(repos, n_clusters=2)
    assert result.n_repos == 6
    assert result.n_clusters == 2

    assert sum(c.size for c in result.clusters) == 6
    assert all(c.size > 0 for c in result.clusters)

    for c in result.clusters:
        names = {r.name for r in c.repos}
        is_agents = all(n.startswith("agent") for n in names)
        is_vision = all(n.startswith("vision") for n in names)
        assert is_agents or is_vision, f"cluster mixed themes: {names}"


def test_cluster_repos_handles_empty_input() -> None:
    result = cluster_repos([], n_clusters=3)
    assert result.n_repos == 0
    assert result.n_clusters == 0
    assert result.clusters == []
