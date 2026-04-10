"""Tests for the typer CLI surface."""

from __future__ import annotations

from typer.testing import CliRunner

from gh_trends.cli import app

runner = CliRunner()


def test_top_level_help_lists_all_commands() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    for command in ("fetch", "digest", "serve", "version"):
        assert command in result.stdout


def test_version_command() -> None:
    from gh_trends import __version__

    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_digest_help_shows_options() -> None:
    result = runner.invoke(app, ["digest", "--help"])
    assert result.exit_code == 0
    assert "--language" in result.stdout
    assert "--window" in result.stdout
    assert "--lang" in result.stdout
