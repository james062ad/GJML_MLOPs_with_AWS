from fastapi import APIRouter, HTTPException, Query
from services.generation_service import generate_response
from services.retrieval_service import retrieve_top_k_chunks
from server.src.config import settings
import traceback

router = APIRouter()


@router.get("/generate")
def generate(
    query: str,
    top_k: int = 5,
    max_tokens: int = 200,
    temperature: float = 0.7,
    llm_provider: str = Query(None, description="Override LLM provider"),
    embedding_provider: str = Query(
        None, description="Override embedding provider"),
):
    """
    FastAPI endpoint to generate a response from user query using top-k RAG retrieval.
    """

    try:
        # 🧠 Override providers if passed from frontend
        if llm_provider:
            settings.llm_provider = llm_provider
        if embedding_provider:
            settings.embedding_provider = embedding_provider

        print(f"🧪 Received query: {query}")
        print(
            f"🔁 Using LLM: {settings.llm_provider} | Embedding: {settings.embedding_provider}")

        # Step 1: Retrieve relevant chunks
        db_config = {
            "dbname": settings.postgres_db,
            "user": settings.postgres_user,
            "password": settings.postgres_password,
            "host": settings.postgres_host,
            "port": settings.postgres_port,
        }

        chunks = retrieve_top_k_chunks(query, top_k=top_k, db_config=db_config)
        print(f"🧪 Retrieved {len(chunks)} chunks")

        # Step 2: Generate a response using the retrieved context
        result = generate_response(
            query, chunks, max_tokens=max_tokens, temperature=temperature)
        print("🧪 generate_response returned:", result)

        if not result or "response" not in result:
            raise ValueError(f"Missing 'response' in LLM result: {result}")

        return result

    except Exception as e:
        print("❌ Exception in /generate endpoint:")
        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail=f"Error generating response: {e}")
