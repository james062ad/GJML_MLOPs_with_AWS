import pytest
from server.src.services.generation_service import generate_response


def test_generate_response_basic(
    mock_query, mock_chunks, mock_config, mock_generate_response
):
    """Test the basic functionality of the generate_response function."""
    mock_generate_response.return_value = {
        "response": "Here is information about perovskites: They are used in solar cells.",
        "response_tokens_per_second": None
    }

    response = generate_response(mock_query, mock_chunks, **mock_config)

    assert isinstance(response, dict)
    assert "response" in response
    assert "query" in response
    assert "context" in response
    assert "perovskites" in response["response"]
    assert "solar cells" in response["response"]


def test_generate_response_empty_chunks(
    mock_query, mock_config, mock_generate_response
):
    """Test generate_response with no document chunks."""
    mock_generate_response.return_value = {
        "response": "No relevant information found for perovskites in solar cells.",
        "response_tokens_per_second": None
    }

    response = generate_response(mock_query, [], **mock_config)

    assert isinstance(response, dict)
    assert "response" in response
    assert "No relevant information found" in response["response"]


def test_generate_response_high_temperature(
    mock_query, mock_chunks, mock_generate_response
):
    """Test generate_response with high temperature."""
    mock_generate_response.return_value = {
        "response": "Perovskites might revolutionize solar cells with surprising applications.",
        "response_tokens_per_second": None
    }

    response = generate_response(
        mock_query, mock_chunks, max_tokens=150, temperature=1.5)

    assert isinstance(response, dict)
    assert "response" in response
    assert isinstance(response["response"], str)


def test_generate_response_long_query(mock_chunks, mock_generate_response):
    """Test generate_response with a very long query string."""
    long_query = "Perovskites " * 100

    mock_generate_response.return_value = {
        "response": "Perovskites are materials used in solar cells.",
        "response_tokens_per_second": None
    }

    response = generate_response(
        long_query, mock_chunks, max_tokens=150, temperature=0.7)

    assert isinstance(response, dict)
    assert "response" in response
    assert "Perovskites" in response["response"]


def test_generate_response_with_multiple_chunks(
    mock_query, mock_chunks, mock_generate_response
):
    """Test generate_response with multiple document chunks."""
    mock_generate_response.return_value = {
        "response": (
            "Perovskites are used in solar cells and have unique properties. "
            "Their efficiency has recently improved."
        ),
        "response_tokens_per_second": None
    }

    response = generate_response(
        mock_query, mock_chunks, max_tokens=150, temperature=0.7)

    assert isinstance(response, dict)
    assert "response" in response
    assert "used in solar cells" in response["response"]
    assert "unique properties" in response["response"]
    assert "efficiency has recently improved" in response["response"]
