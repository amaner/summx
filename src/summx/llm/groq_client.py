from typing import Dict, List

from groq import AsyncGroq

from .base import LLMClient


class GroqClient(LLMClient):
    """LLM client for the Groq API."""

    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self.client = AsyncGroq(api_key=self.api_key)

    async def chat(self, messages: List[Dict[str, str]]) -> str:
        """Sends a chat request to the Groq API."""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,  # type: ignore
            )
            content = response.choices[0].message.content
            if content is None:
                raise ValueError("Received null content from Groq API.")
            return content
        except Exception as e:
            raise RuntimeError(f"Error calling Groq API: {e}") from e
