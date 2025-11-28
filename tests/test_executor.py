import pytest
from unittest.mock import AsyncMock, MagicMock

from summx.agent import PaperAgent, PlanExecutor, QueryPlanner
from summx.llm import DummyLLMClient
from summx.sources.base import PaperSourceClient
from summx.models import PaperMeta, SearchPlan, PaperResult, PaperContentSections

# Mock data to be returned by dependencies
MOCK_SEARCH_PLAN = SearchPlan(raw_query="test query")
MOCK_PAPER_LIST = [
    PaperMeta(
        arxiv_id="1234.56789",
        title="Test Paper 1",
        authors=["Author A"],
        categories=["cs.AI"],
        published="2025-01-01",
        abstract="Abstract for paper 1.",
    )
]

@pytest.mark.asyncio
async def test_plan_executor_fetches_and_summarizes():
    """
    Tests that the PlanExecutor correctly calls the MCP client and summarizer LLM.
    """
    # 1. Setup: Create mocks for dependencies
    mock_source_client = AsyncMock(spec=PaperSourceClient)
    mock_source_client.search_papers.return_value = MOCK_PAPER_LIST
    mock_source_client.read_paper.return_value = PaperContentSections(full_text="Abstract for paper 1.")

    mock_summarizer_llm = DummyLLMClient(response='{"tldr": ["TLDR"], "problem": "Problem", "method": "Method", "results": "Results", "limitations": "Limitations", "future_work": "Future work", "raw_markdown": "Summary"}')

    # 2. Instantiate the executor with mocks
    executor = PlanExecutor(
        source_client=mock_source_client, summarizer_llm=mock_summarizer_llm
    )

    # 3. Run the execute method
    results = await executor.execute(plan=MOCK_SEARCH_PLAN)

    # 4. Assertions
    mock_source_client.search_papers.assert_called_once_with(MOCK_SEARCH_PLAN)
    mock_source_client.read_paper.assert_called_once_with("1234.56789")
    
    assert len(results) == 1
    result = results[0]
    assert result.meta.title == "Test Paper 1"
    assert result.summary is not None
    assert result.summary.raw_markdown == "Summary"

@pytest.mark.asyncio
async def test_paper_agent_orchestrates_planning_and_execution():
    """
    Tests that the PaperAgent correctly calls the planner and then the executor.
    """
    # 1. Setup: Mock the planner and executor
    mock_planner = AsyncMock(spec=QueryPlanner)
    mock_planner.plan.return_value = MOCK_SEARCH_PLAN
    
    mock_executor = AsyncMock(spec=PlanExecutor)
    mock_executor.execute.return_value = [PaperResult(meta=meta) for meta in MOCK_PAPER_LIST]
    
    # 2. Instantiate the agent
    agent = PaperAgent(planner=mock_planner, executor=mock_executor)
    
    # 3. Run the agent
    raw_query = "test query"
    plan, results = await agent.run(raw_query=raw_query)
    
    # 4. Assertions
    mock_planner.plan.assert_called_once_with(raw_query)
    mock_executor.execute.assert_called_once_with(MOCK_SEARCH_PLAN)
    
    assert plan == MOCK_SEARCH_PLAN
    assert len(results) == 1
    assert results[0].meta.title == "Test Paper 1"
