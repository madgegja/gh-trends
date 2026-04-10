"""Summarize a TrendingSnapshot into a thematic markdown digest via the Anthropic API."""

from __future__ import annotations

import os
from typing import Literal

from anthropic import Anthropic

from .models import TrendingSnapshot

DigestLang = Literal["ko", "en"]
DEFAULT_MODEL = "claude-opus-4-6"
MAX_TOKENS = 4096

_PROMPT_KO = """다음은 GitHub trending 스냅샷입니다. 이를 분석해 정확히 아래 형식의 마크다운 디지스트를 작성하세요. 마크다운 외 다른 텍스트는 출력하지 마세요.

## 트렌드 디지스트 — {scope} ({window}) — {date}

### 핵심 테마
- **<테마 이름>** — 왜 뜨는지 한 문장, 어떤 레포가 이를 대표하는지.
- (3~5개 테마, 비슷한 레포는 하나의 테마로 묶기)

### 주요 레포
| 레포 | 언어 | 별 (Δ window) | 카테고리 | 한 줄 설명 |
|---|---|---|---|---|

### 인사이트
- 1~3개 불릿. 놀라운 점, 의미 있는 패턴, 또는 *없는데 있을 법한* 것.

규칙:
- 별 개수, 설명, 언어를 절대 지어내지 마세요. 데이터에 있는 값만 사용하세요.
- 카테고리는 다음 중 하나: agent, rag, mcp, infra, devtool, data, ml, ui, security, other.
- 한국어로 작성하세요.

데이터 ({count}개 레포):
{rows}
"""

_PROMPT_EN = """The following is a GitHub trending snapshot. Analyze it and produce a markdown digest in EXACTLY the structure below. Output nothing but the markdown.

## Trend digest — {scope} ({window}) — {date}

### Themes
- **<theme name>** — one sentence on why it's hot and which repos exemplify it.
- (3-5 themes max; merge similar repos under one theme)

### Top repos
| Repo | Lang | Stars (Δ window) | Category | One-liner |
|---|---|---|---|---|

### Insights
- 1-3 bullets on what surprised you or what's notably absent.

Rules:
- Never invent stars, descriptions, or languages. Use only what's in the data.
- Category must be one of: agent, rag, mcp, infra, devtool, data, ml, ui, security, other.
- Write in English.

Data ({count} repos):
{rows}
"""


def _format_rows(snapshot: TrendingSnapshot) -> str:
    return "\n".join(
        f"- {r.full_name} | lang={r.language or 'unknown'} | "
        f"stars={r.stars_total} | delta=+{r.stars_window} | "
        f"desc={r.description or '(none)'}"
        for r in snapshot.repos
    )


def build_prompt(snapshot: TrendingSnapshot, lang: DigestLang = "ko") -> str:
    template = _PROMPT_KO if lang == "ko" else _PROMPT_EN
    return template.format(
        scope=snapshot.language or "overall",
        window=snapshot.window,
        date=snapshot.fetched_on.isoformat(),
        count=len(snapshot.repos),
        rows=_format_rows(snapshot),
    )


def summarize(
    snapshot: TrendingSnapshot,
    *,
    lang: DigestLang = "ko",
    model: str = DEFAULT_MODEL,
    api_key: str | None = None,
) -> str:
    """Call the Anthropic API and return a markdown digest."""
    if not snapshot.repos:
        return "_(빈 스냅샷 — 디지스트할 레포가 없습니다.)_"

    key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set. Export it or pass api_key= explicitly."
        )

    client = Anthropic(api_key=key)
    prompt = build_prompt(snapshot, lang=lang)

    response = client.messages.create(
        model=model,
        max_tokens=MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}],
    )

    parts = [block.text for block in response.content if getattr(block, "type", None) == "text"]
    return "".join(parts).strip()
