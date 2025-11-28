import os
from pathlib import Path
from typing import List, Optional, Literal

from pydantic import ConfigDict
from pydantic_settings import BaseSettings



class SummXConfig(BaseSettings):
    """
    Central configuration for the SummX application, loaded from environment variables.
    """

    # --- API Keys ---
    openai_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None

    # --- Paper Source Configuration ---
    paper_source: Literal["api", "mcp"] = "api"
    # The following are for the optional MCP backend
    mcp_arxiv_command: Optional[str] = None
    mcp_arxiv_storage_path: Optional[Path] = None

    # --- Default LLM Models ---
    planner_provider: str = "openai"
    planner_model: str = "gpt-4o-mini"
    summarizer_provider: str = "groq"
    summarizer_model: str = "llama3-8b-8192"

    model_config = ConfigDict(
        case_sensitive=False,
        env_file=".env",
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
