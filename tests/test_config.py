import os
from pathlib import Path
from unittest.mock import patch

import pytest
from summx.config import SummXConfig, load_config

def test_load_config_defaults():
    """Tests that the config loads with default values when no env vars are set."""
    with patch.dict(os.environ, {}, clear=True):
        config = load_config()
        assert isinstance(config, SummXConfig)
        assert config.openai_api_key is None
        assert config.groq_api_key is None
        assert config.planner_provider == "openai"
        assert config.planner_model == "gpt-4o-mini"
        assert config.summarizer_provider == "groq"
        assert config.summarizer_model == "llama3-8b-8192"
        assert config.paper_source == "api"
        assert config.mcp_arxiv_command is None
        assert config.mcp_arxiv_storage_path is None


def test_load_config_with_env_vars():
    """Tests that environment variables correctly override default config values."""
    mock_env = {
        "OPENAI_API_KEY": "test_openai_key",
        "GROQ_API_KEY": "test_groq_key",
        "PLANNER_MODEL": "gpt-4-turbo",
        "PAPER_SOURCE": "mcp",
        "MCP_ARXIV_COMMAND": "test command",
    }
    with patch.dict(os.environ, mock_env, clear=True):
        config = load_config()
        assert config.openai_api_key == "test_openai_key"
        assert config.groq_api_key == "test_groq_key"
        assert config.planner_model == "gpt-4-turbo"
        assert config.paper_source == "mcp"
        assert config.mcp_arxiv_command == "test command"


def test_load_config_is_singleton():
    """Tests that load_config returns the same instance on subsequent calls."""
    with patch.dict(os.environ, {}, clear=True):
        config1 = load_config()
        config2 = load_config()
        assert config1 is config2