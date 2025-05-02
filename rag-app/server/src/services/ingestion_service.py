import os
import json
import requests
from typing import Optional
import psycopg2
from psycopg2.extras import execute_values

from server.src.config import settings
from server.src.utils.bedrock_client_factory import get_bedrock_client
from server.src.ingestion.embeddings import process_papers
from server.src.ingestion.utils import read_json_files, save_processed_papers_to_file
import opik

# ─────────────────────────────────────────────────────────────
# 🧠 Detect vector dimension for given embedding provider
# ─────────────────────────────────────────────────────────────


def detect_embedding_dim(example_text: str = "test", override_provider: Optional[str] = None) -> int:
    provider = override_provider or settings.embedding_provider
    print(f"⚙️ Embedding provider → {provider}")

    if provider == "bedrock":
        client = get_bedrock_client()
        response = client.invoke_model(
            modelId=settings.bedrock_embedding_model_id,
            body=json.dumps({"inputText": example_text}),
            contentType="application/json",
            accept="application/json"
        )
        return len(json.loads(response["body"].read())["embedding"])

    elif provider == "openai":
        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json"
        }
        response = requests.post(
            "https://api.openai.com/v1/embeddings",
            headers=headers,
            json={"input": example_text, "model": settings.openai_embedding_model}
        )
        return len(response.json()["data"][0]["embedding"])

    elif provider == "huggingface":
        headers = {"Authorization": f"Bearer {settings.huggingface_api_key}"}
        response = requests.post(
            f"https://api-inference.huggingface.co/pipeline/feature-extraction/{settings.huggingface_model}",
            headers=headers,
            json={"inputs": example_text}
        )
        result = response.json()
        return len(result[0]) if isinstance(result, list) else len(result)

    elif provider == "cohere":
        headers = {"Authorization": f"Bearer {settings.cohere_api_key}"}
        response = requests.post(
            "https://api.cohere.ai/v1/embed",
            headers=headers,
            json={"texts": [example_text]}
        )
        return len(response.json()["embeddings"][0])

    elif provider == "google":
        url = f"https://generativelanguage.googleapis.com/v1/models/{settings.google_embedding_model}:embedContent?key={settings.google_api_key}"
        headers = {"Content-Type": "application/json"}
        body = {
            "content": {
                "parts": [{"text": example_text}]
            }
        }
        response = requests.post(url, headers=headers, json=body)
        result = response.json()

        if "embedding" not in result or "values" not in result["embedding"]:
            print("❌ Google embedding error: full response =",
                  json.dumps(result, indent=2))
            raise ValueError("Missing 'embedding.values' in Google response")

        return len(result["embedding"]["values"])

    raise ValueError(f"Unsupported embedding provider: {provider}")


# ─────────────────────────────────────────────────────────────
# 📐 Write init_pgvector.sql for Postgres vector setup
# ─────────────────────────────────────────────────────────────
def write_pgvector_sql(dim: int, output_file: str = "init/init_pgvector.sql"):
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    sql = f"""
CREATE EXTENSION IF NOT EXISTS vector;

DROP TABLE IF EXISTS papers;

CREATE TABLE IF NOT EXISTS papers (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    chunk TEXT NOT NULL,
    embedding vector({dim})
);
"""
    with open(output_file, "w") as f:
        f.write(sql)
    print(f"✅ Wrote init_pgvector.sql with dimension {dim}")


# ─────────────────────────────────────────────────────────────
# 🔁 End-to-end ingestion & vector DB rebuild
# ─────────────────────────────────────────────────────────────
@opik.track
def rebuild_vector_db(
    json_dir: str,
    output_file: Optional[str] = None,
    chunk_size: int = 512,
    overlap: int = 50
):
    print(f"📂 Rebuilding vector DB from: {json_dir}")
    dim = detect_embedding_dim(override_provider=settings.embedding_provider)
    write_pgvector_sql(dim)

    try:
        papers = read_json_files(json_dir)
        print(f"📄 Papers loaded: {len(papers)}")
        processed = process_papers(papers, chunk_size, overlap)
        print(f"✂️ Processed papers: {len(processed)}")

        db_config = {
            "dbname": settings.postgres_db,
            "user": settings.postgres_user,
            "password": settings.postgres_password,
            "host": settings.postgres_host,
            "port": settings.postgres_port,
        }

        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()

        cursor.execute("DROP TABLE IF EXISTS papers;")
        cursor.execute(f"""
            CREATE TABLE papers (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                summary TEXT NOT NULL,
                chunk TEXT NOT NULL,
                embedding vector({dim})
            );
        """)
        print(f"🧱 Recreated 'papers' table with vector({dim})")

        insert_query = """
        INSERT INTO papers (title, summary, chunk, embedding)
        VALUES %s
        """

        values = []
        for entry in processed:
            for chunk, embedding in zip(entry["chunks"], entry["embeddings"]):
                if hasattr(embedding, "tolist"):
                    embedding = embedding.tolist()
                values.append(
                    (entry["title"], entry["summary"], chunk, embedding))

        execute_values(cursor, insert_query, values)
        conn.commit()
        cursor.close()
        conn.close()
        print(f"✅ Inserted {len(values)} rows into the papers table.")

        if output_file:
            for entry in processed:
                entry["embeddings"] = [
                    emb.tolist() if hasattr(emb, "tolist") else emb
                    for emb in entry["embeddings"]
                ]
            save_processed_papers_to_file(processed, output_file)
            print(f"💾 Saved processed papers to: {output_file}")

    except Exception as e:
        print(f"❌ Ingestion failed: {e}")
        raise
