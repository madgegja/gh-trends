"""Tests for the Anthropic-backed summarizer."""

from __future__ import annotations

from datetime import date

import pytest

from gh_trends.models import TrendingSnapshot
from gh_trends.summarizer import build_prompt, summarize


def test_build_prompt_includes_repo_data_ko(sample_snapshot: TrendingSnapshot) -> None:
    prompt = build_prompt(sample_snapshot, lang="ko")
    assert "한국어" in prompt
    assert "NousResearch/hermes-agent" in prompt
    assert "delta=+19765" in prompt
    assert "lang=Python" in prompt
    assert "python (weekly)" in prompt
    assert "2026-04-10" in prompt


def test_build_prompt_english_template(sample_snapshot: TrendingSnapshot) -> None:
    prompt = build_prompt(sample_snapshot, lang="en")
    assert "Write in English" in prompt
    assert "NousResearch/hermes-agent" in prompt


def test_summarize_empty_snapshot_short_circuits(monkeypatch: pytest.MonkeyPatch) -> None:
    # If the function ever reached the API, this would explode loudly.
    monkeypatch.setattr(
        "gh_trends.summarizer.Anthropic",
        lambda **_: pytest.fail("Anthropic must not be called for empty snapshots"),
    )
    empty = TrendingSnapshot(fetched_on=date(2026, 4, 10), window="daily")
    result = summarize(empty, api_key="ignored")
    assert "빈 스냅샷" in result


def test_summarize_missing_key_raises(
    sample_snapshot: TrendingSnapshot, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
        summarize(sample_snapshot)


def test_summarize_calls_anthropic_with_built_prompt(
    sample_snapshot: TrendingSnapshot, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict = {}

    class FakeBlock:
        type = "text"
        text = "## 트렌드 디지스트 — python (weekly) — 2026-04-10\n\n(stub)"

    class FakeResponse:
        content = [FakeBlock()]

    class FakeMessages:
        def create(self, **kwargs):
            captured.update(kwargs)
            return FakeResponse()

    class FakeClient:
        def __init__(self, api_key: str) -> None:
            captured["api_key"] = api_key
            self.messages = FakeMessages()

    monkeypatch.setattr("gh_trends.summarizer.Anthropic", FakeClient)
    out = summarize(sample_snapshot, lang="ko", api_key="sk-test")

    assert "트렌드 디지스트" in out
    assert captured["api_key"] == "sk-test"
    assert captured["model"] == "claude-opus-4-6"
    assert captured["max_tokens"] == 4096
    assert captured["messages"][0]["role"] == "user"
    assert "NousResearch/hermes-agent" in captured["messages"][0]["content"]
