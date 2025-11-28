import arxiv
import fitz  # PyMuPDF
import httpx
from typing import List

from summx.models.paper import PaperMeta, PaperContentSections
from summx.models.plan import SearchPlan, SortType
from summx.sources.base import PaperSourceClient


class ArxivApiClient(PaperSourceClient):
    """A client for interacting directly with the arXiv API."""

    async def search_papers(self, plan: SearchPlan) -> List[PaperMeta]:
        """Search for papers using the official arXiv API."""
        query = self._build_query(plan)
        sort_by = self._get_sort_by(plan.sort)

        search = arxiv.Search(
            query=query,
            max_results=plan.limit,
            sort_by=sort_by,
        )

        results = []
        for result in search.results():
            meta = PaperMeta(
                arxiv_id=result.entry_id.split('/')[-1],
                title=result.title,
                authors=[author.name for author in result.authors],
                categories=result.categories,
                published=result.published.isoformat(),
                abstract=result.summary,
                pdf_url=result.pdf_url,
            )
            results.append(meta)
        return results

    async def read_paper(self, arxiv_id: str) -> PaperContentSections:
        """Download the PDF for a paper and extract its text content."""
        # First, get the paper's metadata to find its PDF URL
        search = arxiv.Search(id_list=[arxiv_id])
        paper = next(search.results(), None)
        if not paper or not paper.pdf_url:
            raise ValueError(f"Could not find paper or PDF URL for arXiv ID: {arxiv_id}")

        async with httpx.AsyncClient() as client:
            response = await client.get(paper.pdf_url)
            response.raise_for_status()  # Ensure the download was successful

        pdf_bytes = response.content
        text_content = ""
        with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
            for page in doc:
                text_content += page.get_text()

        return PaperContentSections(
            full_text=text_content,
            abstract=paper.summary
        )

    def _build_query(self, plan: SearchPlan) -> str:
        """Build the query string for the arXiv API from a SearchPlan."""
        parts = []
        if plan.filters.topic:
            parts.append(f'ti:"{plan.filters.topic}"')
        if plan.filters.author:
            parts.append(f'au:"{plan.filters.author}"')
        return " AND ".join(parts)

    def _get_sort_by(self, sort: SortType) -> arxiv.SortCriterion:
        """Map our internal SortType to the arxiv package's SortCriterion."""
        if sort == "relevance":
            return arxiv.SortCriterion.Relevance
        return arxiv.SortCriterion.SubmittedDate
