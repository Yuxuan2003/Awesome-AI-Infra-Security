#!/usr/bin/env python3
"""字段迁移：把 summary（实为中文）改名为 summary_zh，为英文 summary 留位。
幂等：只处理「有 summary 且无 summary_zh」的条目。"""
import sys
from pathlib import Path
try:
    import yaml
except ImportError:
    sys.exit("pip install pyyaml")

ROOT = Path(__file__).resolve().parent.parent
f = ROOT / "data" / "papers.yaml"
data = yaml.safe_load(f.read_text(encoding="utf-8"))

moved = 0
for p in data["papers"]:
    if p.get("summary") and not p.get("summary_zh"):
        p["summary_zh"] = p.pop("summary")
        moved += 1

# 保持字段顺序：summary 在 summary_zh 前
def order(p):
    keys = ["id", "url", "title", "abbr", "date", "venue", "section", "boundary",
            "summary", "summary_zh", "code"]
    return {k: p[k] for k in keys if k in p}

data["papers"] = [order(p) for p in data["papers"]]
f.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=120),
             encoding="utf-8")
print(f"✓ 迁移 {moved} 篇：summary → summary_zh，英文 summary 留空待补")
