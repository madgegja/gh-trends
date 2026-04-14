"""Thematic clustering over trending repo descriptions.

Optional dependency: install with `uv pip install -e '.[analysis]'`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .models import TrendingRepo, TrendingSnapshot

_SKLEARN_HINT = (
    "scikit-learn is required for clustering. "
    "Install with: uv pip install -e '.[analysis]'"
)

# Generic words common across many repos that obscure cluster topics.
_STOPWORDS_EXTRA = {
    "github",
    "open",
    "source",
    "project",
    "repository",
    "repo",
    "code",
    "tool",
    "tools",
    "library",
    "framework",
    "official",
    "simple",
    "easy",
    "fast",
    "best",
    "free",
    "build",
    "building",
    "use",
    "using",
    "based",
    "powered",
    "support",
    "https",
    "com",
    "io",
}


@dataclass(frozen=True)
class Cluster:
    label: int
    top_terms: list[str]
    repos: list[TrendingRepo]

    @property
    def size(self) -> int:
        return len(self.repos)


@dataclass(frozen=True)
class ClusteringResult:
    clusters: list[Cluster]
    n_repos: int
    n_clusters: int


def gather_repos(snapshots: Iterable[TrendingSnapshot]) -> list[TrendingRepo]:
    """Deduplicate repos across snapshots by full_name, keeping the latest seen."""
    seen: dict[str, TrendingRepo] = {}
    for snap in snapshots:
        for repo in snap.repos:
            seen[repo.full_name] = repo
    return list(seen.values())


def _repo_text(repo: TrendingRepo) -> str:
    parts = [repo.name.replace("-", " ").replace("_", " ")]
    if repo.language:
        parts.append(repo.language)
    if repo.description:
        parts.append(repo.description)
    return " ".join(parts)


def cluster_repos(repos: list[TrendingRepo], n_clusters: int = 5) -> ClusteringResult:
    """Cluster repos via TF-IDF + KMeans on name/language/description."""
    if not repos:
        return ClusteringResult(clusters=[], n_repos=0, n_clusters=0)
    try:
        from sklearn.cluster import KMeans  # type: ignore
        from sklearn.feature_extraction.text import TfidfVectorizer  # type: ignore
    except ImportError as exc:  # pragma: no cover - exercised manually
        raise RuntimeError(_SKLEARN_HINT) from exc

    n_clusters = max(2, min(n_clusters, len(repos)))
    texts = [_repo_text(r) for r in repos]

    vectorizer = TfidfVectorizer(
        stop_words="english",
        max_features=2048,
        ngram_range=(1, 2),
        min_df=1,
    )
    matrix = vectorizer.fit_transform(texts)

    model = KMeans(n_clusters=n_clusters, random_state=42, n_init="auto")
    labels = model.fit_predict(matrix)

    terms = vectorizer.get_feature_names_out()
    centers = model.cluster_centers_

    clusters: list[Cluster] = []
    for label_id in range(n_clusters):
        members = [r for r, lbl in zip(repos, labels) if lbl == label_id]
        if not members:
            continue
        top_idx = centers[label_id].argsort()[::-1][:6]
        top_terms = [
            t for t in (terms[i] for i in top_idx) if t.lower() not in _STOPWORDS_EXTRA
        ][:5]
        clusters.append(Cluster(label=label_id, top_terms=top_terms, repos=members))

    clusters.sort(key=lambda c: c.size, reverse=True)
    return ClusteringResult(
        clusters=clusters, n_repos=len(repos), n_clusters=len(clusters)
    )
