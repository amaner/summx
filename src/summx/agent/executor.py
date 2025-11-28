import asyncio
import json
import logging
import re
from typing import List, Tuple

from summx.llm import LLMClient
from summx.sources.base import PaperSourceClient
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

    def __init__(self, source_client: PaperSourceClient, summarizer_llm: LLMClient):
        self.source_client = source_client
        self.summarizer_llm = summarizer_llm

    async def execute(self, plan: SearchPlan) -> List[PaperResult]:
        """Executes the given search plan and returns a list of paper results."""
        logger.info(f"Executing plan: {plan.model_dump_json(indent=2)}")

        # 1. Fetch paper metadata from the source client
        paper_metas = await self.source_client.search_papers(plan)

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
            # Read the full paper content
            content = await self.source_client.read_paper(meta.arxiv_id)

            # Summarize the content
            summary = await self._summarize_content(content)

            return PaperResult(meta=meta, content=content, summary=summary)
        except Exception as e:
            logger.error(f"Failed to process paper {meta.arxiv_id}: {e}")
            # Return metadata-only result on failure
            return PaperResult(meta=meta)

    async def _summarize_content(self, content: PaperContentSections) -> PaperSummary:
        """Summarizes the given content using the summarizer LLM."""
        # In a real application, this prompt would be more sophisticated and live in `prompts.py`.
        system_prompt = (
            "You are a research assistant. Your task is to summarize a paper's abstract."
            "Analyze the text and provide a summary in the following JSON format:\n"
            "{\n"
            '    "tldr": ["A one-sentence summary."],\n'
            '    "problem": "What problem is the paper trying to solve?",\n'
            '    "method": "What method does the paper propose?",\n'
            '    "results": "What are the key results?",\n'
            '    "limitations": "What are the limitations of the work?",\n'
            '    "future_work": "What are the suggestions for future work?",\n'
            '    "raw_markdown": "A markdown-formatted summary."\n'
            "}\n"
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content.full_text},
        ]

        response_text = await self.summarizer_llm.chat(messages)
        try:
            # Use regex to find the JSON block, even with markdown fences
            match = re.search(r"```json\n({.*?})\n```|({.*?})", response_text, re.DOTALL)
            if not match:
                raise json.JSONDecodeError("No JSON object found in response", response_text, 0)
            
            # Extract the first non-empty group
            json_str = next(g for g in match.groups() if g)
            summary_json = json.loads(json_str)
            return PaperSummary.model_validate(summary_json)
        except (json.JSONDecodeError, TypeError) as e:
            # If the LLM fails to produce valid JSON, we fall back to a raw summary.
            return PaperSummary(
                tldr=["LLM failed to produce a valid JSON summary."],
                problem="N/A",
                method="N/A",
                results="N/A",
                limitations="N/A",
                future_work="N/A",
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
