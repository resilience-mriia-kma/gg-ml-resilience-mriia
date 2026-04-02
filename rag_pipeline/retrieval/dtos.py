from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievalResult:
    chunk_id: int
    content: str
    score: float
    document_title: str
