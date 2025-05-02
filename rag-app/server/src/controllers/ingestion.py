from fastapi import APIRouter, Query, HTTPException, Request
from server.src.services import ingestion_service
from server.src.config import settings
from datetime import datetime, timezone

router = APIRouter()


@router.post("/rebuild")
def rebuild_vector_store(
    request: Request,
    json_dir: str = Query(..., description="Directory containing JSON files"),
    output_file: str = Query("init/processed_papers.json",
                             description="Path to save processed papers"),
    chunk_size: int = Query(512, description="Chunk size for splitting text"),
    overlap: int = Query(50, description="Token overlap between chunks")
):
    """
    API endpoint to rebuild the vector DB using the current or overridden embedding provider.
    """
    try:
        # 🧠 Allow overriding the embedding provider dynamically via query string
        provider_override = request.query_params.get("embedding_provider")
        if provider_override:
            print(f"⚙️ Overriding embedding_provider → {provider_override}")
            settings.embedding_provider = provider_override

        # 🚀 Kick off the full rebuild
        ingestion_service.rebuild_vector_db(
            json_dir=json_dir,
            output_file=output_file,
            chunk_size=chunk_size,
            overlap=overlap
        )

        # 🧠 Dimension is detected inside rebuild_vector_db(), but we'll return it again here
        dim = ingestion_service.detect_embedding_dim()

        return {
            "status": "success",
            "message": f"Rebuilt vector DB and ingested with dimension {dim}.",
            "embedding_dimension": dim,
            "embedding_provider": str(settings.embedding_provider),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Rebuild failed: {str(e)}")
