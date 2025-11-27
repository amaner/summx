from typing import Dict, List

from openai import AsyncOpenAI

from .base import LLMClient


class OpenAIClient(LLMClient):
    """LLM client for OpenAI API."""

    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self.client = AsyncOpenAI(api_key=self.api_key)

    async def chat(self, messages: List[Dict[str, str]]) -> str:
        """Sends a chat request to the OpenAI API."""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,  # type: ignore
            )
            content = response.choices[0].message.content
            if content is None:
                raise ValueError("Received null content from OpenAI API.")
            return content
        except Exception as e:
            # In a real app, you'd want more specific error handling
            raise RuntimeError(f"Error calling OpenAI API: {e}") from e
