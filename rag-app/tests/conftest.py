import pytest
from unittest.mock import patch, MagicMock
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from pydantic_settings import BaseSettings
from pydantic import Field, SecretStr, AnyHttpUrl
from typing import Optional, Dict, Any

# Mock the Bedrock client factory
@pytest.fixture(autouse=True)
def mock_bedrock_client():
    """Mock the Bedrock client factory to avoid AWS calls during testing."""
    mock_client = MagicMock()
    with patch("server.src.utils.bedrock_client_factory.get_bedrock_client", return_value=mock_client):
        yield mock_client

# Import after mock is defined to avoid circular imports
from server.src.services.generation_service import generate_response, call_llm

@pytest.fixture(autouse=True)
def mock_settings(monkeypatch):
    """Mock the settings with test values."""
    from server.src.config import Settings
    
    class TestSettings(Settings):
        class Config:
            validate_assignment = True
            arbitrary_types_allowed = True
            
        # Override the parent class to provide default values for testing
        environment: str = "test"
        app_name: str = "rag-app"
        debug: bool = True
        
        # Database settings
        postgres_host: str = "localhost"
        postgres_db: str = "test_db"
        postgres_user: str = "test_user"
        postgres_password: str = "test_password"
        postgres_port: int = 5432
        
        # API settings
        arxiv_api_url: AnyHttpUrl = "https://export.arxiv.org/api/query"
        data_path: str = "./data"
        
        # Model settings
        llm_provider: str = "openai"
        embedding_provider: str = "sentence-transformer"
        temperature: float = 0.7
        top_p: float = 0.9
        max_tokens: int = 1000
        
        # OpenAI settings
        openai_api_key: str = "test-key"
        openai_model: str = "gpt-3.5-turbo"
        openai_embedding_model: str = "text-embedding-ada-002"
        
        # AWS settings
        aws_region: str = "us-east-1"
        aws_access_key_id: SecretStr = SecretStr("test-key")
        aws_secret_access_key: SecretStr = SecretStr("test-secret")
        aws_session_token: Optional[SecretStr] = None
        bedrock_model_id: str = "test-model"
        bedrock_embedding_model_id: str = "test-embedding-model"
        
        # Ollama settings
        ollama_url: AnyHttpUrl = "http://localhost:11434"
        ollama_model: str = "llama2"
        ollama_embedding_model: str = "llama2"
        
        # Opik settings
        opik_api_key: str = "test-key"
        opik_workspace: str = "test-workspace"
        opik_project_name: str = "rag-app-test"

        # RAG config
        rag_config: Dict[str, Any] = {}

    test_settings = TestSettings()
    monkeypatch.setattr("server.src.config.settings", test_settings)
    return test_settings


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
    conn = psycopg2.connect(**db_config)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    
    try:
        cursor = conn.cursor()
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS papers (
            id SERIAL PRIMARY KEY,
            title TEXT,
            chunk TEXT,
            embedding vector(384)
        );
        """)
        
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
