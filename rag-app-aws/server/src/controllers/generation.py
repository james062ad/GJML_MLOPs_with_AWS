from fastapi import APIRouter, HTTPException, Query
from typing import List
from services.generation_service import generate_response, safe_opik_track
from services.retrieval_service import retrieve_top_k_chunks
from services.query_expansion_service import expand_query
from models.document import RetrievedDocument
import os
from config import settings

router = APIRouter()

# Reuse your database configuration
db_config = {
    "dbname": os.environ.get("POSTGRES_DB"),
    "user": os.environ.get("POSTGRES_USER"),
    "password": os.environ.get("POSTGRES_PASSWORD"),
    "host": os.environ.get("POSTGRES_HOST"),
    "port": os.environ.get("POSTGRES_PORT"),
}

@safe_opik_track
@router.get("/generate")
async def generate_answer_endpoint(
    query: str = Query(..., description="The query text from the user"),
    top_k: int = Query(5, description="Number of top chunks to retrieve"),
    max_tokens: int = Query(
        200, description="The maximum number of tokens to generate"
    ),
    temperature: float = Query(0.7, description="Sampling temperature for the model"),
):
    """
    Retrieve the top K relevant chunks and generate a response based on them.

    Args:
        query (str): The query text from the user.
        top_k (int): Number of top chunks to retrieve.
        max_tokens (int): Maximum number of tokens to generate in the response.
        temperature (float): Temperature setting for the generation model.

    Returns:
        str: The generated answer based on the query and retrieved chunks.
    """
    try:
        # First retrieve relevant chunks
        chunks = retrieve_top_k_chunks(query, top_k, db_config=db_config)
        
        # Then generate a response based on those chunks
        response = await generate_response(
            query=query,
            chunks=chunks,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        if not response:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate response"
            )
            
        return response
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating answer: {str(e)}"
        )
