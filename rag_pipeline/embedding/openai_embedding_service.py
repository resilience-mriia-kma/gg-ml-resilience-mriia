from django.conf import settings
from openai import OpenAI

from rag_pipeline.constants import DIMENSIONALITY
from rag_pipeline.embedding.protocols import IEmbeddingService


class OpenAIEmbeddingService(IEmbeddingService):
    MODEL = "text-embedding-3-small"

    def __init__(self) -> None:
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def embed(self, text: str) -> list[float]:
        response = self.client.embeddings.create(
            input=text,
            model=self.MODEL,
            dimensions=DIMENSIONALITY,
        )
        return response.data[0].embedding

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        response = self.client.embeddings.create(
            input=texts,
            model=self.MODEL,
            dimensions=DIMENSIONALITY,
        )
        return [item.embedding for item in response.data]
