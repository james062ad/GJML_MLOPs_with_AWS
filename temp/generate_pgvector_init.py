import os
import json
import requests
from sentence_transformers import SentenceTransformer
from server.src.config import settings

def detect_embedding_dim() -> int:
    """Generate a dummy embedding and return its dimension length."""
    text = "dimension test"
    provider = settings.embedding_provider

    if provider == "sentence-transformer":
        model = SentenceTransformer("all-MiniLM-L6-v2")
        return len(model.encode(text))

    elif provider == "openai":
        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json"
        }
        response = requests.post(
            "https://api.openai.com/v1/embeddings",
            headers=headers,
            json={"input": text, "model": settings.openai_embedding_model}
        )
        return len(response.json()["data"][0]["embedding"])

    elif provider == "bedrock":
        import boto3
        client = boto3.client("bedrock-runtime", region_name=settings.aws_region)
        response = client.invoke_model(
            modelId=settings.bedrock_embedding_model_id,
            body=json.dumps({"inputText": text}),
            contentType="application/json",
            accept="application/json"
        )
        return len(json.loads(response["body"].read())["embedding"])

    raise ValueError(f"Unsupported provider for dynamic schema: {provider}")

def write_pgvector_sql(dim: int):
    sql = f"""
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS papers (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    chunk TEXT NOT NULL,
    embedding vector({dim})
);
"""
    os.makedirs("init", exist_ok=True)
    with open("init/init_pgvector.sql", "w") as f:
        f.write(sql)
    print(f"✅ init_pgvector.sql created with dimension {dim}")

if __name__ == "__main__":
    dimension = detect_embedding_dim()
    write_pgvector_sql(dimension)
