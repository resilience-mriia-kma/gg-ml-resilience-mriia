from dataclasses import dataclass


@dataclass(frozen=True)
class RawChunk:
    content: str
    resilience_factor: str
    category: str
    token_count: int
    chunk_index: int
