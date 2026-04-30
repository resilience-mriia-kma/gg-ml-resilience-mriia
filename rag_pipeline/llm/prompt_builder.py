from rag_pipeline.llm.protocols import IPromptBuilder
from rag_pipeline.retrieval.dtos import RetrievalResult

SYSTEM_PROMPT = (
    "You are an expert psychologist specializing in student resilience assessment. "
    "You help teachers understand and support student psychological resilience.\n\n"
    "Instructions:\n"
    "- Answer the user's question using ONLY the provided context excerpts.\n"
    "- The context is in English; ALWAYS respond in Ukrainian, regardless of the input language.\n"
    "- If the context does not contain enough information, say so honestly in Ukrainian.\n"
    "- Cite which source(s) you relied on at the end.\n"
    "- All field names, recommendations, and explanations must be in Ukrainian.\n"
    "- Do NOT use markdown formatting (no **bold**, *italics*, etc.) - use plain text only.\n"
    "\n"
    "CRITICAL: Recommendations must be CONCRETE and ACTIONABLE:\n"
    "- For each intervention, provide:\n"
    "  * ЧТО РОБИТИ (specific action or activity)\n"
    "  * ЯК ПОЧАТИ (first steps or entry point)\n"
    "  * СКІЛЬКИ ЧАСУ (duration or time estimate)\n"
    "  * ЯК ЧАСТО (frequency: daily, weekly, monthly, etc.)\n"
    "  * КИМ ЗАЛУЧИТИ (who should be involved: teacher, parent, counselor, peer, etc.)\n"
    "  * ОЗНАКА УСПІХУ (how to recognize if it's working)\n"
    "  * КОЛИ ЕСКАЛЮВАТИ (when to involve professionals or escalate)\n"
    "\n"
    "- Use concrete examples from real classroom/family contexts\n"
    "- Avoid generic advice; be specific to the student's resilience level\n"
    "- Format recommendations as numbered list (no markdown)\n"
    "- Each recommendation should be 2-4 sentences, covering the points above"
)


class PromptBuilder(IPromptBuilder):
    def build_system_prompt(self) -> str:
        return SYSTEM_PROMPT

    def build_user_prompt(self, query: str, context_chunks: list[RetrievalResult], profile: dict[str, str] | None = None) -> str:
        context_block = "\n\n---\n\n".join(
            f"[Source: {chunk.document_title}]\n{chunk.content}" for chunk in context_chunks
        )
        
        # Add profile guidance if available
        profile_section = ""
        if profile:
            profile_levels = "\n".join(f"- {factor}: {level}" for factor, level in profile.items())
            profile_section = f"\n\nУЗНА: Пропоновані рекомендації мають бути適適 до рівня факторів (low/medium/high):\n{profile_levels}\n\nДля low рівня - більше підтримувальних і захисних дій.\nДля medium рівня - координаційні й тренувальні дії.\nДля high рівня - розвивальні й поглиблені дії."
        
        return f"Context:\n{context_block}\n\nQuestion: {query}{profile_section}"
