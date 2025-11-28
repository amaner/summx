"""
This package contains clients for fetching paper data from various sources.

The primary interface is the `PaperSourceClient` abstract base class.
"""

from .base import PaperSourceClient
from .arxiv_api_client import ArxivApiClient
