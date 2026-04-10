"""Pydantic models for trending data."""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

Window = Literal["daily", "weekly", "monthly"]


class TrendingRepo(BaseModel):
    owner: str
    name: str
    url: str
    description: str | None = None
    language: str | None = None
    stars_total: int = 0
    stars_window: int = Field(0, description="Stars gained during the requested window.")

    @property
    def full_name(self) -> str:
        return f"{self.owner}/{self.name}"


class TrendingSnapshot(BaseModel):
    fetched_on: date
    window: Window
    language: str | None = None
    repos: list[TrendingRepo] = Field(default_factory=list)
