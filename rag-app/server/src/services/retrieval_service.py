"""
🔎 Retrieve documents service

Performs RAG-style top-k retrieval via cosine similarity using pgvector. Embeddings for the query are generated
using the configured EMBEDDING_PROVIDER — this may differ from LLM_PROVIDER.
"""

import psycopg2
from typing import List, Dict
import opik
import requests
import json
from server.src.config import settings

# ─────────────────────────────────────────────────────────────
# 🧠 PROVIDER-AWARE EMBEDDING DISPATCH
# ─────────────────────────────────────────────────────────────


def embed_query(query: str) -> List[float]:
    """
    Generate an embedding for the input query using the configured provider.
    Returns a single embedding as a flat list of floats.

    Supported providers:
    - sentence-transformer
    - openai
    - bedrock
    - huggingface
    - cohere
    - anthropic
    - azure
    - google
    - mistral
    """
    provider = settings.embedding_provider

    # ─── 1. SentenceTransformer (local, no API) ─────────────────────────────────
    # INPUT: single string
    # OUTPUT: numpy array (converted to list via .tolist())
    # NOTES: deterministic, requires model download, best for dev/testing
    if provider == "sentence-transformer":
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("all-MiniLM-L6-v2")
        return model.encode(query).tolist()

    # ─── 2. OpenAI Embeddings API ───────────────────────────────────────────────
    # INPUT: "input": <string>
    # OUTPUT: JSON -> {"data": [{"embedding": [...]}]}
    # NOTES: model must be from embedding family (e.g. text-embedding-ada-002)
    elif provider == "openai":
        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json"
        }
        response = requests.post(
            "https://api.openai.com/v1/embeddings",
            headers=headers,
            json={"input": query, "model": settings.openai_embedding_model}
        )
        return response.json()["data"][0]["embedding"]

    # ─── 3. AWS Bedrock ─────────────────────────────────────────────────────────
    # INPUT: { "inputText": <string> }
    # OUTPUT: JSON -> { "embedding": [...] }
    # NOTES: model must be Bedrock-compatible (e.g. amazon.titan-embed-text-v2:0)
    elif provider == "bedrock":
        import boto3
        client = boto3.client(
            "bedrock-runtime", region_name=settings.aws_region)
        response = client.invoke_model(
            modelId=settings.bedrock_embedding_model_id,
            body=json.dumps({"inputText": query}),
            contentType="application/json",
            accept="application/json"
        )
        return json.loads(response["body"].read())["embedding"]

    # ─── 4. HuggingFace Inference API ───────────────────────────────────────────
    # INPUT: "inputs": <string>
    # OUTPUT: list of floats, or nested list for batched input
    # NOTES: result is usually [[...]] for batch, use [0] to extract embedding
    elif provider == "huggingface":
        headers = {"Authorization": f"Bearer {settings.huggingface_api_key}"}
        response = requests.post(
            f"https://api-inference.huggingface.co/pipeline/feature-extraction/{settings.huggingface_model}",
            headers=headers,
            json={"inputs": query}
        )
        return response.json()[0]

    # ─── 5. Cohere Embed API ────────────────────────────────────────────────────
    # INPUT: "texts": [<string>]
    # OUTPUT: JSON -> {"embeddings": [ [...embedding...] ]}
    # NOTES: always returns batch, so you must extract [0]
    elif provider == "cohere":
        headers = {
            "Authorization": f"Bearer {settings.cohere_api_key}",
            "Content-Type": "application/json"
        }
        response = requests.post(
            "https://api.cohere.ai/v1/embed",
            headers=headers,
            json={"texts": [query]}
        )
        return response.json()["embeddings"][0]

    # ─── 6. Anthropic (custom assumption) ───────────────────────────────────────
    # INPUT: "text": <string>
    # OUTPUT: JSON -> {"embedding": [...]}
    # NOTES: Anthropic does not have public embedding API (assumed format or via proxy)
    elif provider == "anthropic":
        headers = {
            "x-api-key": settings.anthropic_api_key,
            "Content-Type": "application/json"
        }
        response = requests.post(
            "https://api.anthropic.com/v1/embeddings",
            headers=headers,
            json={"text": query, "model": settings.anthropic_embedding_model}
        )
        return response.json()["embedding"]

    # ─── 7. Azure OpenAI ────────────────────────────────────────────────────────
    # INPUT: "input": <string>
    # OUTPUT: JSON -> {"data": [{"embedding": [...]}]}
    # NOTES: model deployed in your Azure instance; use correct API version
    elif provider == "azure":
        headers = {
            "api-key": settings.azure_openai_api_key,
            "Content-Type": "application/json"
        }
        url = f"{settings.azure_endpoint}/openai/deployments/{settings.azure_embedding_deployment}/embeddings?api-version=2023-05-15"
        response = requests.post(
            url,
            headers=headers,
            json={"input": query}
        )
        return response.json()["data"][0]["embedding"]


    # ─── 8. Google PaLM API (Vertex AI) ─────────────────────────────────────────
    # INPUT: { "text": <string> }
    # OUTPUT: JSON -> { "embedding": { "value": [ ... ] } }
    # NOTES: requires model and key to be valid for the PaLM embedding endpoint
    elif provider == "google":
        url = f"https://generativelanguage.googleapis.com/v1/models/{settings.google_embedding_model}:embedContent?key={settings.google_api_key}"
        headers = {"Content-Type": "application/json"}
        body = {
            "content": {
                "parts": [{"text": query}]
            }
        }
        response = requests.post(url, headers=headers, json=body)
        result = response.json()

        if "embedding" not in result or "values" not in result["embedding"]:
            raise ValueError(
                f"❌ Google embedding error: {json.dumps(result, indent=2)}")

        return result["embedding"]["values"]

    # ─── 9. Mistral (via Together.ai or similar) ────────────────────────────────
    # INPUT: "input": <string>
    # OUTPUT: JSON -> { "data": [ { "embedding": [...] } ] }
    # NOTES: endpoint and auth may vary by host
    elif provider == "mistral":
        headers = {"Authorization": f"Bearer {settings.mistral_api_key}"}
        response = requests.post(
            "https://api.together.xyz/v1/embeddings",
            headers=headers,
            json={"model": settings.mistral_embedding_model, "input": query}
        )
        return response.json()["data"][0]["embedding"]

    # ─── Unsupported provider fallback ──────────────────────────────────────────
    else:
        raise ValueError(f"Unsupported EMBEDDING_PROVIDER: {provider}")

