import pytest
from unittest.mock import patch, MagicMock
import sys
import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from pydantic import SecretStr, AnyHttpUrl
from typing import Optional, Dict, Any

# ─────────────────────────────────────────────────────────────
# ✅ 1. Add root directory to sys.path
# ─────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))

# ─────────────────────────────────────────────────────────────
# ✅ 2. Global mock for OpenAI client before any imports
# ─────────────────────────────────────────────────────────────
class MockOpenAIClient:
    def __init__(self):
        self.chat = self.Chat()
    
    class Chat:
        def completions(self):
            return self
        
        def create(self, **kwargs):
            return {
                "choices": [{
                    "message": {
                        "content": "Here is information about perovskites: They are used in solar cells."
                    }
                }]
            }

# Patch the module-level client in generation_service.py
openai_patcher = patch("server.src.services.generation_service.openai_client", MockOpenAIClient())
openai_patcher.start()

# ─────────────────────────────────────────────────────────────
# ✅ 3. Global mock for SentenceTransformer before any imports
# ─────────────────────────────────────────────────────────────
mock_model = MagicMock()
mock_model.encode.return_value = [[0.1] * 384]  # Simulate 384-dim vector
patcher = patch("sentence_transformers.SentenceTransformer",
                return_value=mock_model)
patcher.start()

# ─────────────────────────────────────────────────────────────
# ✅ 4. Fixture: patch get_embedding_model to return mock
# ─────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def mock_sentence_transformer():
    with patch("server.src.services.retrieval_service.get_embedding_model", return_value=mock_model):
        yield mock_model

# ─────────────────────────────────────────────────────────────
# ✅ 5. Fixture: patch AWS credential fetch
# ─────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def mock_aws_credentials():
    mock_credentials = {
        "access_key": "test-access-key",
        "secret_key": "test-secret-key",
        "session_token": "test-session-token"
    }
    with patch("server.src.services.aws_refresh_service.CredentialStore.get_credentials", return_value=mock_credentials):
        yield

# ─────────────────────────────────────────────────────────────
# ✅ 6. Fixture: patch boto3 Bedrock client
# ─────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def mock_bedrock_client():
    mock_client = MagicMock()
    mock_client.invoke_model.return_value = {
        "body": MagicMock(read=lambda: '{"results": [{"outputText": "test response"}]}')
    }
    with patch("boto3.client", return_value=mock_client):
        yield mock_client

# ─────────────────────────────────────────────────────────────
# ✅ 7. Fixture: safely patch config.settings (NO class override)
# ─────────────────────────────────────────────────────────────


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
        
        # Model settings - Force OpenAI only
        llm_provider: str = "openai"
        embedding_provider: str = "openai"
        temperature: float = 0.7
        top_p: float = 0.9
        max_tokens: int = 1000
        
        # OpenAI settings
        openai_api_key: str = "test-key"
        openai_model: str = "gpt-3.5-turbo"
        openai_embedding_model: str = "text-embedding-ada-002"
        
        # AWS settings - Disabled
        aws_region: str = "us-east-1"
        aws_access_key_id: SecretStr = SecretStr("test-key")
        aws_secret_access_key: SecretStr = SecretStr("test-secret")
        aws_session_token: Optional[SecretStr] = None
        bedrock_model_id: str = "test-model"
        bedrock_embedding_model_id: str = "test-embedding-model"
        
        # Opik settings
        opik_api_key: str = "test-key"
        opik_workspace: str = "test-workspace"
        opik_project_name: str = "rag-app-test"

        # RAG config
        rag_config: Dict[str, Any] = {
            "providers": {
                "enabled": ["openai"],
                "disabled": ["ollama", "huggingface", "anthropic", "cohere"]#, "bedrock"]
            }
        }

    test_settings = TestSettings()
    monkeypatch.setattr("server.src.config.settings", test_settings)
    return test_settings

# ─────────────────────────────────────────────────────────────
# ✅ 8. DB setup: create papers table and insert sample data
# ─────────────────────────────────────────────────────────────


@pytest.fixture
def db_config():
    return {
        "dbname": "test_db",
        "user": "test_user",
        "password": "test_password",
        "host": "localhost",
        "port": "5432",
    }


@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    return {
        "max_tokens": 1000,
        "temperature": 0.7
    }

@pytest.fixture(autouse=True)
def setup_test_database(db_config):
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
        # Create a proper 384-dimensional vector
        embedding_vector = [0.1] * 384
        embedding_str = f"ARRAY{embedding_vector}::vector(384)"
        cursor.execute(f"""
            INSERT INTO papers (title, chunk, embedding)
            VALUES 
                ('Test Paper 1', 'Perovskite materials are used in solar cells.', {embedding_str}),
                ('Test Paper 2', 'Perovskites have unique electronic properties.', {embedding_str}),
                ('Test Paper 3', 'The efficiency of perovskite solar cells has improved.', {embedding_str})
            ON CONFLICT DO NOTHING;
        """)
        conn.commit()
    except Exception as e:
        print(f"❌ Error setting up test database: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

# ─────────────────────────────────────────────────────────────
# ✅ 8. Cleanup global patches
# ─────────────────────────────────────────────────────────────


def pytest_sessionfinish(session, exitstatus):
    patcher.stop()
    openai_patcher.stop()

@pytest.fixture
def mock_query():
    """Mock query for testing."""
    return "What are perovskites?"

@pytest.fixture
def mock_chunks():
    """Mock document chunks for testing."""
    return [
        {
            "id": 1,
            "title": "Test Paper 1",
            "chunk": "Perovskite materials are used in solar cells.",
            "similarity_score": 0.9
        },
        {
            "id": 2,
            "title": "Test Paper 2",
            "chunk": "Perovskites have unique electronic properties.",
            "similarity_score": 0.8
        }
    ]

@pytest.fixture
def mock_generate_response():
    """Mock OpenAI response for testing."""
    with patch("server.src.services.generation_service.generate_response") as mock:
        mock.return_value = {
            "response": "Perovskites are materials used in solar cells.",
            "response_tokens_per_second": None
        }
        yield mock
