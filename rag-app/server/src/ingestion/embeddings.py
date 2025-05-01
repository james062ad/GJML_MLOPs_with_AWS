from sentence_transformers import SentenceTransformer
from typing import List
import os
import json
import requests
from server.src.ingestion.utils import read_json_files, save_processed_papers_to_file
from server.src.config import settings
import dotenv

dotenv.load_dotenv()
DATA_PATH = os.getenv('DATA_PATH')

# ─────────────────────────────────────────────────────────────
# 🧠 Load default local model (used only if provider = sentence-transformer)
# ─────────────────────────────────────────────────────────────
model = None
if settings.embedding_provider == "sentence-transformer":
    model = SentenceTransformer('all-MiniLM-L6-v2')


def chunk_text(text: str, max_length: int = 512, overlap: int = 50) -> List[str]:
    words = text.split()
    chunks = []
    if overlap >= max_length:
        raise ValueError(
            "Overlap must be smaller than the maximum chunk length.")
    start = 0
    while start < len(words):
        end = min(start + max_length, len(words))
        chunks.append(" ".join(words[start:end]))
        start += max_length - overlap
    return chunks


def generate_embeddings(text_chunks: List[str]) -> List[List[float]]:
    """
    Dispatch to appropriate embedding provider based on config.
    Supports:
    - sentence-transformer
    - openai
    - bedrock
    - huggingface
    - cohere
    - google (text-embedding-004)
    """
    provider = settings.embedding_provider

    if provider == "sentence-transformer":
        return model.encode(text_chunks, convert_to_tensor=False)

    elif provider == "openai":
        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json"
        }
        url = "https://api.openai.com/v1/embeddings"
        return [
            requests.post(url, headers=headers, json={
                "input": chunk,
                "model": settings.openai_embedding_model
            }).json()["data"][0]["embedding"]
            for chunk in text_chunks
        ]

    elif provider == "bedrock":
        import boto3
        client = boto3.client(
            "bedrock-runtime", region_name=settings.aws_region)
        return [
            json.loads(client.invoke_model(
                modelId=settings.bedrock_embedding_model_id,
                body=json.dumps({"inputText": chunk}),
                contentType="application/json",
                accept="application/json"
            )["body"].read())["embedding"]
            for chunk in text_chunks
        ]

    elif provider == "huggingface":
        headers = {"Authorization": f"Bearer {settings.huggingface_api_key}"}
        return [
            requests.post(
                f"https://api-inference.huggingface.co/pipeline/feature-extraction/{settings.huggingface_model}",
                headers=headers,
                json={"inputs": chunk}
            ).json()[0]
            for chunk in text_chunks
        ]

    elif provider == "cohere":
        headers = {"Authorization": f"Bearer {settings.cohere_api_key}"}
        return [
            requests.post(
                "https://api.cohere.ai/v1/embed",
                headers=headers,
                json={"texts": [chunk]}
            ).json()["embeddings"][0]
            for chunk in text_chunks
        ]

    elif provider == "google":
        # ✅ Google Gemini embedding (text-embedding-004)
        url = f"https://generativelanguage.googleapis.com/v1/models/{settings.google_embedding_model}:embedContent?key={settings.google_api_key}"
        headers = {"Content-Type": "application/json"}
        embeddings = []

        for chunk in text_chunks:
            body = {
                "content": {
                    "parts": [{"text": chunk}]
                }
            }
            response = requests.post(url, headers=headers, json=body)
            result = response.json()

            if "embedding" not in result or "values" not in result["embedding"]:
                print(
                    f"❌ Google error: missing 'embedding.values'. Full response:\n{json.dumps(result, indent=2)}"
                )
                raise ValueError(
                    "Missing 'embedding.values' in Google embedding response")

            embeddings.append(result["embedding"]["values"])

        return embeddings

    else:
        raise ValueError(f"❌ Unsupported embedding provider: {provider}")


def process_papers(papers: List[dict], chunk_size: int = 512, overlap: int = 50) -> List[dict]:
    processed = []
    for paper in papers:
        title = paper.get("title", "Untitled")
        summary = paper.get("summary", "")
        if not summary:
            print(f"⚠️ Skipping empty summary: {title}")
            continue

        chunks = chunk_text(summary, max_length=chunk_size, overlap=overlap)
        if not chunks:
            print(f"⚠️ No chunks for: {title}")
            continue

        try:
            embeddings = generate_embeddings(chunks)
        except Exception as e:
            print(f"❌ Embedding failed for {title}: {e}")
            continue

        if len(chunks) != len(embeddings):
            print(
                f"⚠️ Mismatch: {title} → {len(chunks)} chunks vs {len(embeddings)} embeddings")
            continue

        processed.append({
            "title": title,
            "summary": summary,
            "chunks": chunks,
            "embeddings": embeddings
        })
        print(f"✅ {title}: {len(chunks)} chunks processed")

    print(f"📦 Total valid papers: {len(processed)}")
    return processed


def run_pipeline(json_dir: str, output_file: str, chunk_size: int = 512, overlap: int = 50):
    papers = read_json_files(json_dir)
    processed = process_papers(papers, chunk_size=chunk_size, overlap=overlap)
    print(f"✅ Successfully processed {len(processed)} papers.")
    if processed:
        save_processed_papers_to_file(processed, output_file)
        print("🔍 Sample output:", json.dumps(processed[0], indent=2)[:1000])
        print(f"✅ Saved to {output_file}")
    return processed


if __name__ == "__main__":
    run_pipeline(
        json_dir=DATA_PATH,
        output_file=os.path.join(DATA_PATH, "processed_papers.json")
    )
