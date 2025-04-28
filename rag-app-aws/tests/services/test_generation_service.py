# example_prompts = ["tell me about quantum criticality for perovskites?",
#                    "what materials are often used along with perovskites?",
#                    "what electronic structure phenomena are important in recent perovskite papers?",
#                    "do any of the papers you know about mention band gaps of perovskites?"
#                    ]

import pytest
from unittest.mock import patch
from typing import Dict, Union

from server.src.services.generation_service import generate_response

# Leverages the mock's from conftest.py


@pytest.mark.asyncio
@patch('server.src.services.generation_service.call_llm')
async def test_generate_response_basic(mock_call_llm, mock_query, mock_chunks, mock_config):
    """Test the basic functionality of the generate_response function."""
    # Mock the response from the LLM
    mock_call_llm.return_value = {
        "response": "Here is information about perovskites: They are used in solar cells.",
        "eval_count": 100,
        "eval_duration": 0.1,
    }

    # Call the function under test
    response = await generate_response(mock_query, mock_chunks, **mock_config)

    # Assertions
    assert isinstance(response, dict), "Response should be a dictionary."
    assert "perovskites" in response["response"].lower()
    assert "solar cells" in response["response"].lower()


@pytest.mark.asyncio
@patch('server.src.services.generation_service.call_llm')
async def test_generate_response_empty_chunks(mock_call_llm, mock_query, mock_config):
    """Test the generate_response function with an empty list of chunks."""
    mock_call_llm.return_value = {
        "response": "No relevant information found for perovskites in solar cells."
    }

    # Call the function with an empty list of chunks
    response = await generate_response(mock_query, [], **mock_config)

    # Assertions
    assert isinstance(response, dict)
    assert "no relevant information" in response["response"].lower()


@pytest.mark.asyncio
@patch('server.src.services.generation_service.call_llm')
async def test_generate_response_high_temperature(mock_call_llm, mock_query, mock_chunks):
    """Test the generate_response function with a high temperature setting."""
    mock_call_llm.return_value = {
        "response": "Perovskites might revolutionize solar cells with surprising applications."
    }

    # Call the function with a high temperature setting
    response = await generate_response(mock_query, mock_chunks, max_tokens=150, temperature=1.5)

    # Assertions
    assert isinstance(response, dict)
    assert "perovskites" in response["response"].lower()


@pytest.mark.asyncio
@patch('server.src.services.generation_service.call_llm')
async def test_generate_response_long_query(mock_call_llm, mock_chunks):
    """Test generate_response with a long query string."""
    long_query = "Perovskites " * 100

    mock_call_llm.return_value = {
        "response": "Perovskites are materials used in solar cells."
    }

    response = await generate_response(long_query, mock_chunks, max_tokens=150, temperature=0.7)

    # Assertions
    assert "perovskites" in response["response"].lower()
    assert len(response["response"].split()) <= 150


@pytest.mark.asyncio
@patch('server.src.services.generation_service.call_llm')
async def test_generate_response_with_multiple_chunks(mock_call_llm, mock_query, mock_chunks):
    """Test generate_response with multiple chunks."""
    mock_call_llm.return_value = {
        "response": "Perovskites are used in solar cells and have unique properties. Their efficiency has recently improved."
    }

    response = await generate_response(mock_query, mock_chunks, max_tokens=150, temperature=0.7)

    # Assertions
    assert "solar cells" in response["response"].lower()
    assert "unique properties" in response["response"].lower()
    assert "efficiency" in response["response"].lower()
