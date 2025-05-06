import pytest
import numpy as np
from unittest.mock import MagicMock, patch
from server.src.services.retrieval_service import retrieve_top_k_chunks


def test_retrieve_top_k_chunks(db_config):
    query = "perovskite"
    top_k = 5

    mock_model = MagicMock()
    mock_model.encode.return_value = np.array([0.1] * 384)

    with patch("server.src.services.retrieval_service.get_embedding_model", return_value=mock_model):
        documents = retrieve_top_k_chunks(query, top_k, db_config)

        assert isinstance(documents, list)
        assert len(documents) <= top_k

        for doc in documents:
            assert "id" in doc
            assert "title" in doc
            assert "chunk" in doc
            assert "similarity_score" in doc