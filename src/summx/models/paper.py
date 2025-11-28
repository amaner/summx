from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class PaperMeta(BaseModel):
    """Represents metadata for a single paper."""
    arxiv_id: str
    title: str
    authors: List[str]
    categories: List[str]
    published: str
    abstract: Optional[str] = None
    pdf_url: Optional[str] = None
    local_pdf_path: Optional[str] = None


class PaperContentSections(BaseModel):
    """Represents the extracted textual content of a paper."""
    full_text: str
    abstract: Optional[str] = None
    introduction: Optional[str] = None
    methods: Optional[str] = None
    results: Optional[str] = None
    conclusion: Optional[str] = None
    other_sections: Dict[str, str] = Field(default_factory=dict)


class PaperSummary(BaseModel):
    """Represents the structured summary of a paper."""
    tldr: List[str] = Field(default_factory=list)
    problem: str
    method: str
    results: str
    limitations: str
    future_work: str
    raw_markdown: str

    def to_markdown(self) -> str:
        """Converts the structured summary into a pretty markdown string."""
        if self.problem == "N/A":  # Fallback for when parsing failed
            return self.raw_markdown

        sections = {
            "Problem": self.problem,
            "Method": self.method,
            "Results": self.results,
            "Limitations": self.limitations,
            "Future Work": self.future_work,
        }

        tldr_section = "- " + "\n- ".join(self.tldr) if self.tldr else ""
        other_sections = "\n".join(f"**{title}:** {content}" for title, content in sections.items())

        return f"**TL;DR:**\n{tldr_section}\n\n---\n\n{other_sections}"


class PaperResult(BaseModel):
    """Convenience wrapper combining everything for a single paper result."""
    meta: PaperMeta
    content: Optional[PaperContentSections] = None
    summary: Optional[PaperSummary] = None
    plan_tags: List[str] = Field(default_factory=list)