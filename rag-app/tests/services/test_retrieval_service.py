import pytest
from server.src.services.retrieval_service import retrieve_top_k_chunks
from dotenv import load_dotenv
import os
from unittest.mock import patch
import numpy as np

# TODO: update to use BaseSettings implementation
load_dotenv()

DATA_PATH = os.getenv("DATA_PATH")

# Database connection configuration
db_config = {
    "dbname": os.environ.get("POSTGRES_DB"),
    "user": os.environ.get("POSTGRES_USER"),
    "password": os.environ.get("POSTGRES_PASSWORD"),
    "host": os.environ.get("POSTGRES_HOST"),
    "port": os.environ.get("POSTGRES_PORT"),
}

# Test function for the retrieval service - your postgres instance needs to be running.
@pytest.mark.asyncio
async def test_retrieve_top_k_chunks(db_config):
    # Mock query and top_k value
    query = "perovskite"
    top_k = 5

    # Mock the embedding model
    with patch("server.src.services.retrieval_service.embedding_model.encode") as mock_encode:
        # Set up the mock to return a fixed embedding
        # Return a numpy array instead of a list to support .tolist() method
        mock_encode.return_value = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
        
        # Call the function
        try:
            documents = retrieve_top_k_chunks(query, top_k, db_config)

            # Assertions
            assert isinstance(documents, list)
            assert len(documents) <= top_k

            for doc in documents:
                assert "id" in doc
                assert "title" in doc
                assert "chunk" in doc
                assert "similarity_score" in doc
        except Exception as e:
            pytest.fail(f"Test failed with error: {str(e)}")
