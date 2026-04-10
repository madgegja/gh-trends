"""Tests for the dual-mode summarizer (proxy-first, SDK-fallback)."""

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
    monkeypatch.delenv("CLAUDE_PROXY_URL", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    empty = TrendingSnapshot(fetched_on=date(2026, 4, 10), window="daily")
    result = summarize(empty, api_key="ignored")
    assert "빈 스냅샷" in result


def test_summarize_missing_both_raises(
    sample_snapshot: TrendingSnapshot, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("CLAUDE_PROXY_URL", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="CLAUDE_PROXY_URL.*ANTHROPIC_API_KEY"):
        summarize(sample_snapshot)


def test_summarize_sdk_mode_with_explicit_key(
    sample_snapshot: TrendingSnapshot, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Explicit api_key= forces SDK mode regardless of env."""
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

    monkeypatch.delenv("CLAUDE_PROXY_URL", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr("gh_trends.summarizer.Anthropic", FakeClient)
    out = summarize(sample_snapshot, lang="ko", api_key="sk-test")

    assert "트렌드 디지스트" in out
    assert captured["api_key"] == "sk-test"
    assert captured["model"] == "claude-sonnet-4-20250514"
    assert captured["messages"][0]["role"] == "user"
    assert "NousResearch/hermes-agent" in captured["messages"][0]["content"]


def test_summarize_sdk_mode_via_env(
    sample_snapshot: TrendingSnapshot, monkeypatch: pytest.MonkeyPatch
) -> None:
    """ANTHROPIC_API_KEY env (no proxy) → SDK mode."""
    captured: dict = {}

    class FakeBlock:
        type = "text"
        text = "digest stub"

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

    monkeypatch.delenv("CLAUDE_PROXY_URL", raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-env-key")
    monkeypatch.setattr("gh_trends.summarizer.Anthropic", FakeClient)
    summarize(sample_snapshot)

    assert captured["api_key"] == "sk-env-key"


def test_summarize_proxy_mode(
    sample_snapshot: TrendingSnapshot, monkeypatch: pytest.MonkeyPatch
) -> None:
    """CLAUDE_PROXY_URL set → proxy mode (OpenAI-compatible endpoint)."""
    captured: dict = {}

    class FakeResponse:
        status_code = 200

        def raise_for_status(self):
            pass

        def json(self):
            return {"choices": [{"message": {"content": "## proxy digest stub"}}]}

    class FakeClient:
        def __init__(self, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def post(self, url, **kwargs):
            captured["url"] = url
            captured["payload"] = kwargs.get("json", {})
            return FakeResponse()

    monkeypatch.setenv("CLAUDE_PROXY_URL", "http://127.0.0.1:3456/v1")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr("gh_trends.summarizer.httpx.Client", FakeClient)
    out = summarize(sample_snapshot)

    assert out == "## proxy digest stub"
    assert captured["url"] == "http://127.0.0.1:3456/v1/chat/completions"
    assert captured["payload"]["model"] == "claude-sonnet-4-20250514"
    assert captured["payload"]["messages"][0]["role"] == "user"
    assert "NousResearch/hermes-agent" in captured["payload"]["messages"][0]["content"]


def test_summarize_proxy_takes_priority_over_sdk(
    sample_snapshot: TrendingSnapshot, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When both CLAUDE_PROXY_URL and ANTHROPIC_API_KEY are set, proxy wins."""

    class FakeResponse:
        status_code = 200

        def raise_for_status(self):
            pass

        def json(self):
            return {"choices": [{"message": {"content": "proxy wins"}}]}

    class FakeClient:
        def __init__(self, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def post(self, url, **kwargs):
            return FakeResponse()

    monkeypatch.setenv("CLAUDE_PROXY_URL", "http://127.0.0.1:3456/v1")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-should-not-be-used")
    monkeypatch.setattr("gh_trends.summarizer.httpx.Client", FakeClient)
    monkeypatch.setattr(
        "gh_trends.summarizer.Anthropic",
        lambda **_: pytest.fail("SDK must not be called when proxy is set"),
    )
    out = summarize(sample_snapshot)

    assert out == "proxy wins"
