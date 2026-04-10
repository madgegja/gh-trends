"""Async fetcher for github.com/trending pages."""

from __future__ import annotations

from datetime import date

import httpx
from selectolax.parser import HTMLParser

from .models import TrendingRepo, TrendingSnapshot, Window

USER_AGENT = "gh-trends/0.1 (+https://github.com/)"
BASE = "https://github.com/trending"


def _build_url(language: str | None, window: Window) -> str:
    path = f"{BASE}/{language}" if language and language != "all" else BASE
    return f"{path}?since={window}"


def _parse_int(raw: str) -> int:
    digits = raw.replace(",", "").strip()
    return int(digits) if digits.isdigit() else 0


def _parse_repo(article) -> TrendingRepo | None:
    title_node = article.css_first("h2 a")
    if title_node is None:
        return None
    href = (title_node.attributes.get("href") or "").strip("/")
    if "/" not in href:
        return None
    owner, name = href.split("/", 1)

    desc_node = article.css_first("p")
    description = desc_node.text(strip=True) if desc_node else None

    lang_node = article.css_first('[itemprop="programmingLanguage"]')
    language = lang_node.text(strip=True) if lang_node else None

    stars_total = 0
    star_link = article.css_first('a[href$="/stargazers"]')
    if star_link is not None:
        stars_total = _parse_int(star_link.text())

    stars_window = 0
    for span in article.css("span.d-inline-block.float-sm-right"):
        stars_window = _parse_int(span.text().split()[0])
        break

    return TrendingRepo(
        owner=owner,
        name=name,
        url=f"https://github.com/{owner}/{name}",
        description=description,
        language=language,
        stars_total=stars_total,
        stars_window=stars_window,
    )


async def fetch_trending(
    language: str | None = None,
    window: Window = "daily",
    *,
    client: httpx.AsyncClient | None = None,
) -> TrendingSnapshot:
    """Fetch one trending page and return a parsed snapshot."""
    url = _build_url(language, window)
    owns_client = client is None
    client = client or httpx.AsyncClient(
        headers={"User-Agent": USER_AGENT},
        timeout=httpx.Timeout(15.0),
        follow_redirects=True,
    )
    try:
        response = await client.get(url)
        response.raise_for_status()
    finally:
        if owns_client:
            await client.aclose()

    tree = HTMLParser(response.text)
    repos: list[TrendingRepo] = []
    for article in tree.css("article.Box-row"):
        repo = _parse_repo(article)
        if repo is not None:
            repos.append(repo)

    return TrendingSnapshot(
        fetched_on=date.today(),
        window=window,
        language=language,
        repos=repos,
    )
