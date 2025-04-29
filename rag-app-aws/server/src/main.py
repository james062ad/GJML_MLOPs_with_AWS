"""
This is the main entry point for the backend application, this will define and instantiate the FastAPI server
that uses the controllers, models and services defined in the rest of the sub-repo.

For development purposes this will run on localhost:8000
"""

# server/src/main.py
from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
from controllers import retrieval, health_check, generation
from sentence_transformers import SentenceTransformer
from server.src.config import Settings
import opik
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Async context manager to load in models I want to keep in memory for the app to use.
@asynccontextmanager
async def lifespan_context(app: FastAPI):
    """
    Lifespan context to manage the embedding model across the app.
    """
    print("Spinning up lifespan context...")

    # Try to configure OPIK, but don't fail if it's not available
    try:
        print("Configuring OPIK...")
        opik.configure()
        print("OPIK configured successfully")
    except Exception as e:
        logger.warning(f"OPIK configuration failed (this is okay in test environment): {str(e)}")

    print("Loading embedding model...")
    embedding_model = SentenceTransformer("all-MiniLM-L6-v2")  # Load the model

    # Use the global settings instance
    print(f"Environment loaded: {Settings.environment}")

    try:
        yield {
            "embedding_model": embedding_model
        }  # Pass the model as part of the app state
    finally:
        print("Cleaning up embedding model...")
        del embedding_model  # Optionally clean up if necessary


app = FastAPI(lifespan=lifespan_context)

# Include routers
app.include_router(retrieval.router)
app.include_router(health_check.router)
app.include_router(generation.router)


@app.get("/")
async def read_root():
    return {"message": "Welcome to the RAG app!"}
