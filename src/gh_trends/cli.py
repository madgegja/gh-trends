"""Typer CLI for gh-trends."""

from __future__ import annotations

import asyncio
import json as json_mod
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table

from .differ import diff_snapshots, load_snapshots, timeline
from .clusterer import cluster_repos, gather_repos
from .fetcher import fetch_trending
from .models import Window
from .summarizer import DEFAULT_MODEL, DigestLang, summarize

app = typer.Typer(help="Fetch and digest GitHub trending repositories.")
console = Console()


@app.command()
def fetch(
    language: Optional[str] = typer.Option(
        None, "--language", "-l", help="Language slug, e.g. python, rust, go. Omit for overall."
    ),
    window: Window = typer.Option("daily", "--window", "-w", help="daily | weekly | monthly"),
    limit: int = typer.Option(15, "--limit", "-n", help="How many repos to display."),
) -> None:
    """Fetch the current trending list and print it as a table."""
    snapshot = asyncio.run(fetch_trending(language=language, window=window))

    title = f"GitHub trending — {language or 'overall'} ({window}) — {snapshot.fetched_on}"
    table = Table(title=title)
    table.add_column("#", justify="right", style="dim")
    table.add_column("Repo", style="bold cyan")
    table.add_column("Lang")
    table.add_column("Stars", justify="right")
    table.add_column("Δ window", justify="right", style="green")
    table.add_column("Description", overflow="fold")

    for idx, repo in enumerate(snapshot.repos[:limit], start=1):
        table.add_row(
            str(idx),
            repo.full_name,
            repo.language or "—",
            f"{repo.stars_total:,}",
            f"+{repo.stars_window:,}",
            repo.description or "",
        )

    console.print(table)


@app.command()
def digest(
    language: Optional[str] = typer.Option(
        None, "--language", "-l", help="Language slug, e.g. python, rust. Omit for overall."
    ),
    window: Window = typer.Option("weekly", "--window", "-w", help="daily | weekly | monthly"),
    output_lang: DigestLang = typer.Option(
        "ko", "--lang", help="Digest language: ko or en"
    ),
    model: str = typer.Option(DEFAULT_MODEL, "--model", help="Model name for the proxy"),
    save: bool = typer.Option(False, "--save", help="Persist the digest under digests/"),
) -> None:
    """Fetch trending and produce a Claude-summarized thematic digest."""
    snapshot = asyncio.run(fetch_trending(language=language, window=window))
    text = summarize(snapshot, lang=output_lang, model=model)

    console.print(Markdown(text))

    if save:
        scope = language or "overall"
        path = Path("digests") / f"{snapshot.fetched_on}-{scope}-{window}.md"
        path.parent.mkdir(exist_ok=True)
        path.write_text(text + "\n", encoding="utf-8")
        console.print(f"\n[dim]Saved → {path}[/dim]")


