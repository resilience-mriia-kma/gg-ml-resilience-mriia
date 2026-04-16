from __future__ import annotations

import logging
import tempfile
from pathlib import Path

import faiss
import numpy as np
from numpy.typing import NDArray

from .protocols import IVectorIndex

logger = logging.getLogger(__name__)


class FAISSIndex(IVectorIndex):
    """IVectorIndex implementation backed by FAISS IndexIDMap(IndexFlatIP).

    Responsibilities: load/save/add/remove/search vectors.
    Does not handle embedding or persistence of metadata.
    """

    def __init__(self, dimension: int, index_path: Path) -> None:
        self.dimension = dimension
        self.index_path = index_path
        self.faiss_index: faiss.IndexIDMap | None = None

    def load_or_create(self) -> None:
        if self.index_path.exists():
            self.faiss_index = faiss.read_index(str(self.index_path))
            logger.info(f"Loaded FAISS index from {self.index_path} ({self.count} vectors)")
        else:
            inner = faiss.IndexFlatIP(self.dimension)
            self.faiss_index = faiss.IndexIDMap(inner)
            logger.info(f"Created new FAISS index (dim={self.dimension})")

    def save(self) -> None:
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=self.index_path.parent, delete=False, suffix=".tmp") as tmp:
            faiss.write_index(self._ensure_index(), tmp.name)
            Path(tmp.name).replace(self.index_path)
        logger.info(f"Saved FAISS index to {self.index_path} ({self.count} vectors)")

    def add(self, ids: NDArray[np.int64], vectors: NDArray[np.float32]) -> None:
        self._ensure_index().add_with_ids(vectors, ids)

    def remove(self, ids: NDArray[np.int64]) -> None:
        self._ensure_index().remove_ids(ids)

    def search(self, query: NDArray[np.float32], k: int) -> tuple[NDArray[np.float32], NDArray[np.int64]]:
        distances, ids = self._ensure_index().search(query, k)
        return distances, ids

    def get_all_ids(self) -> NDArray[np.int64]:
        index = self._ensure_index()
        if index.ntotal == 0:
            return np.array([], dtype=np.int64)
        return faiss.vector_to_array(index.id_map).copy()

    @property
    def count(self) -> int:
        return self._ensure_index().ntotal

    def _ensure_index(self) -> faiss.IndexIDMap:
        if self.faiss_index is None:
            raise RuntimeError("FAISS index not initialized — call load_or_create() first")
        return self.faiss_index
