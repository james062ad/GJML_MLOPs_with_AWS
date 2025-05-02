import pytest
from server.src.services.retrieval_service import retrieve_top_k_chunks


def test_retrieve_top_k_chunks(db_config):
    """Test the retrieval service with mock embeddings (auto-patched from conftest)."""
    query = "perovskite"
    top_k = 5

    try:
        documents = retrieve_top_k_chunks(query, top_k, db_config)

        assert isinstance(documents, list)
        assert len(documents) <= top_k

        for doc in documents:
            assert "id" in doc
            assert "title" in doc
            assert "chunk" in doc
            assert "similarity_score" in doc
    except Exception as e:
        pytest.fail(f"Test failed with error: {str(e)}")
