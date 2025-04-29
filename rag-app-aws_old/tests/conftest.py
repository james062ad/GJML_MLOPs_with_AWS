import pytest
from server.src.services.generation_service import generate_response, call_llm
from unittest.mock import patch, MagicMock
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


@pytest.fixture(autouse=True)
def mock_sentence_transformer():
    """Mock the SentenceTransformer module to avoid loading the real model during tests."""
    mock_model = MagicMock()
    mock_model.encode.return_value = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    
    with patch("server.src.services.retrieval_service.SentenceTransformer", return_value=mock_model):
        yield


@pytest.fixture
def mock_query():
    """Fixture to provide a sample query for testing."""
    return "Tell me about perovskites in solar cells."


@pytest.fixture
def mock_chunks():
    """Fixture to provide mock retrieved document chunks for generation tests."""
    return [
        {"text": "Perovskite materials are used in solar cells."},
        {"text": "Perovskites have unique electronic properties."},
        {"text": "The efficiency of perovskite solar cells has improved."},
    ]


@pytest.fixture
def mock_config():
    """Fixture for mock configuration settings."""
    return {
        "max_tokens": 150,
        "temperature": 0.7,
    }


@pytest.fixture
def mock_generate_response():
    """Fixture that mocks the LLM generation process in the call_llm function."""
    with patch("server.src.services.generation_service.call_llm") as mock_gen:
        yield mock_gen


@pytest.fixture
def db_config():
    """Fixture for database configuration."""
    return {
        "dbname": "test_db",
        "user": "test_user",
        "password": "test_password",
        "host": "localhost",
        "port": "5432",
    }


@pytest.fixture(autouse=True)
def setup_test_database(db_config):
    """Fixture to set up the test database with required tables."""
    # Connect to the database
    conn = psycopg2.connect(**db_config)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    
    try:
        cursor = conn.cursor()
        
        # Create the pgvector extension if it doesn't exist
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        
        # Create the papers table if it doesn't exist
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS papers (
            id SERIAL PRIMARY KEY,
            title TEXT,
            chunk TEXT,
            embedding vector(384)
        );
        """)
        
        # Insert some test data
        cursor.execute("""
        INSERT INTO papers (title, chunk, embedding)
        VALUES 
            ('Test Paper 1', 'Perovskite materials are used in solar cells.', '[0.1]'::vector(384)),
            ('Test Paper 2', 'Perovskites have unique electronic properties.', '[0.1]'::vector(384)),
            ('Test Paper 3', 'The efficiency of perovskite solar cells has improved.', '[0.1]'::vector(384))
        ON CONFLICT DO NOTHING;
        """)
        
        conn.commit()
    except Exception as e:
        print(f"Error setting up test database: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
