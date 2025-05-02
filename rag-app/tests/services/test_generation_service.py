# example_prompts = ["tell me about quantum criticality for perovskites?",
#                    "what materials are often used along with perovskites?",
#                    "what electronic structure phenomena are important in recent perovskite papers?",
#                    "do any of the papers you know about mention band gaps of perovskites?"
#                    ]

import pytest
from typing import Dict, Union
from server.src.services.generation_service import generate_response

def test_generate_response_basic(
    mock_query, mock_chunks, mock_config, mock_generate_response
):
    """Test the basic functionality of the generate_response function."""
    mock_generate_response.return_value = {
        "response": "Here is information about perovskites: They are used in solar cells.",
        "response_tokens_per_second": None
    }

    # Call the function under test
    response = generate_response(mock_query, mock_chunks, **mock_config)

    # Assertions
    assert isinstance(response, dict), "Response should be a Dict."
    assert "response" in response, "Response should contain 'response' key."
    assert "query" in response, "Response should contain 'query' key."
    assert "context" in response, "Response should contain 'context' key."
    assert "perovskites" in response["response"], "Response should contain relevant query content."
    assert "solar cells" in response["response"], "Response should refer to context from retrieved chunks."


def test_generate_response_empty_chunks(
    mock_query, mock_config, mock_generate_response
):
    """Test the generate_response function with an empty list of chunks."""
    mock_generate_response.return_value = {
        "response": "No relevant information found for perovskites in solar cells.",
        "response_tokens_per_second": None
    }

    # Call the function with an empty list of chunks
    response = generate_response(mock_query, [], **mock_config)

    # Assertions
    assert isinstance(response, dict), "Response should be a Dict."
    assert "response" in response, "Response should contain 'response' key."
    assert "No relevant information found" in response["response"], "Should indicate no information found."


def test_generate_response_high_temperature(
    mock_query, mock_chunks, mock_generate_response
):
    """Test the generate_response function with a high temperature setting."""
    mock_generate_response.return_value = {
        "response": "Perovskites might revolutionize solar cells with surprising applications.",
        "response_tokens_per_second": None
    }

    # Call the function with a high temperature setting
    response = generate_response(
        mock_query, mock_chunks, max_tokens=150, temperature=1.5
    )

    # Assertions
    assert isinstance(response, dict), "Response should be a Dict."
    assert "response" in response, "Response should contain 'response' key."
    assert len(response["response"].split()) <= 150, "Response should respect the max_tokens limit."


def test_generate_response_long_query(mock_chunks, mock_generate_response):
    """Test generate_response with a long query string"""
    # Simulate a long query by repeating the word 'Perovskites'
    long_query = "Perovskites " * 100

    mock_generate_response.return_value = {
        "response": "Perovskites are materials used in solar cells.",
        "response_tokens_per_second": None
    }

    # Call the generate_response function with the long query
    response = generate_response(
        long_query, mock_chunks, max_tokens=150, temperature=0.7
    )

    # Assertions
    assert isinstance(response, dict), "Response should be a Dict."
    assert "response" in response, "Response should contain 'response' key."
    assert "Perovskites" in response["response"], "Response should handle long query without error."
    assert len(response["response"].split()) <= 150, "Response should not exceed max_tokens."


def test_generate_response_with_multiple_chunks(
    mock_query, mock_chunks, mock_generate_response
):
    """Test generate_response with multiple chunks."""
    mock_generate_response.return_value = {
        "response": "Perovskites are used in solar cells and have unique properties. Their efficiency has recently improved.",
        "response_tokens_per_second": None
    }

    # Call the function with multiple chunks
    response = generate_response(
        mock_query, mock_chunks, max_tokens=150, temperature=0.7
    )

    # Assertions
    assert isinstance(response, dict), "Response should be a Dict."
    assert "response" in response, "Response should contain 'response' key."
    assert "used in solar cells" in response["response"]
    assert "unique properties" in response["response"]
    assert "efficiency has recently improved" in response["response"]