# ─────────────────────────────────────────────────────────────
# 🔌 DATABASE CONNECTION
# ─────────────────────────────────────────────────────────────


def get_db_connection(db_config: dict):
    """
    Connect to the Postgres database.

    Args:
        db_config (dict): DB credentials

    Returns:
        psycopg2 connection object
    """
    return psycopg2.connect(**db_config)

# ─────────────────────────────────────────────────────────────
# 🔍 MAIN RETRIEVAL FUNCTION
# ─────────────────────────────────────────────────────────────


@opik.track
def retrieve_top_k_chunks(query: str, top_k: int, db_config: dict) -> List[Dict]:
    """
    Retrieve the top-k most relevant document chunks by embedding the query and using pgvector similarity search.

    Args:
        query (str): Natural language input.
        top_k (int): Number of results to return.
        db_config (dict): Database credentials.

    Returns:
        List[Dict]: Top-k chunks with associated metadata.
    """
    # Generate the query embedding
    query_embedding = embed_query(query)

    # Convert to list if needed (some providers return np arrays)
    if hasattr(query_embedding, "tolist"):
        query_embedding = query_embedding.tolist()

    # Connect to DB and execute cosine similarity search
    conn = get_db_connection(db_config)
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
        {"id": row[0], "title": row[1],
            "chunk": row[2], "similarity_score": row[3]}
        for row in rows
    ]

    cursor.close()
    conn.close()
    return results