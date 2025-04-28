from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr
from typing import Optional


class Settings(BaseSettings):
    environment: str = Field(..., env="ENVIRONMENT")
    app_name: str = Field(..., env="APP_NAME")
    debug: bool = Field(..., env="DEBUG")

    postgres_host: str = Field(..., env="POSTGRES_HOST")
    postgres_port: int = 5432
    postgres_db: str = Field(..., env="POSTGRES_DB")
    postgres_user: str = Field(..., env="POSTGRES_USER")
    postgres_password: SecretStr = Field(..., env="POSTGRES_PASSWORD")

    arxiv_api_url: str = Field(..., env="ARXIV_API_URL")
    data_path: str = Field(..., env="DATA_PATH")

    temperature: float = Field(..., env="TEMPERATURE")
    top_p: float = Field(..., env="TOP_P")
    max_tokens: int = Field(..., env="MAX_TOKENS")

    opik_api_key: SecretStr = Field(..., env="OPIK_API_KEY")
    opik_workspace: str = Field(..., env="OPIK_WORKSPACE")
    opik_project_name: str = Field(..., env="OPIK_PROJECT_NAME")

    openai_model: str = Field(..., env="OPENAI_MODEL")
    openai_api_key: SecretStr = Field(..., env="OPENAI_API_KEY")

    aws_region: str = Field(..., env="AWS_REGION")
    aws_access_key_id: SecretStr = Field(..., env="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: SecretStr = Field(..., env="AWS_SECRET_ACCESS_KEY")
    aws_session_token: Optional[SecretStr] = Field(
        None, env="AWS_SESSION_TOKEN")
    bedrock_model_id: str = Field(..., env="BEDROCK_MODEL_ID")
    bedrock_embedding_model_id: str = Field(...,
                                            env="BEDROCK_EMBEDDING_MODEL_ID")

    rag_config: dict = {}

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow"
    )


def get_settings() -> Settings:
    return Settings()
