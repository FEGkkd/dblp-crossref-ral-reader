# Sample Commands

## 近一年多关键词检索，默认 RAL

```bash
python -m dblp_crossref_ral_reader.cli   --keywords "formation control" "multi-UAV" "reinforcement learning"   --days-back 365   --max-results 30   --output-dir ./outputs   --crossref-mailto your_email@example.com
```

## 联合检索 RAL 和 T-RO

```bash
python -m dblp_crossref_ral_reader.cli   --keywords "formation control" "swarm"   --journals RAL TRO   --days-back 3650   --max-results 30   --output-dir ./outputs_multi   --crossref-mailto your_email@example.com
```

## 检索 T-RO 和 T-ASE，优先保留有摘要的结果

```bash
python -m dblp_crossref_ral_reader.cli   --keywords "legged robot" "imitation learning"   --journals TRO TASE   --years-back 3   --max-results 25   --require-abstract   --output-dir ./outputs   --crossref-mailto your_email@example.com
```

## 检索 ICRA 和 IROS

```bash
python -m dblp_crossref_ral_reader.cli   --keywords "trajectory planning" "motion planning"   --journals ICRA IROS   --years-back 2   --max-results 20   --output-dir ./outputs_icra_iros   --crossref-mailto your_email@example.com
```

## 只生成 JSON 和 Markdown

```bash
python -m dblp_crossref_ral_reader.cli   --keywords "shared autonomy"   --journals RAL   --days-back 730   --max-results 15   --output-dir ./outputs   --crossref-mailto your_email@example.com   --no-save-docx
```
