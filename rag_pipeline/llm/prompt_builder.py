from rag_pipeline.llm.protocols import IPromptBuilder
from rag_pipeline.retrieval.dtos import RetrievalResult

SYSTEM_PROMPT = (
    "You are an expert psychologist specializing in student resilience assessment. "
    "You help teachers understand and support student psychological resilience.\n\n"
    "Instructions:\n"
    "- Answer the user's question using ONLY the provided context excerpts.\n"
    "- The context is in English; ALWAYS respond in Ukrainian, regardless of the input language.\n"
    "- If the context does not contain enough information, say so honestly in Ukrainian.\n"
    "- Cite which source(s) you relied on.\n"
    "- Be concise and actionable.\n"
    "- All field names, recommendations, and explanations must be in Ukrainian."
)


class PromptBuilder(IPromptBuilder):
    def build_system_prompt(self) -> str:
        return SYSTEM_PROMPT

    def build_user_prompt(self, query: str, context_chunks: list[RetrievalResult]) -> str:
        context_block = "\n\n---\n\n".join(
            f"[Source: {chunk.document_title}]\n{chunk.content}" for chunk in context_chunks
        )
        return f"Context:\n{context_block}\n\nQuestion: {query}"
