#!/usr/bin/env python3
"""给没有 summary 字段的条目，用 summary_zh 初始化英文 summary 占位（等待人工/subagent 完善）"""
import sys
from pathlib import Path
try:
    import yaml
except ImportError:
    sys.exit("pip install pyyaml")

ROOT = Path(__file__).resolve().parent.parent
f = ROOT / "data" / "papers.yaml"
papers = yaml.safe_load(f.read_text(encoding="utf-8"))["papers"]

need = [p for p in papers if not p.get("summary")]
have = [p for p in papers if p.get("summary")]
print(f"已有英文 summary: {len(have)} 篇")
print(f"缺英文 summary（待补）: {len(need)} 篇")
for p in need:
    print(f"  - {p.get('abbr') or p['title'][:50]}")
