import os
import pytest
from unittest.mock import patch

from summx.config import load_config
from summx.llm import get_llm, LLMClient, DummyLLMClient, OpenAIClient, GroqClient

# Mock API keys for testing
MOCK_ENV = {
    "OPENAI_API_KEY": "fake-openai-key",
    "GROQ_API_KEY": "fake-groq-key",
}

@pytest.mark.asyncio
async def test_dummy_llm_client():
    """Tests that the DummyLLMClient returns its canned response."""
    dummy_client = DummyLLMClient(response="test")
    response = await dummy_client.chat(messages=[])
    assert response == "test"

    default_dummy = get_llm(provider="dummy", config=load_config())
    assert isinstance(default_dummy, DummyLLMClient)
    response = await default_dummy.chat(messages=[])
    assert response == "This is a dummy response."

@patch.dict("os.environ", MOCK_ENV, clear=True)
def test_get_llm_factory_openai():
    """Tests that the factory returns an OpenAIClient when requested."""
    config = load_config()
    client = get_llm(provider="openai", config=config)
    assert isinstance(client, OpenAIClient)
    assert client.model == config.planner_model

@patch.dict("os.environ", MOCK_ENV, clear=True)
def test_get_llm_factory_groq():
    """Tests that the factory returns a GroqClient when requested."""
    config = load_config()
    client = get_llm(provider="groq", config=config)
    assert isinstance(client, GroqClient)
    assert client.model == config.summarizer_model

@patch.dict("os.environ", MOCK_ENV, clear=True)
def test_get_llm_factory_override_model():
    """Tests that the model can be overridden in the factory."""
    config = load_config()
    client = get_llm(provider="openai", config=config, model_name="test-model-override")
    assert isinstance(client, OpenAIClient)
    assert client.model == "test-model-override"

def test_get_llm_factory_missing_key():
    """Tests that the factory raises a ValueError if an API key is missing."""
    with patch.dict(os.environ, {}, clear=True):
        config = load_config()
        with pytest.raises(ValueError, match="OPENAI_API_KEY is not set."):
            get_llm(provider="openai", config=config)

        with pytest.raises(ValueError, match="GROQ_API_KEY is not set."):
            get_llm(provider="groq", config=config)

def test_get_llm_factory_unknown_provider():
    """Tests that the factory raises a ValueError for an unknown provider."""
    config = load_config()
    with pytest.raises(ValueError, match="Unsupported LLM provider: fake_provider"):
        get_llm(provider="fake_provider", config=config) # type: ignore