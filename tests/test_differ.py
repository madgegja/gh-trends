"""Tests for the snapshot differ."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from gh_trends.differ import diff_snapshots, load_snapshots, timeline
from gh_trends.models import TrendingRepo, TrendingSnapshot


def _repo(name: str, stars: int = 100) -> TrendingRepo:
    return TrendingRepo(
        owner="acme",
        name=name,
        url=f"https://github.com/acme/{name}",
        stars_total=stars,
        stars_window=10,
    )


def _write(directory: Path, snap: TrendingSnapshot, scope: str) -> None:
    path = directory / f"{snap.fetched_on}-{scope}-{snap.window}.json"
    path.write_text(
        json.dumps(snap.model_dump(mode="json"), ensure_ascii=False), encoding="utf-8"
    )


def test_diff_detects_added_dropped_and_rank_changes() -> None:
    prev = TrendingSnapshot(
        fetched_on=date(2026, 4, 13),
        window="weekly",
        repos=[_repo("alpha", 100), _repo("beta", 200), _repo("gamma", 300)],
    )
    curr = TrendingSnapshot(
        fetched_on=date(2026, 4, 14),
        window="weekly",
        repos=[_repo("beta", 250), _repo("alpha", 120), _repo("delta", 50)],
    )

    d = diff_snapshots(prev, curr)

    assert [r.name for r in d.added] == ["delta"]
    assert [r.name for r in d.dropped] == ["gamma"]
    assert d.summary == {"added": 1, "dropped": 1, "retained": 2}

    by_name = {c.repo.name: c for c in d.retained}
    assert by_name["beta"].rank_delta == 1  # 2 -> 1
    assert by_name["beta"].stars_delta == 50
    assert by_name["alpha"].rank_delta == -1  # 1 -> 2


def test_load_snapshots_filters_scope_and_window(tmp_path: Path) -> None:
    overall = TrendingSnapshot(
        fetched_on=date(2026, 4, 10), window="weekly", repos=[_repo("a")]
    )
    python = TrendingSnapshot(
        fetched_on=date(2026, 4, 10),
        window="weekly",
        language="python",
        repos=[_repo("b")],
    )
    daily_overall = TrendingSnapshot(
        fetched_on=date(2026, 4, 10), window="daily", repos=[_repo("c")]
    )

    _write(tmp_path, overall, "overall")
    _write(tmp_path, python, "python")
    _write(tmp_path, daily_overall, "overall")

    loaded = load_snapshots(language=None, window="weekly", directory=tmp_path)
    assert len(loaded) == 1
    assert loaded[0].repos[0].name == "a"

    loaded_py = load_snapshots(language="python", window="weekly", directory=tmp_path)
    assert len(loaded_py) == 1
    assert loaded_py[0].repos[0].name == "b"


def test_timeline_returns_pairwise_diffs(tmp_path: Path) -> None:
    snaps = [
        TrendingSnapshot(
            fetched_on=date(2026, 4, 10 + i), window="weekly", repos=[_repo(f"r{i}")]
        )
        for i in range(3)
    ]
    diffs = timeline(snaps)
    assert len(diffs) == 2
    assert diffs[0].prev_date == date(2026, 4, 10)
    assert diffs[1].curr_date == date(2026, 4, 12)
