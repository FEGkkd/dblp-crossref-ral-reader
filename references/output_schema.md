# Output Schema

## JSON 输出结构

`results.json` 顶层字段建议如下：

```json
{
  "generated_at": "20260321_153000",
  "run_dir": "/abs/path/to/output",
  "config": {},
  "stats": {},
  "overview": "string",
  "keyword_observations": "string",
  "recommendations": [],
  "keyword_groups": {},
  "papers": []
}
```

## `config` 字段

包含本次检索参数：

- `keywords`
- `journal`
- `journals`
- `years_back`
- `days_back`
- `max_results`
- `output_dir`
- `language`
- `require_abstract`
- `group_by_keyword`
- `save_json`
- `save_markdown`
- `save_docx`
- `crossref_mailto`
- `enable_semantic_scholar`
- `semantic_scholar_api_key_env`
- `semantic_scholar_top_k`
- `semantic_scholar_enrich_limit`
- `semantic_scholar_timeout`
- `semantic_scholar_max_retries`

## `stats` 字段

统计信息：

- `dblp_candidates`
- `crossref_enriched`
- `semantic_scholar_enriched`
- `final_papers`
- `papers_with_abstract`
- `papers_with_doi`
- `papers_with_pdf`
- `keyword_hit_counts`
- `overlap_keyword_pairs`
- `generated_files`

## `papers` 字段

每篇论文统一为：

```json
{
  "title": "string",
  "authors": ["string"],
  "abstract": "string or null",
  "abstract_source": "semantic_scholar | crossref | existing | null",
  "crossref_abstract": "string or null",
  "doi": "string or null",
  "url": "string or null",
  "pdf_url": "string or null",
  "pdf_url_source": "semantic_scholar | existing | null",
  "journal": "string or null",
  "publication_year": 2025,
  "publication_date": "2025-08-01",
  "dblp_url": "string or null",
  "crossref_score": 88.2,
  "matched_keywords": ["formation control", "multi-UAV"],
  "source_tags": ["dblp", "crossref-doi", "semantic-scholar-title"],
  "chinese_summary": "string or null",
  "topic_tags": ["multi-robot", "control"],
  "recommendation_reason": "string or null",
  "rank_score": 15.3,
  "metadata_completeness": 9,
  "raw_venue": "ICRA",
  "semantic_scholar_paper_id": "string or null",
  "semantic_scholar_url": "string or null",
  "semantic_scholar_abstract": "string or null",
  "semantic_scholar_publication_date": "2025-05-19",
  "semantic_scholar_citation_count": 42,
  "semantic_scholar_fields_of_study": ["Computer Science", "Robotics"],
  "semantic_scholar_open_access_pdf_url": "string or null",
  "semantic_scholar_open_access_pdf_status": "OPEN_ACCESS | null",
  "semantic_scholar_match_score": 91.4
}
```

## Markdown / DOCX 报告章节

报告至少包含以下章节：

1. `检索任务说明`
2. `总体观察`
3. `单篇论文整理`
4. `关键词分组观察`
5. `推荐优先阅读列表`
6. `统计信息`

其中单篇论文至少新增展示：

- 摘要来源
- Semantic Scholar 页面链接（若有）
- 是否有开放获取 PDF 链接
- PDF 链接来源
- OA PDF 状态
- Citation Count（若有）
- Fields of Study（若有）
