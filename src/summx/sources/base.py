from abc import ABC, abstractmethod
from typing import List

from summx.models.paper import PaperMeta, PaperContentSections
from summx.models.plan import SearchPlan


class PaperSourceClient(ABC):
    """Abstract base class for a client that can retrieve paper data."""

    @abstractmethod
    async def search_papers(self, plan: SearchPlan) -> List[PaperMeta]:
        """Search for papers based on a search plan and return metadata."""
        pass

    @abstractmethod
    async def read_paper(self, arxiv_id: str) -> PaperContentSections:
        """Read the content of a paper and return its sections."""
        pass
