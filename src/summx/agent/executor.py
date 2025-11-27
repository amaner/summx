import asyncio
import json
import logging
from typing import List, Tuple

from summx.llm import LLMClient
from summx.mcp import ArxivMcpClient
from summx.models import (
    PaperContentSections,
    PaperResult,
    PaperSummary,
    SearchPlan,
)
from .planner import QueryPlanner

logger = logging.getLogger(__name__)


class PlanExecutor:
    """Executes a SearchPlan to fetch and summarize papers."""

    def __init__(self, mcp_client: ArxivMcpClient, summarizer_llm: LLMClient):
        self.mcp_client = mcp_client
        self.summarizer_llm = summarizer_llm

    async def execute(self, plan: SearchPlan) -> List[PaperResult]:
        """Executes the given search plan and returns a list of paper results."""
        logger.info(f"Executing plan: {plan.model_dump_json(indent=2)}")

        # 1. Fetch paper metadata from MCP client
        paper_metas = await self.mcp_client.get_papers_for_plan(plan)

        results: List[PaperResult] = []
        if not plan.summarization.enabled:
            # If summarization is disabled, just return the metadata
            for meta in paper_metas:
                results.append(PaperResult(meta=meta))
            return results

        # 2. If summarization is enabled, process papers concurrently
        tasks = [self._process_paper(meta) for meta in paper_metas]
        processed_results = await asyncio.gather(*tasks)
        return [res for res in processed_results if res is not None]

    async def _process_paper(self, meta) -> PaperResult:
        """Helper to process a single paper: download, read, and summarize."""
        try:
            # In a real implementation, we would download and read the paper.
            # The current `read_paper` is a placeholder, so we simulate content.
            # This part will be expanded in Phase 9 (Real Integration).
            content = PaperContentSections(full_text=meta.abstract or "")

            # For now, we'll just summarize the abstract.
            summary = await self._summarize_content(content)

            return PaperResult(meta=meta, content=content, summary=summary)
        except Exception as e:
            logger.error(f"Failed to process paper {meta.arxiv_id}: {e}")
            # Return metadata-only result on failure
            return PaperResult(meta=meta)

    async def _summarize_content(self, content: PaperContentSections) -> PaperSummary:
        """Summarizes the given content using the summarizer LLM."""
        # This is a placeholder for the real summarization prompt and logic.
        # A real implementation would use a prompt from `prompts.py`.
        messages = [
            {
                "role": "system",
                "content": "You are a helpful research assistant. Summarize the following abstract.",
            },
            {"role": "user", "content": content.full_text},
        ]
        response_text = await self.summarizer_llm.chat(messages)
        # A real implementation would parse this into the structured PaperSummary.
        return PaperSummary(
            tldr=["TLDR placeholder"],
            problem="Problem placeholder",
            method="Method placeholder",
            results="Results placeholder",
            limitations="Limitations placeholder",
            future_work="Future work placeholder",
            raw_markdown=response_text,
        )


class PaperAgent:
    """
    High-level agent that orchestrates planning and execution.
    """

    def __init__(self, planner: QueryPlanner, executor: PlanExecutor):
        self.planner = planner
        self.executor = executor

    async def run(self, raw_query: str) -> Tuple[SearchPlan, List[PaperResult]]:
        """
        Takes a raw user query, generates a plan, and executes it.

        Returns:
            A tuple containing the generated SearchPlan and the list of PaperResults.
        """
        logger.info(f"Received query: '{raw_query}'")
        # 1. Create a plan
        plan = await self.planner.plan(raw_query)
        logger.info("Plan created successfully.")

        # 2. Execute the plan
        results = await self.executor.execute(plan)
        logger.info(f"Execution finished. Found {len(results)} results.")

        return plan, results
