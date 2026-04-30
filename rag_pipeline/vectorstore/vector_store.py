from __future__ import annotations

import logging

import numpy as np

from rag_pipeline.embedding.protocols import IEmbeddingService
from rag_pipeline.models import Document, EmbeddingStatus

from .dtos import SearchResult
from .protocols import IDocumentRepository, IVectorIndex, IVectorStore

logger = logging.getLogger(__name__)


class VectorStore(IVectorStore):
    """
    Bridges the vector index and document persistence.

    Single entry point for all index+DB coordination.
    Depends on abstractions (IVectorIndex, IEmbeddingService, IDocumentRepository), not concretions.
    """

    def __init__(self, index: IVectorIndex, embedder: IEmbeddingService, repository: IDocumentRepository) -> None:
        self.index = index
        self.embedder = embedder
        self.repository = repository

    def index_document(self, document: Document) -> int:
        """Embed all chunks and add to the vector index. Returns count of indexed chunks."""
        chunks = self.repository.get_ordered_chunks(document)
        if not chunks:
            logger.warning(f"Document {document.pk} has no chunks to index")
            return 0

        texts = [c.content for c in chunks]
        vectors = np.array(self.embedder.embed_batch(texts), dtype=np.float32)
        ids = np.array([c.pk for c in chunks], dtype=np.int64)

        self.index.add(ids, vectors)
        self.index.save()
        self.repository.update_document_status(document, EmbeddingStatus.INDEXED)

        logger.info(f"Indexed {len(chunks)} chunks for document {document.pk}")
        return len(chunks)

    def remove_document(self, document: Document) -> int:
        """Remove all chunk vectors from the index. Returns count of removed chunks."""
        chunk_ids = self.repository.get_chunk_ids(document)
        if not chunk_ids:
            return 0

        self.index.remove(np.array(chunk_ids, dtype=np.int64))
        self.index.save()
        self.repository.update_document_status(document, EmbeddingStatus.PENDING)

        logger.info(f"Removed {len(chunk_ids)} chunks for document {document.pk}")
        return len(chunk_ids)

    def search(self, query: str, *, profile: dict[str, str] | None = None, k: int = 10) -> list[SearchResult]:
        """Embed query, search index, hydrate from DB preserving rank order."""
        query_vec = np.array(self.embedder.embed(query), dtype=np.float32).reshape(1, -1)
        distances, ids = self.index.search(query_vec, k=max(k, 50))  # Get more for reranking

        valid_mask = ids[0] != -1
        chunk_ids = ids[0][valid_mask].tolist()
        scores = distances[0][valid_mask].tolist()

        if not chunk_ids:
            return []

        chunks_by_pk = self.repository.get_chunks_by_ids(chunk_ids)

        results = []
        for cid, score in zip(chunk_ids, scores, strict=True):
            chunk = chunks_by_pk.get(cid)
            if chunk is not None:
                results.append(SearchResult(chunk=chunk, score=score))
            else:
                logger.warning(f"Chunk {cid} found in index but missing from DB (drift)")

        # Apply metadata-based reranking if profile provided
        if profile:
            results = self._rerank_by_profile(results, profile)

        return results[:k]

    def _rerank_by_profile(self, results: list[SearchResult], profile: dict[str, str]) -> list[SearchResult]:
        """Rerank results based on profile match. Boost score for matching metadata."""
        for result in results:
            # Start with original semantic similarity score
            boost = 0.0
            
            # Boost if resilience_factor matches any of the user's profile factors
            if result.chunk.resilience_factor and result.chunk.resilience_factor in profile:
                boost += 0.20  # 20% boost for factor match
            
            # Boost if target_resilience_level matches user's level for that factor
            if result.chunk.target_resilience_level and result.chunk.resilience_factor:
                user_level = profile.get(result.chunk.resilience_factor)
                if user_level == result.chunk.target_resilience_level:
                    boost += 0.30  # 30% boost for level match
                # Slight boost even if levels differ (content still relevant)
                elif result.chunk.target_resilience_level and user_level:
                    boost += 0.05
            
            # Apply boost to score (lower is better in FAISS, so subtract)
            result.score = result.score * (1.0 - boost)
        
        # Sort by boosted score (ascending, since lower is better in FAISS)
        return sorted(results, key=lambda r: r.score)
        for result in results:
            boost = 0.0
            chunk = result.chunk

            # Boost if resilience_factor matches any low/medium factor in profile
            if chunk.resilience_factor:
                for factor, level in profile.items():
                    if level in ('low', 'medium') and chunk.resilience_factor == factor:
                        boost += 0.2  # Boost for relevant factors

            # Boost if target_resilience_level matches
            if chunk.target_resilience_level:
                # If student has low in a factor, prefer chunks targeting low
                for factor, level in profile.items():
                    if chunk.target_resilience_level == level:
                        boost += 0.3  # Strong boost for level match

            # Slight boost for category match (if we had category logic)
            # For now, just factor and level

            new_score = result.score * (1 + boost)
            reranked.append(SearchResult(chunk=chunk, score=new_score))

        # Sort by new score descending
        reranked.sort(key=lambda r: r.score, reverse=True)
        return reranked

        return results

    def reindex_document(self, document: Document) -> int:
        """Remove existing vectors and re-index from current chunk content."""
        self.remove_document(document)
        return self.index_document(document)
