"""Tests for the proxy-only summarizer."""

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


def test_summarize_empty_snapshot_short_circuits() -> None:
    empty = TrendingSnapshot(fetched_on=date(2026, 4, 10), window="daily")
    result = summarize(empty)
    assert "빈 스냅샷" in result


def test_summarize_calls_proxy(
    sample_snapshot: TrendingSnapshot, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verifies proxy endpoint, payload format, and response parsing."""
    captured: dict = {}

    class FakeResponse:
        status_code = 200

        def raise_for_status(self):
            pass

        def json(self):
            return {"choices": [{"message": {"content": "## 트렌드 디지스트 stub"}}]}

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

    monkeypatch.setattr("gh_trends.summarizer.httpx.Client", FakeClient)
    out = summarize(sample_snapshot, proxy_url="http://127.0.0.1:3456/v1")

    assert out == "## 트렌드 디지스트 stub"
    assert captured["url"] == "http://127.0.0.1:3456/v1/chat/completions"
    assert captured["payload"]["model"] == "claude-sonnet-4-20250514"
    assert captured["payload"]["max_tokens"] == 4096
    assert captured["payload"]["temperature"] == 0.3
    assert captured["payload"]["messages"][0]["role"] == "user"
    assert "NousResearch/hermes-agent" in captured["payload"]["messages"][0]["content"]


def test_summarize_uses_env_var(
    sample_snapshot: TrendingSnapshot, monkeypatch: pytest.MonkeyPatch
) -> None:
    """CLAUDE_PROXY_URL env var is picked up."""
    captured: dict = {}

    class FakeResponse:
        status_code = 200

        def raise_for_status(self):
            pass

        def json(self):
            return {"choices": [{"message": {"content": "ok"}}]}

    class FakeClient:
        def __init__(self, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def post(self, url, **kwargs):
            captured["url"] = url
            return FakeResponse()

    monkeypatch.setenv("CLAUDE_PROXY_URL", "http://custom:9999/v1")
    monkeypatch.setattr("gh_trends.summarizer.httpx.Client", FakeClient)
    summarize(sample_snapshot)

    assert captured["url"] == "http://custom:9999/v1/chat/completions"


def test_summarize_defaults_to_localhost_proxy(
    sample_snapshot: TrendingSnapshot, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No env var and no explicit proxy_url → falls back to DEFAULT_PROXY_URL."""
    captured: dict = {}

    class FakeResponse:
        status_code = 200

        def raise_for_status(self):
            pass

        def json(self):
            return {"choices": [{"message": {"content": "default"}}]}

    class FakeClient:
        def __init__(self, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def post(self, url, **kwargs):
            captured["url"] = url
            return FakeResponse()

    monkeypatch.delenv("CLAUDE_PROXY_URL", raising=False)
    monkeypatch.setattr("gh_trends.summarizer.httpx.Client", FakeClient)
    summarize(sample_snapshot)

    assert captured["url"] == "http://127.0.0.1:3456/v1/chat/completions"
