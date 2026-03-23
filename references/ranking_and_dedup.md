# Ranking And Dedup

## 去重规则

去重顺序：

1. DOI 去重优先。
2. DOI 缺失时用标题标准化和相似度近似去重。
3. 多关键词重复命中只保留一条记录，合并 `matched_keywords`。
4. 多 venue 联合检索时，若同一篇论文在不同查询路径下重复命中，也只保留一条标准记录。
5. Semantic Scholar enrich 不改变 primary dedup 根规则，它只补充字段，不单独定义新的去重主键。

## 标题标准化

标准化步骤：

1. Unicode 规范化。
2. 转小写。
3. 去除多余空白。
4. 去掉常见标点。
5. 统一连字符和斜杠影响。

## 记录合并规则

1. 优先保留有 DOI 的记录。
2. 优先保留有摘要的记录。
3. `abstract` 最终优先级为：
   - `semantic_scholar_abstract`
   - `crossref_abstract`
   - existing abstract
4. `pdf_url` 最终优先级为：
   - `semantic_scholar_open_access_pdf_url`
   - existing `pdf_url`
5. 优先保留有正式发布日期的记录。
6. 优先保留能明确落入目标 venue 集合的记录。
7. 合并来源标签。
8. 合并关键词命中列表。
9. 合并 fields of study、subjects 和 topic tags。
10. 优先保留更长、更像正式题目的标题版本。

## 排序规则

综合因素包括：

1. `publication_year / publication_date`
2. 是否有摘要
3. 是否命中多个关键词
4. Crossref 信息完整度
5. Semantic Scholar enrich 后的元数据完整度
6. 是否存在开放获取 PDF 链接
7. citationCount 的弱辅助信号

说明：

1. Semantic Scholar enrich 会影响排序，但只是增强，不重写原有排序框架。
2. `citationCount` 只作为弱辅助信号，不能压过近期性和关键词相关性。
3. enrich 失败或缺失时，排序会自然退化回原有 DBLP + Crossref 行为。

## 推荐逻辑

推荐列表优先选择：

1. 最近发表的论文。
2. 摘要存在、便于快速判断价值的论文。
3. 同时命中多个关键词的交叉主题论文。
4. 元数据完整、可继续追踪 DOI 和链接的论文。
5. 如果存在 OA PDF 链接，会适度提高推荐优先级。
6. 排序理由应可解释，避免黑箱式推荐。
