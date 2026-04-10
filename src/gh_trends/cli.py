"""Typer CLI for gh-trends."""

from __future__ import annotations

import asyncio
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
    model: str = typer.Option(DEFAULT_MODEL, "--model", help="Anthropic model id"),
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
def serve() -> None:
    """Launch the MCP stdio server. Configure your MCP client to spawn this."""
    from .server import main as serve_main

    serve_main()


@app.command()
def version() -> None:
    """Print the package version."""
    from . import __version__

    console.print(f"gh-trends {__version__}")


if __name__ == "__main__":
    app()
