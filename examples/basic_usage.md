# Basic Usage

## 目标

检索 `RAL + T-RO` 中与 `formation control`、`multi-UAV` 相关的近期论文，并输出中文总结。

## 命令

```bash
python scripts/run_pipeline.py   --keywords "formation control" "multi-UAV"   --journals RAL TRO   --days-back 3650   --max-results 20   --output-dir ./outputs   --crossref-mailto your_email@example.com
```

## 结果

输出目录示例：

```text
./outputs/robot_journal_search_20260321_153000/
├── results.json
├── summary.md
└── summary.docx
```

也可以把会议作为来源范围，例如 `--journals ICRA IROS`。
