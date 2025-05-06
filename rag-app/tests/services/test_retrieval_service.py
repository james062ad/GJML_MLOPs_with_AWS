import pytest
from server.src.services.retrieval_service import retrieve_top_k_chunks
from unittest.mock import patch, MagicMock
import numpy as np

def test_retrieve_top_k_chunks(db_config):
    """Test the retrieval service with mock embeddings."""
    # Mock query and top_k value
    query = "perovskite"
    top_k = 5

    # Create a mock for the entire SentenceTransformer module
    mock_model = MagicMock()
    mock_model.encode.return_value = np.array([0.1] * 384)  # Create a 384-dimensional vector
    
    # Mock the entire module to avoid loading the real model
    with patch("sentence_transformers.SentenceTransformer", return_value=mock_model):
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
