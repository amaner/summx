from abc import ABC, abstractmethod
from typing import Dict, List, Literal, Optional

from summx.config import SummXConfig

Provider = Literal["openai", "groq", "dummy"]


class LLMClient(ABC):
    """Abstract base class for all LLM provider clients."""

    @abstractmethod
    async def chat(self, messages: List[Dict[str, str]]) -> str:
        """Sends a chat request to the LLM and returns the string response."""
        pass


class DummyLLMClient(LLMClient):
    """A dummy LLM client for testing that returns a canned response."""

    def __init__(self, response: str = "This is a dummy response."):
        self.response = response

    async def chat(self, messages: List[Dict[str, str]]) -> str:
        return self.response


def get_llm(
    provider: Provider,
    config: SummXConfig,
    model: Optional[str] = None,
) -> LLMClient:
    """
    Factory function to get an LLM client based on the provider and config.

    Args:
        provider: The name of the LLM provider.
        config: The application configuration object.
        model: Optional model name to override the default from config.

    Returns:
        An instance of an LLMClient.
    """
    # Local imports to avoid circular dependencies
    from .groq_client import GroqClient
    from .openai_client import OpenAIClient

    if provider == "openai":
        api_key = config.openai_api_key
        if not api_key:
            raise ValueError("OPENAI_API_KEY is not set.")
        return OpenAIClient(api_key=api_key, model=model or config.planner_model)

    if provider == "groq":
        api_key = config.groq_api_key
        if not api_key:
            raise ValueError("GROQ_API_KEY is not set.")
        return GroqClient(api_key=api_key, model=model or config.summarizer_model)

    if provider == "dummy":
        return DummyLLMClient()

    raise ValueError(f"Unknown LLM provider: {provider}")
