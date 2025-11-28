"""
This package contains clients for fetching paper data from various sources.

The primary interface is the `PaperSourceClient` abstract base class.
"""

from .base import PaperSourceClient
from .arxiv_api_client import ArxivApiClient
from summx.config import SummXConfig

def get_source_client(config: SummXConfig) -> PaperSourceClient:
    """Factory function to get a paper source client based on the config."""
    if config.paper_source == "api":
        return ArxivApiClient()
    # In the future, this is where we would add the MCP client.
    # elif config.paper_source == "mcp":
    #     from .arxiv_mcp_client import ArxivMcpClient
    #     return ArxivMcpClient()
    else:
        raise ValueError(f"Unsupported paper source: {config.paper_source}")

