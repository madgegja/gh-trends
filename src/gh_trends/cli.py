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
def version() -> None:
    """Print the package version."""
    from . import __version__

    console.print(f"gh-trends {__version__}")


if __name__ == "__main__":
    app()
