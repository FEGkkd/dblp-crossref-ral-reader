from .models import DEFAULT_JOURNAL, PaperRecord, SearchConfig, SearchResultPackage, SearchStats
from .pipeline import run_search_pipeline

__all__ = [
    "DEFAULT_JOURNAL",
    "PaperRecord",
    "SearchConfig",
    "SearchResultPackage",
    "SearchStats",
    "run_search_pipeline",
]

__version__ = "0.1.0"
