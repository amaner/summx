import json
from typing import Dict, List

from summx.llm import LLMClient
from summx.models import SearchPlan
from summx.prompts import QUERY_PLANNER_SYSTEM_PROMPT


class QueryPlanner:
    """
    Converts a natural-language user query into a structured SearchPlan using an LLM.
    """

    def __init__(self, llm: LLMClient):
        """
        Initializes the QueryPlanner with an LLM client.

        Args:
            llm: An instance of a class that inherits from LLMClient.
        """
        self.llm = llm

    async def plan(self, raw_query: str) -> SearchPlan:
        """
        Takes a raw query and returns a structured SearchPlan.

        Args:
            raw_query: The user's natural language query.

        Returns:
            A SearchPlan object.
        """
        messages: List[Dict[str, str]] = [
            {"role": "system", "content": QUERY_PLANNER_SYSTEM_PROMPT},
            {"role": "user", "content": raw_query},
        ]

        try:
            response_text = await self.llm.chat(messages)
            # The prompt asks for a raw JSON object, so we parse it directly.
            plan_json = json.loads(response_text)
            # Add the original query to the plan for traceability
            plan_json["raw_query"] = raw_query
            return SearchPlan.model_validate(plan_json)
        except (json.JSONDecodeError, TypeError) as e:
            # Handle cases where the LLM output is not valid JSON
            raise ValueError(f"Failed to parse LLM response into a valid plan: {e}") from e
        except Exception as e:
            raise RuntimeError(f"An unexpected error occurred during planning: {e}") from e
