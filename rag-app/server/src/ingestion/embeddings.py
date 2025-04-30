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

# ─────────────────────────────────────────────────────────────
# ✂️ Chunk text into overlapping segments
# ─────────────────────────────────────────────────────────────


def chunk_text(text: str, max_length: int = 512, overlap: int = 50) -> List[str]:
    """
    Chunk the text into smaller pieces with some overlap between chunks.
    
    Args:
        text (str): The text to chunk.
        max_length (int): The maximum number of tokens in each chunk.
        overlap (int): The number of overlapping tokens between adjacent chunks.
        
    Returns:
        List[str]: A list of text chunks with the specified overlap.
    """
    words = text.split()
    chunks = []

    # Ensure the overlap is smaller than max_length
    if overlap >= max_length:
        raise ValueError("Overlap must be smaller than the maximum chunk length.")

    # Slide through the text with a window that overlaps
    start = 0
    while start < len(words):
        end = min(start + max_length, len(words))
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        # Move the window by max_length - overlap to create overlap between chunks
        start += max_length - overlap

    return chunks

# ─────────────────────────────────────────────────────────────
# 🧠 Generate embeddings from chunks (provider aware)
# ─────────────────────────────────────────────────────────────


def generate_embeddings(text_chunks: List[str]) -> List[List[float]]:
    """
    Generate embeddings for a list of text chunks.
    
    Args:
        text_chunks (List[str]): The list of text chunks.

    Supports:
    - sentence-transformer (local)
    - openai
    - bedrock
    - huggingface
    - cohere

    Returns:
        List[List[float]]: A list of embeddings (one embedding per chunk).
    """
# Original code
#     embeddings = model.encode(text_chunks, convert_to_tensor=False)

# Generalising for multiple providers
    # Check if the model is loaded
    if settings.embedding_provider == "sentence-transformer":
        return model.encode(text_chunks, convert_to_tensor=False)
    # OpenAI API
    elif settings.embedding_provider == "openai":
        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json"
        }
        url = "https://api.openai.com/v1/embeddings"
        embeddings = []
        for chunk in text_chunks:
            data = {
                "input": chunk,
                "model": settings.openai_embedding_model
            }
            response = requests.post(url, headers=headers, json=data)
            embeddings.append(response.json()["data"][0]["embedding"])
        return embeddings
    # Bedrock API
    elif settings.embedding_provider == "bedrock":
        import boto3
        client = boto3.client(
            "bedrock-runtime", region_name=settings.aws_region)
        embeddings = []
        for chunk in text_chunks:
            response = client.invoke_model(
                modelId=settings.bedrock_embedding_model_id,
                body=json.dumps({"inputText": chunk}),
                contentType="application/json",
                accept="application/json"
            )
            embedding = json.loads(response["body"].read())["embedding"]
            embeddings.append(embedding)
        return embeddings
    # Hugging Face API
    elif settings.embedding_provider == "huggingface":
        headers = {"Authorization": f"Bearer {settings.huggingface_api_key}"}
        embeddings = []
        for chunk in text_chunks:
            response = requests.post(
                f"https://api-inference.huggingface.co/pipeline/feature-extraction/{settings.huggingface_model}",
                headers=headers,
                json={"inputs": chunk}
            )
            embeddings.append(response.json()[0])
        return embeddings
    # Cohere API
    elif settings.embedding_provider == "cohere":
        headers = {"Authorization": f"Bearer {settings.cohere_api_key}"}
        embeddings = []
        for chunk in text_chunks:
            response = requests.post(
                "https://api.cohere.ai/v1/embed",
                headers=headers,
                json={"texts": [chunk]}
            )
            embeddings.append(response.json()["embeddings"][0])
        return embeddings
        
    else:
        raise ValueError(
            f"Embedding provider not supported: {settings.embedding_provider}")

# ─────────────────────────────────────────────────────────────
# 🔁 Process a list of papers (chunk + embed)
# ─────────────────────────────────────────────────────────────


def process_papers(papers: List[dict], chunk_size: int = 512, overlap: int = 50) -> List[dict]:
    """
    Process each paper by chunking the summary and embedding the chunks.

    Args:
        papers (List[dict]): List of papers with title and summary.
        chunk_size (int): Maximum number of tokens per chunk.
        overlap (int): Number of overlapping tokens between chunks.
        
    Returns:
        List[dict]: Processed papers including chunks and embeddings.
    """
    processed_papers = []

    for paper in papers:
        title = paper.get("title")
        summary = paper.get("summary")

        # Step 1: Chunk the summary into smaller chunks
        chunks = chunk_text(summary, max_length=chunk_size, overlap=overlap)

        # Step 2: Generate embeddings for each chunk
        embeddings = generate_embeddings(chunks)

        processed_papers.append({
            "title": title,
            "summary": summary,
            "chunks": chunks,
            "embeddings": embeddings
        })

    return processed_papers

# ─────────────────────────────────────────────────────────────
# 🚀 Full ingestion pipeline runner
# ─────────────────────────────────────────────────────────────


def run_pipeline(json_dir: str, output_file: str, chunk_size: int = 512, overlap: int = 50):
    """
    Executes the ingestion pipeline: read → chunk → embed → save.

    Args:
        json_dir (str): Directory containing paper JSONs.
        output_file (str): Path to save output JSON file.

    Returns:
        List[dict]: Processed papers.
    """
    # Step 1: Read JSON files
    papers = read_json_files(json_dir)

    # Step 2: Process papers (chunking and embedding)
    processed_papers = process_papers(
        papers, chunk_size=chunk_size, overlap=overlap)
    print(f"✅ Successfully processed {len(processed_papers)} papers.")

    # Step 3: Save the processed papers with embeddings
    save_processed_papers_to_file(processed_papers, output_file)
    print("🔍 Sample output:", json.dumps(processed_papers[0], indent=2)[:1000])
    print(f"✅ Successfully saved to {output_file}")

    return processed_papers


# ─────────────────────────────────────────────────────────────
# 🧪 CLI entry point
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Example usage: process and save embeddings to disk
    run_pipeline(
        json_dir=DATA_PATH,
        output_file=os.path.join(DATA_PATH, "processed_papers.json")
    )
