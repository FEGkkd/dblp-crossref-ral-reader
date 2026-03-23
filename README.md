# dblp-crossref-ral-reader

`dblp-crossref-ral-reader` 是一个可复用的 Codex skill，同时也是一个可直接运行的 Python 工具，用来在机器人论文 venue 中做公开元数据检索、补全、排序和中文总结输出。

它的主流程是：

- 用 `DBLP` 做候选论文召回和 venue 约束
- 用 `Crossref` 做 DOI / 标题驱动的元数据补全
- 可选用 `Semantic Scholar` 做摘要、引用数和开放获取 PDF 元数据 enrich
- 输出 `results.json`、`summary.md`、`summary.docx`

## 适用场景

适合这些任务：

- 检索 `RAL`、`TRO`、`TASE`、`IJRR`、`RSS`、`CoRL`、`ICRA`、`IROS` 上的近期论文
- 根据若干关键词构建结构化阅读清单
- 输出中文文献综述草稿或组会汇报材料
- 在不依赖 IEEE Xplore API 和网页抓取的前提下做公开元数据检索

## 支持的 venue

- `RAL` -> `IEEE Robotics and Automation Letters`
- `TRO` / `T-RO` -> `IEEE Transactions on Robotics`
- `TASE` / `T-ASE` -> `IEEE Transactions on Automation Science and Engineering`
- `IJRR` -> `The International Journal of Robotics Research`
- `RSS` -> `Robotics: Science and Systems`
- `CoRL` -> `Conference on Robot Learning`
- `ICRA` -> `IEEE International Conference on Robotics and Automation`
- `IROS` -> `IEEE/RSJ International Conference on Intelligent Robots and Systems`

默认 venue 是 `RAL`。

## 这个 skill 不做什么

- 不调用 IEEE Xplore 官方 API
- 不抓取 IEEE 网页
- 不依赖登录态或付费 API
- 不下载 PDF 文件本身
- 不解析 PDF 全文
- 不保证每篇论文都能命中 Semantic Scholar enrich

## 安装

### 1. 创建虚拟环境

```bash
python -m venv .venv
source .venv/bin/activate
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 验证环境

```bash
python scripts/validate_env.py   --output-dir ./outputs   --crossref-mailto your_email@example.com   --semantic-scholar-api-key-env SEMANTIC_SCHOLAR_API_KEY
```

`SEMANTIC_SCHOLAR_API_KEY` 不设置也能运行，只是更容易遇到限流。

## 快速开始

### 默认检索 RAL

```bash
python scripts/run_pipeline.py   --keywords "formation control" "multi-UAV" "reinforcement learning"   --days-back 365   --max-results 30   --output-dir ./outputs   --crossref-mailto your_email@example.com
```

### 联合检索多个 venue

```bash
python scripts/run_pipeline.py   --keywords "UAV exploration" "aerial exploration"   --journals RAL TRO ICRA IROS   --years-back 3   --max-results 80   --output-dir ./outputs_multi   --crossref-mailto your_email@example.com   --enable-semantic-scholar
```

### 使用 package CLI

```bash
python -m dblp_crossref_ral_reader.cli   --keywords "trajectory planning" "motion planning"   --journals ICRA IROS   --years-back 2   --max-results 20   --output-dir ./outputs_cli   --crossref-mailto your_email@example.com
```

## 输出内容

每次运行会在输出目录下创建一个时间戳子目录，例如：

```text
ral_search_YYYYMMDD_HHMMSS/
robot_journal_search_YYYYMMDD_HHMMSS/
```

其中包含：

- `results.json`
- `summary.md`
- `summary.docx`

`results.json` 中会保存：

- 检索配置
- 统计信息
- 每篇论文的标准化元数据
- 摘要来源和 PDF 链接来源
- Semantic Scholar enrich 字段
- 推荐阅读列表和关键词分组结果

## 目录结构

```text
.
├── README.md
├── SKILL.md
├── requirements.txt
├── scripts/
├── src/
├── references/
├── examples/
├── assets/
└── agents/
```

## 作为 Codex skill 使用

如果你在 Codex skill 环境中使用这个项目，优先阅读：

1. `SKILL.md`
2. `references/data_sources.md`
3. `references/ranking_and_dedup.md`
4. `scripts/run_pipeline.py`
5. `src/dblp_crossref_ral_reader/pipeline.py`
6. `src/dblp_crossref_ral_reader/semantic_scholar_client.py`

## 主要流程

1. 按关键词和 venue 从 DBLP 召回候选论文
2. 按 venue / DBLP path / container title 做过滤
3. 用 Crossref 做 DOI 优先、标题回退的补全
4. 做本地关键词匹配、去重、合并和排序
5. 对筛选后的论文做 Semantic Scholar enrich
6. 输出中文 JSON / Markdown / DOCX 报告

## 限制说明

- 这是一个公开元数据检索和整理工具，不是全文分析器
- `openAccessPdf.url` 只是公开元数据中的链接信号，不保证一定可访问
- 推荐结果是启发式排序，不替代正式的人工文献综述
