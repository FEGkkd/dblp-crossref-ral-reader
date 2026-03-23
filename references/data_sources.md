# Data Sources

## 三层分工

本技能现在采用三层公开元数据流水线：

1. `DBLP`：venue / candidate retrieval
2. `Crossref`：publication metadata enrichment
3. `Semantic Scholar`：abstract + OA PDF enrichment

## DBLP 的角色

DBLP 是本技能的来源范围锁定层和候选论文发现层。

职责：

1. 使用公开搜索接口检索论文候选项。
2. 尽量将候选项限制到用户请求的目标 venue 集合，而不是全库泛搜。
3. 当前内置支持：`RAL`、`T-RO`、`T-ASE`、`ICRA`、`IROS`。
4. 提供基础元数据：
   - title
   - authors
   - year
   - venue
   - dblp_url
   - doi（若 DBLP 记录提供）

## Crossref 的角色

Crossref 是本技能的正式元数据补全层。

职责：

1. 优先通过 DOI 查询单篇论文的更完整元数据。
2. DOI 缺失时通过标题查询补全信息。
3. 对标题回查结果继续校验 venue 归属，避免错补到非目标来源。
4. 尽量提供：
   - abstract
   - DOI
   - URL
   - container-title
   - published-print / published-online / issued
   - subject
   - type
   - publisher

## Semantic Scholar 的角色

Semantic Scholar 是本技能的 enrich 层，不参与主检索召回。

职责：

1. 只对已经过 DBLP + Crossref + 本地过滤/去重后的论文做 enrich。
2. 优先补充：
   - abstract
   - Semantic Scholar 页面链接
   - publicationDate
   - openAccessPdf.url
   - openAccessPdf.status
3. 可选补充：
   - citationCount
   - fieldsOfStudy
4. 即使没有命中或请求失败，也不能破坏 DBLP + Crossref 主流程。

## 为什么不用 IEEE API

1. 用户约束不允许使用 IEEE Xplore 官方 API。
2. 减少账号、密钥、权限管理成本。
3. 降低部署门槛，便于复用。
4. 保持与公开元数据工作流一致。

## 为什么不做网页抓取

1. 用户约束明确禁止。
2. 网页结构不稳定，维护成本高。
3. 爬取可能涉及合规和访问策略问题。
4. 本技能目标是可长期复用的公共元数据检索流水线，而不是高耦合网页抓取器。

## 数据源边界

本技能的结论和报告只基于：

1. DBLP 返回的公开论文元数据
2. Crossref 返回的公开论文元数据
3. Semantic Scholar 返回的公开 enrich 元数据
4. 本地关键词匹配、去重、排序和总结规则

不包含：

1. PDF 全文分析
2. IEEE 页面结构化解析
3. 引文网络抓取
4. 需要认证的私有数据
5. PDF 文件下载本身
