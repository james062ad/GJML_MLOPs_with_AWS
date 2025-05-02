import os
import json
import requests
from typing import Optional
import psycopg2
from psycopg2.extras import execute_values
import boto3  # always import at top

from server.src.config import settings
from server.src.ingestion.embeddings import process_papers
from server.src.ingestion.utils import read_json_files, save_processed_papers_to_file
import opik

def detect_embedding_dim(example_text: str = "test") -> int:
    provider = settings.embedding_provider

    # 💬 TEMPORARY DEBUG: print the active AWS credentials
    try:
        session = boto3.Session()
        creds = session.get_credentials().get_frozen_credentials()
        print("🧠 DEBUG - boto3 credentials:", {
            "access_key": creds.access_key,
            "secret_key": f"{creds.secret_key[:4]}...{creds.secret_key[-4:]}",
            "token": creds.token
        })
    except Exception as debug_err:
        print("❌ Failed to inspect boto3 credentials:", debug_err)

    if provider == "sentence-transformer":
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("all-MiniLM-L6-v2")
        return len(model.encode(example_text))

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

    elif provider == "bedrock":
        # ✅ FORCE credentials from .env to avoid any session_token leaks
        client = boto3.client(
            "bedrock-runtime",
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id.get_secret_value(),
            aws_secret_access_key=settings.aws_secret_access_key.get_secret_value()
        )
        response = client.invoke_model(
            modelId=settings.bedrock_embedding_model_id,
            body=json.dumps({"inputText": example_text}),
            contentType="application/json",
            accept="application/json"
        )
        return len(json.loads(response["body"].read())["embedding"])

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
        return len(result["embedding"]["value"])

    raise ValueError(f"Unsupported embedding provider: {provider}")

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

@opik.track
def rebuild_vector_db(
    json_dir: str,
    output_file: Optional[str] = None,
    chunk_size: int = 512,
    overlap: int = 50
):
    print(f"📂 Rebuilding vector DB from: {json_dir}")
    dim = detect_embedding_dim()
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
                values.append((entry["title"], entry["summary"], chunk, embedding))

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
