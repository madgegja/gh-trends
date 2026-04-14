"""Diff consecutive trending snapshots stored under digests/."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from .models import TrendingRepo, TrendingSnapshot, Window

DEFAULT_DIR = Path("digests")
_FILENAME_RE = re.compile(
    r"^(?P<date>\d{4}-\d{2}-\d{2})-(?P<scope>[a-zA-Z0-9_+-]+)-(?P<window>daily|weekly|monthly)\.json$"
)


def _scope(language: str | None) -> str:
    return language or "overall"


def load_snapshots(
    language: str | None = None,
    window: Window = "weekly",
    directory: Path | str = DEFAULT_DIR,
) -> list[TrendingSnapshot]:
    """Return snapshots for (scope, window) sorted by fetched_on ascending."""
    directory = Path(directory)
    target_scope = _scope(language)
    snapshots: list[TrendingSnapshot] = []
    for path in sorted(directory.glob(f"*-{target_scope}-{window}.json")):
        m = _FILENAME_RE.match(path.name)
        if not m or m["scope"] != target_scope or m["window"] != window:
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        snapshots.append(TrendingSnapshot.model_validate(data))
    snapshots.sort(key=lambda s: s.fetched_on)
    return snapshots


@dataclass(frozen=True)
class RepoChange:
    repo: TrendingRepo
    prev_rank: int
    curr_rank: int
    prev_stars_total: int
    curr_stars_total: int

    @property
    def rank_delta(self) -> int:
        """Positive = moved up (toward rank 1)."""
        return self.prev_rank - self.curr_rank

    @property
    def stars_delta(self) -> int:
        return self.curr_stars_total - self.prev_stars_total


@dataclass(frozen=True)
class SnapshotDiff:
    prev_date: date
    curr_date: date
    added: list[TrendingRepo]
    dropped: list[TrendingRepo]
    retained: list[RepoChange]

    @property
    def summary(self) -> dict[str, int]:
        return {
            "added": len(self.added),
            "dropped": len(self.dropped),
            "retained": len(self.retained),
        }


def diff_snapshots(prev: TrendingSnapshot, curr: TrendingSnapshot) -> SnapshotDiff:
    prev_index = {r.full_name: (i, r) for i, r in enumerate(prev.repos, start=1)}
    curr_index = {r.full_name: (i, r) for i, r in enumerate(curr.repos, start=1)}

    added = [r for name, (_, r) in curr_index.items() if name not in prev_index]
    dropped = [r for name, (_, r) in prev_index.items() if name not in curr_index]

    retained: list[RepoChange] = []
    for name, (curr_rank, curr_repo) in curr_index.items():
        if name not in prev_index:
            continue
        prev_rank, prev_repo = prev_index[name]
        retained.append(
            RepoChange(
                repo=curr_repo,
                prev_rank=prev_rank,
                curr_rank=curr_rank,
                prev_stars_total=prev_repo.stars_total,
                curr_stars_total=curr_repo.stars_total,
            )
        )
    retained.sort(key=lambda c: c.curr_rank)

    return SnapshotDiff(
        prev_date=prev.fetched_on,
        curr_date=curr.fetched_on,
        added=added,
        dropped=dropped,
        retained=retained,
    )


def timeline(snapshots: list[TrendingSnapshot]) -> list[SnapshotDiff]:
    """Pairwise diffs across consecutive snapshots."""
    return [diff_snapshots(a, b) for a, b in zip(snapshots, snapshots[1:])]
