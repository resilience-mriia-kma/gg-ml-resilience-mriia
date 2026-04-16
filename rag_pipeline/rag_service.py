from dataclasses import dataclass

from rag_pipeline.llm.protocols import ILLMService, IPromptBuilder
from rag_pipeline.protocols import IRAGService
from rag_pipeline.retrieval.dtos import RetrievalResult
from rag_pipeline.retrieval.protocols import IRetrievalService


@dataclass(frozen=True)
class RAGResponse:
    answer: str
    sources: list[RetrievalResult]


class RAGService(IRAGService):
    def __init__(
        self,
        retrieval_service: IRetrievalService,
        llm_service: ILLMService,
        prompt_builder: IPromptBuilder,
    ) -> None:
        self.retrieval_service = retrieval_service
        self.llm_service = llm_service
        self.prompt_builder = prompt_builder

    def answer(self, query: str, *, top_k: int = 5) -> RAGResponse:
        chunks = self.retrieval_service.retrieve(query, top_k=top_k)

        system_prompt = self.prompt_builder.build_system_prompt()
        user_prompt = self.prompt_builder.build_user_prompt(query, chunks)
        answer = self.llm_service.generate(system_prompt, user_prompt)

        return RAGResponse(answer=answer, sources=chunks)
