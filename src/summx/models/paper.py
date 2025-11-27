from pydantic import BaseModel, Field
from typing import Optional, List, Dict

class PaperMeta(BaseModel):
    """Metadata for a single paper as returned by the MCP layer."""
    arxiv_id: str
    title: str
    authors: List[str]
    categories: List[str]
    published: str
    abstract: Optional[str] = None
    pdf_url: Optional[str] = None
    local_pdf_path: Optional[str] = None

class PaperContentSections(BaseModel):
    """Extracted textual content of a paper, split into semantic sections."""
    full_text: str
    abstract: Optional[str] = None
    introduction: Optional[str] = None
    methods: Optional[str] = None
    results: Optional[str] = None
    conclusion: Optional[str] = None
    other_sections: Dict[str, str] = Field(default_factory=dict)

class PaperSummary(BaseModel):
    """LLM-produced summary of a paper."""
    tldr: List[str] = Field(default_factory=list)
    problem: str
    method: str
    results: str
    limitations: str
    future_work: str
    raw_markdown: str

class PaperResult(BaseModel):
    """Convenience wrapper combining everything for a single paper result."""
    meta: PaperMeta
    content: Optional[PaperContentSections] = None
    summary: Optional[PaperSummary] = None
    plan_tags: List[str] = Field(default_factory=list)
