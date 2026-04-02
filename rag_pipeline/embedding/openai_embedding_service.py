import numpy as np
from django.conf import settings
from numpy.typing import NDArray
from openai import OpenAI

from rag_pipeline.constants import DIMENSIONALITY
from rag_pipeline.retrieval.protocol import IEmbedder


class OpenAIEmbeddingService(IEmbedder):
    MODEL = "text-embedding-3-small"

    def __init__(self) -> None:
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    @property
    def dimension(self) -> int:
        return DIMENSIONALITY

    def embed(self, text: str) -> NDArray[np.float32]:
        response = self.client.embeddings.create(
            input=text,
            model=self.MODEL,
            dimensions=DIMENSIONALITY,
        )
        return np.array(response.data[0].embedding, dtype=np.float32)

    def embed_batch(self, texts: list[str]) -> NDArray[np.float32]:
        response = self.client.embeddings.create(
            input=texts,
            model=self.MODEL,
            dimensions=DIMENSIONALITY,
        )
        return np.array([item.embedding for item in response.data], dtype=np.float32)
