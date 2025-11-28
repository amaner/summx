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
    model_name: Optional[str] = None,
) -> LLMClient:
    """Factory function to get an LLM client based on the provider."""
    if provider == "openai":
        from .openai_client import OpenAIClient
        if not config.openai_api_key:
            raise ValueError("OPENAI_API_KEY is not set in the configuration.")
        return OpenAIClient(
            api_key=config.openai_api_key, model=model_name or config.planner_model
        )
    elif provider == "groq":
        from .groq_client import GroqClient
        if not config.groq_api_key:
            raise ValueError("GROQ_API_KEY is not set in the configuration.")
        return GroqClient(
            api_key=config.groq_api_key, model=model_name or config.summarizer_model
        )
    elif provider == "dummy":
        return DummyLLMClient()
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")
