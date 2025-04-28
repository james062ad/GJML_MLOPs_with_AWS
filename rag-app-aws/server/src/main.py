"""
This is the main entry point for the backend application. This will define and instantiate the FastAPI server
that uses the controllers, models, and services defined in the rest of the sub-repo.

For development purposes, this will run on localhost:8000
"""

# server/src/main.py

from fastapi import FastAPI
from contextlib import asynccontextmanager
from controllers import retrieval, health_check, generation
from sentence_transformers import SentenceTransformer
from server.src.config import get_settings  # ✅ Correct lazy import
import opik

# Async context manager to load in models I want to keep in memory for the app to use.


@asynccontextmanager
async def lifespan_context(app: FastAPI):
    """
    Lifespan context to manage the embedding model across the app.
    """
    print("Spinning up lifespan context...")

    print("Configure opik...")
    opik.configure()

    print("Loading embedding model...")
    embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

    # Optionally load settings here if you need during lifespan
    settings = get_settings()
    print(f"Environment loaded: {settings.environment}")

    try:
        yield {
            "embedding_model": embedding_model
        }
    finally:
        print("Cleaning up embedding model...")
        del embedding_model

# Create the FastAPI application
app = FastAPI(lifespan=lifespan_context)

# Include routers
app.include_router(retrieval.router)
app.include_router(health_check.router)
app.include_router(generation.router)


@app.get("/")
async def read_root():
    return {"message": "Welcome to the RAG app!"}
