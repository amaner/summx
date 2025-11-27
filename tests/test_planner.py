import json
import pytest
from summx.agent.planner import QueryPlanner
from summx.llm import DummyLLMClient
from summx.models import SearchPlan

# A realistic JSON output from the LLM based on the prompt
MOCK_PLAN_JSON = {
    "intent": "search_papers",
    "source": "arxiv",
    "filters": {
        "topic": "hyper graphs"
    },
    "sort": "most_recent",
    "limit": 5,
    "summarization": {
        "enabled": True,
        "depth": "abstract+intro+conclusion"
    }
}

@pytest.mark.asyncio
async def test_query_planner_success():
    """
    Tests that the QueryPlanner correctly parses a valid JSON response from the LLM
    and creates a SearchPlan object.
    """
    # 1. Setup: Create a dummy LLM that returns our mock JSON
    dummy_llm = DummyLLMClient(response=json.dumps(MOCK_PLAN_JSON))
    
    # 2. Instantiate the planner
    planner = QueryPlanner(llm=dummy_llm)
    
    # 3. Run the plan method
    raw_query = "five most recent papers on hyper graphs"
    search_plan = await planner.plan(raw_query=raw_query)
    
    # 4. Assertions: Check if the SearchPlan object is correct
    assert isinstance(search_plan, SearchPlan)
    assert search_plan.raw_query == raw_query
    assert search_plan.filters.topic == "hyper graphs"
    assert search_plan.limit == 5
    assert search_plan.sort == "most_recent"
    assert search_plan.summarization.enabled is True

@pytest.mark.asyncio
async def test_query_planner_invalid_json():
    """
    Tests that the QueryPlanner raises a ValueError if the LLM returns invalid JSON.
    """
    # 1. Setup: Dummy LLM returns a non-JSON string
    dummy_llm = DummyLLMClient(response="This is not valid JSON.")
    planner = QueryPlanner(llm=dummy_llm)
    
    # 2. Run and assert that it raises the expected exception
    with pytest.raises(ValueError, match="Failed to parse LLM response"):
        await planner.plan(raw_query="any query")
