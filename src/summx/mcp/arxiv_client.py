import logging
import re
from typing import List, Optional

from summx.models import PaperMeta, PaperContentSections, SearchPlan, SortType
from .session import McpSession

logger = logging.getLogger(__name__)


class ArxivMcpClient:
    """
    A source-specific client for interacting with the Arxiv MCP server.

    This class translates between SummX's internal models and the raw MCP tool calls,
    providing a clean, semantic interface to the rest of the application.
    """

    def __init__(self, session: McpSession):
        """
        Initializes the ArxivMcpClient with an active McpSession.
        """
        self.session = session

    async def search_papers(
        self,
        topic: Optional[str] = None,
        author: Optional[str] = None,
        sort: SortType = "most_recent",
        limit: int = 10,
    ) -> List[PaperMeta]:
        """
        Searches for papers on arXiv using the underlying MCP tool.

        Args:
            topic: The main topic or query.
            author: The author to filter by.
            sort: The sorting criterion ('most_recent' or 'relevance').
            limit: The maximum number of results to return.

        Returns:
            A list of PaperMeta objects.
        """
        # The `search_by_author` tool is more precise for author queries.
        if author and not topic:
            tool_name = "search_by_author"
            arguments = {"author_name": author, "max_results": limit}
        else:
            # The `search_papers` tool handles general queries and topic+author combos.
            tool_name = "search_papers"
            query = topic or ""
            if author:
                query += f' AND au:"{author}"'
            arguments = {
                "query": query.strip(),
                "max_results": limit,
                "sort_by_relevance": sort == "relevance",
            }

        logger.info(f"Calling MCP tool '{tool_name}' with args: {arguments}")
        response = await self.session.call_tool(name=tool_name, arguments=arguments)

        papers = []
        for item in response.get("results", []):
            # The MCP server returns a slightly different format than our internal model.
            # We perform the mapping here to keep the rest of the app consistent.
            papers.append(
                PaperMeta(
                    arxiv_id=re.sub(r"v\d+$", "", item.get("arxiv_id", "")),
                    title=item.get("title", ""),
                    authors=item.get("authors", []),
                    categories=item.get("categories", []),
                    published=item.get("published_date", ""),
                    abstract=item.get("summary", ""),
                    pdf_url=item.get("pdf_url", ""),
                )
            )
        return papers

    async def get_papers_for_plan(self, plan: SearchPlan) -> List[PaperMeta]:
        """Convenience method to execute a search based on a SearchPlan."""
        return await self.search_papers(
            topic=plan.filters.topic,
            author=plan.filters.author,
            sort=plan.sort,
            limit=plan.limit,
        )

    async def download_paper(self, arxiv_id: str) -> Optional[str]:
        """
        Downloads a paper's PDF and returns its local path.

        Returns:
            The local file path of the downloaded PDF, or None if failed.
        """
        logger.info(f"Requesting download for arXiv ID: {arxiv_id}")
        response = await self.session.call_tool(
            name="download_paper", arguments={"arxiv_id": arxiv_id}
        )
        if response.get("success"):
            return response.get("local_path")
        return None

    async def read_paper(self, arxiv_id: str) -> PaperContentSections:
        """
        Reads the content of a downloaded paper.

        Note: This assumes the paper is already downloaded or that the MCP server
        handles on-demand downloading and reading.
        """
        # This is a placeholder. A real implementation would call a 'read_paper' tool.
        # Emi's server doesn't have a direct 'read' tool, but combines download + read.
        # We will simulate this by calling download and then reading the file locally.
        # In a more advanced setup, the MCP server would handle this atomatically.
        logger.warning(
            "'read_paper' is not a direct MCP tool in this implementation. "
            "This will be handled by the executor."
        )
        # In a real scenario, you might call a tool that returns structured content.
        # For now, we return an empty object as a placeholder.
        return PaperContentSections(full_text="")
