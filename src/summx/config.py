import os
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from pydantic import Field, ConfigDict
from pydantic_settings import BaseSettings

# Load .env file from the project root or parent directories
load_dotenv()


class SummXConfig(BaseSettings):
    """
    Central configuration for the SummX application, loaded from environment variables.
    """

    # --- API Keys ---
    openai_api_key: Optional[str] = Field(None, alias="OPENAI_API_KEY")
    groq_api_key: Optional[str] = Field(None, alias="GROQ_API_KEY")

    # --- MCP Server Configuration ---
    mcp_arxiv_command: str = Field(
        "uv tool run arxiv-mcp-server", alias="MCP_ARXIV_COMMAND"
    )
    mcp_arxiv_storage_path: Path = Field(
        Path.home() / ".summx" / "papers", alias="MCP_ARXIV_STORAGE_PATH"
    )

    # --- Default LLM Models ---
    planner_provider: str = Field("openai", alias="PLANNER_PROVIDER")
    planner_model: str = Field("gpt-4o-mini", alias="PLANNER_MODEL")
    summarizer_provider: str = Field("groq", alias="SUMMARIZER_PROVIDER")
    summarizer_model: str = Field(
        "llama3-8b-8192", alias="SUMMARIZER_MODEL"
    )

    model_config = ConfigDict(
        case_sensitive=False,
        env_file=None,  # Explicitly disable .env file loading for tests
        extra="ignore",
    )


# Singleton instance of the configuration
_config_instance: Optional[SummXConfig] = None


def load_config() -> SummXConfig:
    """
    Loads the application configuration from environment variables and returns a singleton instance.

    This function ensures that config is loaded only once.
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = SummXConfig()
    return _config_instance
