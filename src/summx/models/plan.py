from pydantic import BaseModel, Field
from typing import Literal, Optional

SortType = Literal["most_recent", "relevance"]
DepthType = Literal["abstract", "abstract+intro+conclusion", "full"]

class SummarizationConfig(BaseModel):
    """Controls how and whether the summarization step is run."""
    enabled: bool = True
    depth: DepthType = "abstract+intro+conclusion"
    max_tokens: Optional[int] = None

class SearchFilters(BaseModel):
    """Represents user-intent filters extracted from the query."""
    topic: Optional[str] = None
    author: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None

class SearchPlan(BaseModel):
    """The main plan object used internally by the agent."""
    intent: str = "search_papers"
    source: str = "arxiv"
    filters: SearchFilters = Field(default_factory=SearchFilters)
    sort: SortType = "most_recent"
    limit: int = 5
    summarization: SummarizationConfig = Field(default_factory=SummarizationConfig)
    raw_query: str
