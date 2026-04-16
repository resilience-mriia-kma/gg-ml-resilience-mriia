import json

from dependency_injector.wiring import Provide, inject
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from rag_pipeline.container import RAGContainer
from rag_pipeline.rag_service import RAGService


@require_POST
@inject
def query(request, rag_service: RAGService = Provide[RAGContainer.rag_service]):
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    user_query = body.get("query", "").strip()
    if not user_query:
        return JsonResponse({"error": "Field 'query' is required"}, status=400)

    top_k = body.get("top_k", 5)

    response = rag_service.answer(user_query, top_k=top_k)

    return JsonResponse(
        {
            "answer": response.answer,
            "sources": [
                {
                    "chunk_id": s.chunk_id,
                    "document_title": s.document_title,
                    "score": s.score,
                }
                for s in response.sources
            ],
        }
    )
