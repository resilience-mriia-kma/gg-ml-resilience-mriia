from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np

from rag_pipeline.models import Document, DocumentChunk, EmbeddingStatus

from .protocol import IDocumentRepository, IEmbedder, IVectorIndex

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SearchResult:
    chunk: DocumentChunk
    score: float


class VectorStore:
    """Bridges the vector index and document persistence.

    Single entry point for all index+DB coordination.
    Depends on abstractions (IVectorIndex, IEmbedder, IDocumentRepository), not concretions.
    """

    def __init__(self, index: IVectorIndex, embedder: IEmbedder, repository: IDocumentRepository) -> None:
        self.index = index
        self.embedder = embedder
        self.repo = repository

    def index_document(self, document: Document) -> int:
        """Embed all chunks and add to the vector index. Returns count of indexed chunks."""
        chunks = self.repo.get_ordered_chunks(document)
        if not chunks:
            logger.warning("Document %d has no chunks to index", document.pk)
            return 0

        texts = [c.content for c in chunks]
        vectors = np.array(self.embedder.embed_batch(texts), dtype=np.float32)
        ids = np.array([c.pk for c in chunks], dtype=np.int64)

        self.index.add(ids, vectors)
        self.index.save()
        self.repo.update_document_status(document, EmbeddingStatus.INDEXED)

        logger.info("Indexed %d chunks for document %d", len(chunks), document.pk)
        return len(chunks)

    def remove_document(self, document: Document) -> int:
        """Remove all chunk vectors from the index. Returns count of removed chunks."""
        chunk_ids = self.repo.get_chunk_ids(document)
        if not chunk_ids:
            return 0

        self.index.remove(np.array(chunk_ids, dtype=np.int64))
        self.index.save()
        self.repo.update_document_status(document, EmbeddingStatus.PENDING)

        logger.info("Removed %d chunks for document %d", len(chunk_ids), document.pk)
        return len(chunk_ids)

    def search(self, query: str, k: int = 10) -> list[SearchResult]:
        """Embed query, search index, hydrate from DB preserving rank order."""
        query_vec = np.array(self.embedder.embed(query), dtype=np.float32).reshape(1, -1)
        distances, ids = self.index.search(query_vec, k)

        # FAISS returns -1 for unfilled slots
        valid_mask = ids[0] != -1
        chunk_ids = ids[0][valid_mask].tolist()
        scores = distances[0][valid_mask].tolist()

        if not chunk_ids:
            return []

        chunks_by_pk = self.repo.get_chunks_by_ids(chunk_ids)

        # Preserve FAISS ranking, skip any chunks missing from DB (drift)
        results = []
        for cid, score in zip(chunk_ids, scores, strict=True):
            chunk = chunks_by_pk.get(cid)
            if chunk is not None:
                results.append(SearchResult(chunk=chunk, score=score))
            else:
                logger.warning("Chunk %d found in index but missing from DB (drift)", cid)

        return results

    def reindex_document(self, document: Document) -> int:
        """Remove existing vectors and re-index from current chunk content."""
        self.remove_document(document)
        return self.index_document(document)
