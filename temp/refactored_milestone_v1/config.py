from pydantic_settings import BaseSettings
from pydantic import Field, SecretStr
from typing import Optional  # ✅ needed for session_token


class Settings(BaseSettings):
    # ─── Environment ───────────────────────────────────────────
    environment: str = Field(..., env="ENVIRONMENT")
    app_name: str = Field(..., env="APP_NAME")
    debug: bool = Field(..., env="DEBUG")

    # ─── Database ──────────────────────────────────────────────
    postgres_host: str = Field(..., env="POSTGRES_HOST")
    postgres_port: int = 5432
    postgres_db: str = Field(..., env="POSTGRES_DB")
    postgres_user: str = Field(..., env="POSTGRES_USER")
    postgres_password: str = Field(..., env="POSTGRES_PASSWORD")

    # ─── Ingestion ─────────────────────────────────────────────
    arxiv_api_url: str = Field(..., env="ARXIV_API_URL")
    data_path: str = Field(..., env="DATA_PATH")

    # ─── Model Configuration ───────────────────────────────────
    llm_provider: str = Field(..., env="LLM_PROVIDER")
    embedding_provider: str = Field(..., env="EMBEDDING_PROVIDER")
    temperature: float = Field(..., env="TEMPERATURE")
    top_p: float = Field(..., env="TOP_P")
    max_tokens: int = Field(..., env="MAX_TOKENS")

    # ─── OpenAI ────────────────────────────────────────────────
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_model: str = Field(..., env="OPENAI_MODEL")
    openai_embedding_model: str = Field(..., env="OPENAI_EMBEDDING_MODEL")

    # ─── AWS Bedrock ───────────────────────────────────────────
    aws_region: str = Field(..., env="AWS_REGION")
    aws_access_key_id: SecretStr = Field(..., env="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: SecretStr = Field(..., env="AWS_SECRET_ACCESS_KEY")
    aws_session_token: Optional[SecretStr] = Field(
        None, env="AWS_SESSION_TOKEN")  # ✅ now truly optional
    bedrock_model_id: str = Field(..., env="BEDROCK_MODEL_ID")
    bedrock_embedding_model_id: str = Field(...,
                                            env="BEDROCK_EMBEDDING_MODEL_ID")

    # ─── Ollama ───────────────────────────────────────────────
    ollama_url: str = Field(..., env="OLLAMA_URL")
    ollama_model: str = Field(..., env="OLLAMA_MODEL")
    ollama_embedding_model: str = Field(..., env="OLLAMA_EMBEDDING_MODEL")

    # ─── Tracing (Opik) ─────────────────────────────────────────
    opik_api_key: str = Field(..., env="OPIK_API_KEY")
    opik_workspace: str = Field(..., env="OPIK_WORKSPACE")
    opik_project_name: str = Field(..., env="OPIK_PROJECT_NAME")

    rag_config: dict = {}

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()
