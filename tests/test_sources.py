import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from summx.sources.arxiv_api_client import ArxivApiClient
from summx.models.plan import SearchPlan, SearchFilters
from summx.models.paper import PaperMeta

# Helper to create a mock author object, as expected by the arxiv library
class MockAuthor:
    def __init__(self, name):
        self.name = name

# Helper to create a realistic mock of an arxiv.Result object
def create_mock_arxiv_result(arxiv_id="2305.12345v1", title="Test Paper"):
    mock_result = MagicMock()
    mock_result.entry_id = f"http://arxiv.org/abs/{arxiv_id}"
    mock_result.title = title
    mock_result.authors = [MockAuthor("Dr. Mock Author")]
    mock_result.categories = ["cs.AI", "cs.LG"]
    mock_result.published = datetime(2023, 5, 20, 18, 0, 0)
    mock_result.summary = "This is a test abstract."
    mock_result.pdf_url = f"http://arxiv.org/pdf/{arxiv_id}.pdf"
    return mock_result


@pytest.mark.asyncio
@patch('summx.sources.arxiv_api_client.arxiv.Search')
async def test_arxiv_api_client_search_papers(mock_arxiv_search):
    """
    Tests that the ArxivApiClient correctly calls the arxiv library
    and maps the results to PaperMeta objects.
    """
    # 1. Configure the mock to return a list with one mock result
    mock_instance = mock_arxiv_search.return_value
    mock_instance.results.return_value = [create_mock_arxiv_result()]

    # 2. Instantiate the client and create a search plan
    client = ArxivApiClient()
    plan = SearchPlan(
        filters=SearchFilters(topic="test topic", author="test author"),
        limit=5,
        sort="most_recent",
        raw_query="test"
    )

    # 3. Call the method under test
    results = await client.search_papers(plan)

    # 4. Assert that the arxiv library was called correctly
    mock_arxiv_search.assert_called_once()
    _, call_kwargs = mock_arxiv_search.call_args
    assert call_kwargs['query'] == 'ti:"test topic" AND au:"test author"'
    assert call_kwargs['max_results'] == 5

    # 5. Assert that the mapping to PaperMeta is correct
    assert len(results) == 1
    paper_meta = results[0]
    assert isinstance(paper_meta, PaperMeta)
    assert paper_meta.arxiv_id == "2305.12345v1"
    assert paper_meta.title == "Test Paper"
    assert paper_meta.authors == ["Dr. Mock Author"]
    assert paper_meta.published == "2023-05-20T18:00:00"
