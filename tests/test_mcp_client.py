import pytest
from unittest.mock import AsyncMock

from summx.mcp.arxiv_client import ArxivMcpClient
from summx.models import PaperMeta

# A mock response from the MCP server's 'search_papers' tool
MOCK_MCP_RESPONSE = {
    "query_used": "ti:\"hyper graphs\" OR abs:\"hyper graphs\"",
    "results": [
        {
            "title": "A Survey on Hypergraph Neural Networks",
            "authors": ["Author A", "Author B"],
            "summary": "This paper reviews the recent developments...",
            "pdf_url": "http://arxiv.org/pdf/2301.00001v1",
            "published_date": "2023-01-01",
            "arxiv_id": "2301.00001v1",
            "categories": ["cs.LG"],
        }
    ],
}

@pytest.mark.asyncio
async def test_search_papers_maps_response_correctly():
    """
    Tests that ArxivMcpClient correctly calls the 'search_papers' tool and
    maps the response to a list of PaperMeta objects.
    """
    # 1. Setup: Mock the McpSession and its call_tool method
    mock_session = AsyncMock()
    mock_session.call_tool.return_value = MOCK_MCP_RESPONSE
    
    # 2. Instantiate the client with the mocked session
    client = ArxivMcpClient(session=mock_session)
    
    # 3. Run the search
    papers = await client.search_papers(topic="hyper graphs")
    
    # 4. Assertions
    # Check that the correct tool was called
    mock_session.call_tool.assert_called_once_with(
        name="search_papers",
        arguments={
            "query": "hyper graphs",
            "max_results": 10,
            "sort_by_relevance": False,
        },
    )
    
    # Check that the response was mapped correctly
    assert len(papers) == 1
    paper = papers[0]
    assert isinstance(paper, PaperMeta)
    assert paper.title == "A Survey on Hypergraph Neural Networks"
    assert paper.arxiv_id == "2301.00001" # Version identifier should be stripped
    assert paper.authors == ["Author A", "Author B"]
    assert paper.published == "2023-01-01"

@pytest.mark.asyncio
async def test_search_by_author_uses_correct_tool():
    """
    Tests that a query with only an author uses the 'search_by_author' tool.
    """
    mock_session = AsyncMock()
    mock_session.call_tool.return_value = {"results": []} # Empty response is fine
    
    client = ArxivMcpClient(session=mock_session)
    await client.search_papers(author="John Doe", limit=5)
    
    mock_session.call_tool.assert_called_once_with(
        name="search_by_author",
        arguments={"author_name": "John Doe", "max_results": 5},
    )