"""Compact Pydantic projections of SDK responses for tidy list returns."""

from pydantic import BaseModel


class McpVoice(BaseModel):
    """Trimmed voice catalog entry."""

    id: str
    name: str
    language: str | None = None
    gender: str | None = None
    description: str | None = None
    is_cloned: bool = False


class McpModel(BaseModel):
    """Trimmed LLM catalog entry."""

    id: str
    provider: str
    available: bool
