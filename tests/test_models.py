import pytest
from summx.models import (
    PaperMeta,
    PaperResult,
    SearchPlan,
    SearchFilters,
    SummarizationConfig,
)


def test_search_plan_instantiation():
    """Tests that a SearchPlan can be created with minimal information."""
    raw_query = "test query"
    plan = SearchPlan(raw_query=raw_query)

    assert plan.raw_query == raw_query
    assert isinstance(plan.filters, SearchFilters)
    assert isinstance(plan.summarization, SummarizationConfig)
    assert plan.limit == 5
    assert plan.sort == "most_recent"


def test_paper_meta_instantiation():
    """Tests that PaperMeta can be created with required fields."""
    meta = PaperMeta(
        arxiv_id="1234.56789",
        title="Test Paper",
        authors=["Author One", "Author Two"],
        categories=["cs.AI"],
        published="2025-01-01",
    )
    assert meta.title == "Test Paper"
    assert meta.authors == ["Author One", "Author Two"]


def test_paper_result_composition():
    """Tests that PaperResult correctly composes other models."""
    meta = PaperMeta(
        arxiv_id="1234.56789",
        title="Test Paper",
        authors=["Author One"],
        categories=["cs.AI"],
        published="2025-01-01",
    )
    result = PaperResult(meta=meta)

    assert result.meta.arxiv_id == "1234.56789"
    assert result.content is None
    assert result.summary is None
    assert result.plan_tags == []