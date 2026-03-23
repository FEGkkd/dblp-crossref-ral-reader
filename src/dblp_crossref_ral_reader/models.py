from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


DEFAULT_JOURNAL = "IEEE Robotics and Automation Letters"


@dataclass
class SearchConfig:
    keywords: list[str]
    journal: str = DEFAULT_JOURNAL
    journals: list[str] = field(default_factory=list)
    years_back: int | None = None
    days_back: int | None = None
    max_results: int = 30
    output_dir: str = "./outputs"
    language: str = "zh"
    require_abstract: bool = False
    group_by_keyword: bool = True
    save_json: bool = True
    save_markdown: bool = True
    save_docx: bool = True
    crossref_mailto: str | None = None
    dblp_batch_size: int = 1000
    dblp_max_batches_per_keyword: int = 40
    enable_semantic_scholar: bool = True
    semantic_scholar_api_key_env: str = "SEMANTIC_SCHOLAR_API_KEY"
    semantic_scholar_top_k: int = 5
    semantic_scholar_enrich_limit: int = 300
    semantic_scholar_timeout: int = 30
    semantic_scholar_max_retries: int = 3

    def normalized_keywords(self) -> list[str]:
        return [item.strip() for item in self.keywords if item and item.strip()]

    def normalized_journals(self) -> list[str]:
        raw = self.journals or [self.journal]
        output: list[str] = []
        seen: set[str] = set()
        for item in raw:
            if not item or not str(item).strip():
                continue
            journal_name = str(item).strip()
            if journal_name in seen:
                continue
            seen.add(journal_name)
            output.append(journal_name)
        return output or [DEFAULT_JOURNAL]

    def to_dict(self) -> dict[str, Any]:
        return {
            "keywords": self.keywords,
            "journal": self.journal,
            "journals": self.normalized_journals(),
            "years_back": self.years_back,
            "days_back": self.days_back,
            "max_results": self.max_results,
            "output_dir": self.output_dir,
            "language": self.language,
            "require_abstract": self.require_abstract,
            "group_by_keyword": self.group_by_keyword,
            "save_json": self.save_json,
            "save_markdown": self.save_markdown,
            "save_docx": self.save_docx,
            "crossref_mailto": self.crossref_mailto,
            "dblp_batch_size": self.dblp_batch_size,
            "dblp_max_batches_per_keyword": self.dblp_max_batches_per_keyword,
            "enable_semantic_scholar": self.enable_semantic_scholar,
            "semantic_scholar_api_key_env": self.semantic_scholar_api_key_env,
            "semantic_scholar_top_k": self.semantic_scholar_top_k,
            "semantic_scholar_enrich_limit": self.semantic_scholar_enrich_limit,
            "semantic_scholar_timeout": self.semantic_scholar_timeout,
            "semantic_scholar_max_retries": self.semantic_scholar_max_retries,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "SearchConfig":
        data = data or {}
        journals = list(data.get("journals") or [])
        journal = data.get("journal", DEFAULT_JOURNAL)
        if not journals:
            journals = [journal]
        return cls(
            keywords=list(data.get("keywords") or []),
            journal=journal,
            journals=journals,
            years_back=data.get("years_back"),
            days_back=data.get("days_back"),
            max_results=int(data.get("max_results", 30)),
            output_dir=data.get("output_dir", "./outputs"),
            language=data.get("language", "zh"),
            require_abstract=bool(data.get("require_abstract", False)),
            group_by_keyword=bool(data.get("group_by_keyword", True)),
            save_json=bool(data.get("save_json", True)),
            save_markdown=bool(data.get("save_markdown", True)),
            save_docx=bool(data.get("save_docx", True)),
            crossref_mailto=data.get("crossref_mailto"),
            dblp_batch_size=int(data.get("dblp_batch_size", 1000)),
            dblp_max_batches_per_keyword=int(data.get("dblp_max_batches_per_keyword", 40)),
            enable_semantic_scholar=bool(data.get("enable_semantic_scholar", True)),
            semantic_scholar_api_key_env=str(data.get("semantic_scholar_api_key_env") or "SEMANTIC_SCHOLAR_API_KEY"),
            semantic_scholar_top_k=int(data.get("semantic_scholar_top_k", 5)),
            semantic_scholar_enrich_limit=int(data.get("semantic_scholar_enrich_limit", 300)),
            semantic_scholar_timeout=int(data.get("semantic_scholar_timeout", 30)),
            semantic_scholar_max_retries=int(data.get("semantic_scholar_max_retries", 3)),
        )


@dataclass
class PaperRecord:
    title: str
    authors: list[str] = field(default_factory=list)
    abstract: str | None = None
    abstract_source: str | None = None
    crossref_abstract: str | None = None
    doi: str | None = None
    url: str | None = None
    pdf_url: str | None = None
    pdf_url_source: str | None = None
    journal: str | None = None
    publication_year: int | None = None
    publication_date: str | None = None
    dblp_url: str | None = None
    crossref_score: float | None = None
    matched_keywords: list[str] = field(default_factory=list)
    source_tags: list[str] = field(default_factory=list)
    chinese_summary: str | None = None
    topic_tags: list[str] = field(default_factory=list)
    recommendation_reason: str | None = None
    raw_venue: str | None = None
    subjects: list[str] = field(default_factory=list)
    publication_type: str | None = None
    publisher: str | None = None
    semantic_scholar_paper_id: str | None = None
    semantic_scholar_url: str | None = None
    semantic_scholar_abstract: str | None = None
    semantic_scholar_publication_date: str | None = None
    semantic_scholar_citation_count: int | None = None
    semantic_scholar_fields_of_study: list[str] = field(default_factory=list)
    semantic_scholar_open_access_pdf_url: str | None = None
    semantic_scholar_open_access_pdf_status: str | None = None
    semantic_scholar_match_score: float | None = None
    metadata_completeness: int = 0
    rank_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "authors": self.authors,
            "abstract": self.abstract,
            "abstract_source": self.abstract_source,
            "crossref_abstract": self.crossref_abstract,
            "doi": self.doi,
            "url": self.url,
            "pdf_url": self.pdf_url,
            "pdf_url_source": self.pdf_url_source,
            "journal": self.journal,
            "publication_year": self.publication_year,
            "publication_date": self.publication_date,
            "dblp_url": self.dblp_url,
            "crossref_score": self.crossref_score,
            "matched_keywords": self.matched_keywords,
            "source_tags": self.source_tags,
            "chinese_summary": self.chinese_summary,
            "topic_tags": self.topic_tags,
            "recommendation_reason": self.recommendation_reason,
            "raw_venue": self.raw_venue,
            "subjects": self.subjects,
            "publication_type": self.publication_type,
            "publisher": self.publisher,
            "semantic_scholar_paper_id": self.semantic_scholar_paper_id,
            "semantic_scholar_url": self.semantic_scholar_url,
            "semantic_scholar_abstract": self.semantic_scholar_abstract,
            "semantic_scholar_publication_date": self.semantic_scholar_publication_date,
            "semantic_scholar_citation_count": self.semantic_scholar_citation_count,
            "semantic_scholar_fields_of_study": self.semantic_scholar_fields_of_study,
            "semantic_scholar_open_access_pdf_url": self.semantic_scholar_open_access_pdf_url,
            "semantic_scholar_open_access_pdf_status": self.semantic_scholar_open_access_pdf_status,
            "semantic_scholar_match_score": self.semantic_scholar_match_score,
            "metadata_completeness": self.metadata_completeness,
            "rank_score": self.rank_score,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PaperRecord":
        return cls(
            title=str(data.get("title") or "").strip(),
            authors=list(data.get("authors") or []),
            abstract=data.get("abstract"),
            abstract_source=data.get("abstract_source"),
            crossref_abstract=data.get("crossref_abstract"),
            doi=data.get("doi"),
            url=data.get("url"),
            pdf_url=data.get("pdf_url"),
            pdf_url_source=data.get("pdf_url_source"),
            journal=data.get("journal"),
            publication_year=data.get("publication_year"),
            publication_date=data.get("publication_date"),
            dblp_url=data.get("dblp_url"),
            crossref_score=data.get("crossref_score"),
            matched_keywords=list(data.get("matched_keywords") or []),
            source_tags=list(data.get("source_tags") or []),
            chinese_summary=data.get("chinese_summary"),
            topic_tags=list(data.get("topic_tags") or []),
            recommendation_reason=data.get("recommendation_reason"),
            raw_venue=data.get("raw_venue"),
            subjects=list(data.get("subjects") or []),
            publication_type=data.get("publication_type"),
            publisher=data.get("publisher"),
            semantic_scholar_paper_id=data.get("semantic_scholar_paper_id"),
            semantic_scholar_url=data.get("semantic_scholar_url"),
            semantic_scholar_abstract=data.get("semantic_scholar_abstract"),
            semantic_scholar_publication_date=data.get("semantic_scholar_publication_date"),
            semantic_scholar_citation_count=data.get("semantic_scholar_citation_count"),
            semantic_scholar_fields_of_study=list(data.get("semantic_scholar_fields_of_study") or []),
            semantic_scholar_open_access_pdf_url=data.get("semantic_scholar_open_access_pdf_url"),
            semantic_scholar_open_access_pdf_status=data.get("semantic_scholar_open_access_pdf_status"),
            semantic_scholar_match_score=data.get("semantic_scholar_match_score"),
            metadata_completeness=int(data.get("metadata_completeness", 0)),
            rank_score=float(data.get("rank_score", 0.0)),
        )


@dataclass
class SearchStats:
    dblp_candidates: int = 0
    crossref_enriched: int = 0
    semantic_scholar_enriched: int = 0
    final_papers: int = 0
    papers_with_abstract: int = 0
    papers_with_doi: int = 0
    papers_with_pdf: int = 0
    keyword_hit_counts: dict[str, int] = field(default_factory=dict)
    overlap_keyword_pairs: dict[str, int] = field(default_factory=dict)
    generated_files: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "dblp_candidates": self.dblp_candidates,
            "crossref_enriched": self.crossref_enriched,
            "semantic_scholar_enriched": self.semantic_scholar_enriched,
            "final_papers": self.final_papers,
            "papers_with_abstract": self.papers_with_abstract,
            "papers_with_doi": self.papers_with_doi,
            "papers_with_pdf": self.papers_with_pdf,
            "keyword_hit_counts": self.keyword_hit_counts,
            "overlap_keyword_pairs": self.overlap_keyword_pairs,
            "generated_files": self.generated_files,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "SearchStats":
        data = data or {}
        return cls(
            dblp_candidates=int(data.get("dblp_candidates", 0)),
            crossref_enriched=int(data.get("crossref_enriched", 0)),
            semantic_scholar_enriched=int(data.get("semantic_scholar_enriched", 0)),
            final_papers=int(data.get("final_papers", 0)),
            papers_with_abstract=int(data.get("papers_with_abstract", 0)),
            papers_with_doi=int(data.get("papers_with_doi", 0)),
            papers_with_pdf=int(data.get("papers_with_pdf", 0)),
            keyword_hit_counts=dict(data.get("keyword_hit_counts") or {}),
            overlap_keyword_pairs=dict(data.get("overlap_keyword_pairs") or {}),
            generated_files=dict(data.get("generated_files") or {}),
        )


@dataclass
class SearchResultPackage:
    generated_at: str
    run_dir: str
    config: SearchConfig
    stats: SearchStats
    overview: str
    keyword_observations: str
    recommendations: list[dict[str, Any]] = field(default_factory=list)
    keyword_groups: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    papers: list[PaperRecord] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "run_dir": self.run_dir,
            "config": self.config.to_dict(),
            "stats": self.stats.to_dict(),
            "overview": self.overview,
            "keyword_observations": self.keyword_observations,
            "recommendations": self.recommendations,
            "keyword_groups": self.keyword_groups,
            "papers": [item.to_dict() for item in self.papers],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SearchResultPackage":
        return cls(
            generated_at=data.get("generated_at", ""),
            run_dir=data.get("run_dir", ""),
            config=SearchConfig.from_dict(data.get("config")),
            stats=SearchStats.from_dict(data.get("stats")),
            overview=data.get("overview", ""),
            keyword_observations=data.get("keyword_observations", ""),
            recommendations=list(data.get("recommendations") or []),
            keyword_groups=dict(data.get("keyword_groups") or {}),
            papers=[PaperRecord.from_dict(item) for item in data.get("papers") or []],
        )
