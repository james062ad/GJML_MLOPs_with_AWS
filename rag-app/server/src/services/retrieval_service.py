"""Retrieve documents service

This will perform naive rag retrieval for a given query using cosine similarity and top_k retrieval
"""
import psycopg2
from typing import List, Dict
from sentence_transformers import SentenceTransformer
import opik

# Initialize as None, will be loaded on first use
_embedding_model = None

def get_embedding_model():
    """Get the embedding model, initializing it if necessary."""
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedding_model


def get_db_connection(db_config: dict):
    """
    Establishes a connection to the Postgres database.

    Args:
        db_config (dict): Dictionary containing Postgres connection details (dbname, user, password, host, port).

    Returns:
        psycopg2.connection: The connection object.
    """
    return psycopg2.connect(**db_config)


@opik.track
def retrieve_top_k_chunks(query: str, top_k: int, db_config: dict) -> List[Dict]:
    """
    Retrieves the top_k documents based on cosine similarity to the query embedding using pgvector.

    Args:
        query (str): The input query.
        top_k (int): The number of top chunks to retrieve.
        db_config (dict): Dictionary containing Postgres connection details.

    Returns:
        List[Dict]: A list of dictionaries containing the top_k chunks with their titles and summaries.
    """
    # Generate the embedding for the query
    query_embedding = get_embedding_model().encode(
        query, convert_to_tensor=False
    )
    
    # Convert to list if it's a numpy array
    if hasattr(query_embedding, 'tolist'):
        query_embedding = query_embedding.tolist()

    # Connect to the database
    conn = get_db_connection(db_config)

    try:
        cursor = conn.cursor()

        # SQL query to find the top_k chunks using cosine similarity
        query = """
        SELECT id, title, chunk, embedding <=> %s::vector AS similarity
        FROM papers
        ORDER BY similarity ASC
        LIMIT %s;
        """

        # Execute the query with the query embedding and top_k value
        cursor.execute(query, (query_embedding, top_k))
        rows = cursor.fetchall()

        # Prepare the results
        results = [
            {"id": row[0], "title": row[1], "chunk": row[2], "similarity_score": row[3]}
            for row in rows
        ]

        return results

    finally:
        cursor.close()
        conn.close()
