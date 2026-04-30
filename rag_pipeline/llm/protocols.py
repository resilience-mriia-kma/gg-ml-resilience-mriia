from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from rag_pipeline.retrieval.dtos import RetrievalResult


class ILLMService(Protocol):
    def generate(self, system_prompt: str, user_prompt: str) -> str: ...


class IPromptBuilder(Protocol):
    def build_system_prompt(self) -> str: ...

    def build_user_prompt(self, query: str, context_chunks: list[RetrievalResult], profile: dict[str, str] | None = None) -> str: ...