@app.command()
def daily(
    extra_lang: Optional[str] = typer.Option(
        None, "--extra", "-e", help="Additional language besides overall + python."
    ),
) -> None:
    """Run the daily digest pipeline: fetch + optional LLM digest, saved to digests/.

    Always saves raw JSON snapshots. If the Claude proxy is available,
    also generates a markdown digest.
    """
    import httpx as _httpx
    from datetime import date

    today = date.today().isoformat()
    digests_dir = Path("digests")
    digests_dir.mkdir(exist_ok=True)

    scopes = [("overall", None), ("python", "python")]
    if extra_lang:
        scopes.append((extra_lang, extra_lang))

    snapshots = {}
    for label, lang in scopes:
        snap = asyncio.run(fetch_trending(language=lang, window="weekly"))
        snapshots[label] = snap
        json_path = digests_dir / f"{today}-{label}-weekly.json"
        json_path.write_text(
            json_mod.dumps(snap.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        console.print(f"[dim]Saved snapshot → {json_path}[/dim]")

    # Attempt LLM digest via proxy (graceful skip if proxy is down)
    try:
        _httpx.get("http://127.0.0.1:3456/v1/models", timeout=3.0)
        proxy_up = True
    except Exception:
        proxy_up = False

    if proxy_up:
        parts = [f"# GitHub trending digest — {today}\n"]
        for label, snap in snapshots.items():
            text = summarize(snap, lang="ko")
            parts.append(text)
            parts.append("")
        digest_text = "\n".join(parts)
        md_path = digests_dir / f"{today}.md"
        md_path.write_text(digest_text + "\n", encoding="utf-8")
        console.print(f"[bold green]Digest saved → {md_path}[/bold green]")
    else:
        console.print("[yellow]Proxy not running — skipped LLM digest, JSON snapshots saved.[/yellow]")


@app.command()
def serve(
    transport: str = typer.Option(
        "stdio",
        "--transport",
        "-t",
        help="stdio (for MCP clients) | streamable-http (network, port 8000)",
    ),
) -> None:
    """Launch the MCP server. Use --transport streamable-http for network access."""
    from .server import main as serve_main

    serve_main(transport=transport)


@app.command()
def diff(
    language: Optional[str] = typer.Option(
        None, "--language", "-l", help="Language slug; omit for overall."
    ),
    window: Window = typer.Option("weekly", "--window", "-w", help="daily | weekly | monthly"),
    directory: Path = typer.Option(
        Path("digests"), "--dir", "-d", help="Directory containing snapshot JSON files."
    ),
    limit: int = typer.Option(10, "--limit", "-n", help="Rows shown in the retained table."),
    full: bool = typer.Option(False, "--full", help="Print the full timeline, not just the latest pair."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    """Compare consecutive snapshots and show added / dropped / rank-changed repos."""
    snapshots = load_snapshots(language=language, window=window, directory=directory)
    if len(snapshots) < 2:
        console.print(
            f"[yellow]Need at least 2 snapshots for {language or 'overall'}/{window} "
            f"in {directory} (found {len(snapshots)}).[/yellow]"
        )
        raise typer.Exit(code=1)

    diffs = timeline(snapshots) if full else [diff_snapshots(snapshots[-2], snapshots[-1])]

    if json_output:
        payload = [
            {
                "prev_date": d.prev_date.isoformat(),
                "curr_date": d.curr_date.isoformat(),
                "summary": d.summary,
                "added": [r.model_dump(mode="json") for r in d.added],
                "dropped": [r.model_dump(mode="json") for r in d.dropped],
                "retained": [
                    {
                        "repo": c.repo.full_name,
                        "prev_rank": c.prev_rank,
                        "curr_rank": c.curr_rank,
                        "rank_delta": c.rank_delta,
                        "stars_delta": c.stars_delta,
                    }
                    for c in d.retained
                ],
            }
            for d in diffs
        ]
        console.print_json(data=payload)
        return

    scope = language or "overall"
    for d in diffs:
        header = f"[bold]{d.prev_date} → {d.curr_date}[/bold]  ({scope}/{window})"
        s = d.summary
        console.print(
            f"\n{header}  "
            f"[green]+{s['added']} new[/green]  "
            f"[red]-{s['dropped']} dropped[/red]  "
            f"[dim]={s['retained']} retained[/dim]"
        )

        if d.added:
            t = Table(title="New", title_style="green", show_header=True, header_style="bold")
            t.add_column("Repo", style="bold cyan")
            t.add_column("Lang")
            t.add_column("Stars", justify="right")
            t.add_column("Δ window", justify="right", style="green")
            for r in d.added[:limit]:
                t.add_row(
                    r.full_name,
                    r.language or "—",
                    f"{r.stars_total:,}",
                    f"+{r.stars_window:,}",
                )
            console.print(t)

        if d.dropped:
            t = Table(title="Dropped", title_style="red", show_header=True, header_style="bold")
            t.add_column("Repo", style="bold")
            t.add_column("Lang")
            t.add_column("Stars", justify="right")
            for r in d.dropped[:limit]:
                t.add_row(r.full_name, r.language or "—", f"{r.stars_total:,}")
            console.print(t)

        movers = sorted(d.retained, key=lambda c: abs(c.rank_delta), reverse=True)[:limit]
        if movers:
            t = Table(title="Rank movers (retained)", show_header=True, header_style="bold")
            t.add_column("Repo", style="cyan")
            t.add_column("Rank", justify="right")
            t.add_column("Δ rank", justify="right")
            t.add_column("Δ stars", justify="right", style="green")
            for c in movers:
                arrow = "↑" if c.rank_delta > 0 else ("↓" if c.rank_delta < 0 else "·")
                t.add_row(
                    c.repo.full_name,
                    f"{c.prev_rank}→{c.curr_rank}",
                    f"{arrow}{abs(c.rank_delta)}",
                    f"+{c.stars_delta:,}",
                )
            console.print(t)


@app.command()
def cluster(
    language: Optional[str] = typer.Option(
        None, "--language", "-l", help="Language slug; omit for overall."
    ),
    window: Window = typer.Option("weekly", "--window", "-w", help="daily | weekly | monthly"),
    directory: Path = typer.Option(
        Path("digests"), "--dir", "-d", help="Directory containing snapshot JSON files."
    ),
    n_clusters: int = typer.Option(5, "--k", "-k", help="Number of thematic clusters."),
) -> None:
    """Cluster repos across all snapshots into thematic groups (TF-IDF + KMeans)."""
    snapshots = load_snapshots(language=language, window=window, directory=directory)
    if not snapshots:
        console.print(
            f"[yellow]No snapshots found for {language or 'overall'}/{window} in {directory}.[/yellow]"
        )
        raise typer.Exit(code=1)

    repos = gather_repos(snapshots)
    try:
        result = cluster_repos(repos, n_clusters=n_clusters)
    except RuntimeError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1)

    scope = language or "overall"
    console.print(
        f"[bold]Themes across {result.n_repos} unique repos "
        f"({scope}/{window}, {len(snapshots)} snapshots) → {result.n_clusters} clusters[/bold]"
    )
    for c in result.clusters:
        terms = ", ".join(c.top_terms) or "—"
        t = Table(
            title=f"#{c.label}  ({c.size} repos)  · {terms}",
            title_style="bold magenta",
            show_header=True,
            header_style="bold",
        )
        t.add_column("Repo", style="cyan")
        t.add_column("Lang")
        t.add_column("Stars", justify="right")
        t.add_column("Description", overflow="fold")
        for r in sorted(c.repos, key=lambda x: x.stars_total, reverse=True):
            t.add_row(
                r.full_name,
                r.language or "—",
                f"{r.stars_total:,}",
                r.description or "",
            )
        console.print(t)


@app.command()
def version() -> None:
    """Print the package version."""
    from . import __version__

    console.print(f"gh-trends {__version__}")


if __name__ == "__main__":
    app()
