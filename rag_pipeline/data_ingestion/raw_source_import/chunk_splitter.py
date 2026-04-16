import tiktoken

from rag_pipeline.constants import MAX_CHUNK_TOKENS

CHUNK_OVERLAP = 50

_enc = tiktoken.encoding_for_model("text-embedding-3-small")


class ChunkSplitter:
    """Splits text into token-bounded chunks with overlap."""

    def token_count(self, text: str) -> int:
        return len(_enc.encode(text))

    def split(self, text: str) -> list[str]:
        tokens = _enc.encode(text)
        if len(tokens) <= MAX_CHUNK_TOKENS:
            return [text]

        chunks = []
        start = 0
        while start < len(tokens):
            end = start + MAX_CHUNK_TOKENS
            chunks.append(_enc.decode(tokens[start:end]))
            if end >= len(tokens):
                break
            start = end - CHUNK_OVERLAP
        return chunks
