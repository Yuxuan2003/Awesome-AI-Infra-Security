#!/usr/bin/env python3
"""
arXiv 检索 —— 按「系统级形态词 × 系统安全词 × 章节分类键」三层交集召回。

用法：
    python3 scripts/fetch.py --start 2026-09-05 --end 2026-09-11        # 周更窗口
    python3 scripts/fetch.py --start 2025-01-01 --end 2026-09-04 --count # 只看存量
    python3 scripts/fetch.py --section 2.1 --start ... --end ...        # 只查某节
    python3 scripts/fetch.py --start ... --end ... --loose              # 放宽口径

━━━━━━━━━━━━━━━ 口径设计（本方向最关键的工程问题）━━━━━━━━━━━━━━━

AI Infra Security 的检索噪音比 GUI Agent 安全大一个量级。实测同一方向
（2025-01 ~ 2026-09）不同口径差 8 倍：

    宽形态 × 宽安全 ................ 2091 篇
    宽形态 × 严安全 ................  965
    严形态 × 宽安全 ................ 1002
    严形态 × 严安全 ................  519
    + 限 cs.CR/DC/OS/AR/NI .........  260   ← 本脚本默认口径
    仅 cs.CR .......................   88

**交付任何存量数字都必须连口径一起报**，否则下次复核对不上。

四个已实测的坑：

1. `adversarial` / `safety` / `privacy` 在本方向是灌水词（各带入 140/190/225 篇）——
   它们是**模型层**安全论文的标配。系统安全应改用 side channel / denial-of-service /
   multi-tenant / isolation / confidentiality / information flow。

2. **`disaggregated` 被跨域同名重度污染**：O-RAN（"disaggregated 6G radio access
   networks"）与统计学（"spatial / temporal disaggregation"）。抽样 60 篇里 5 篇是
   这类噪音。已从形态词中移除，改用 prefill-decode / expert parallel 等精确术语。
   同类高危词：router（网络路由器）、scheduling（通用运筹）、GPU（任何用 GPU 的论文）。

3. **限定主分类是提精度最有效的手段**（519 → 260）。但要按章节选：
   侧信道 / DoS / 隔离 → cs.CR, cs.DC, cs.OS, cs.AR；
   第 3 章（优化→safety 漂移）与 2.3（MoE routing × safety）主要在 cs.CL / cs.LG，
   限 cs.CR 会漏掉大半 —— 这两节在 SEC_MODEL / CAT_MODEL 里单独处理。

4. **只看 totalResults 会严重误判，必须抽样判精度**。宽口径 60 篇里真命中仅约 6 篇
   （精度 10%）。本脚本默认打印标题+摘要片段供人工筛，不要跳过这一步。

反向验证（skill 方法论第 1 步）：取 10 篇已知确属本方向的论文测命中率，
实测 9/10 = 90%（漏的那篇用 "LLM API reseller" 而非标准形态词），
≥80% 判据通过，确认 260 是真实体量而非 query 缺陷。
"""
import argparse
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("需要 PyYAML：pip install pyyaml")

ROOT = Path(__file__).resolve().parent.parent
API = "https://export.arxiv.org/api/query"   # 必须 HTTPS，http 返回 301
SLEEP = 3.2

# ── 系统级形态词：必须出现 serving/training 系统实体 ──
# 已移除 "disaggregated"（O-RAN 与统计学污染）与裸 "LLM training"（过泛）
INFRA = [
    'abs:"LLM serving"', 'abs:vLLM', 'abs:SGLang', 'abs:"KV cache"', 'abs:"KV-cache"',
    'abs:"inference engine"', 'abs:"serving system"', 'abs:"inference server"',
    'abs:"prefix caching"', 'abs:"prefix cache"', 'abs:"continuous batching"',
    'abs:PagedAttention', 'abs:"expert parallel"', 'abs:"prefill-decode"',
    'abs:"LLM inference"',
]

# ── 系统安全词：不含 safety / adversarial / privacy ──
SEC_SYS = [
    'abs:"side channel"', 'abs:"side-channel"', 'abs:"timing attack"',
    'abs:"denial-of-service"', 'abs:"multi-tenant"', 'abs:isolation',
    'abs:leakage', 'abs:confidentiality', 'abs:"information flow"',
    'abs:vulnerability', 'abs:exploit', 'abs:"cross-tenant"',
]

# ── 模型层安全词：仅第 3 章与 2.3 节使用 ──
SEC_MODEL = [
    'abs:safety', 'abs:alignment', 'abs:refusal', 'abs:jailbreak',
    'abs:guardrail', 'abs:backdoor',
]

CAT_SYS = ['cat:cs.CR', 'cat:cs.DC', 'cat:cs.OS', 'cat:cs.AR', 'cat:cs.NI']
CAT_MODEL = ['cat:cs.CL', 'cat:cs.LG', 'cat:cs.CR', 'cat:cs.AI']

# 这两节的工作主要投 cs.CL / cs.LG，用模型层安全词 + 对应分类
MODEL_LAYER_SECTIONS = {"3", "2.3"}


def orx(terms):
    return "(" + " OR ".join(terms) + ")"


def build_query(section_queries, section_id, loose=False):
    infra = orx(INFRA)
    if section_id in MODEL_LAYER_SECTIONS:
        sec, cat = orx(SEC_MODEL), orx(CAT_MODEL)
    else:
        sec, cat = orx(SEC_SYS), orx(CAT_SYS)

    parts = [infra, sec]
    if section_queries:
        parts.append(orx(section_queries))
    q = " AND ".join(parts)
    if not loose:
        q += f" AND {cat}"
    return q


def fetch(query, start, end, max_results=100, count_only=False):
    sq = f"({query}) AND submittedDate:[{start}0000 TO {end}2359]"
    params = {
        "search_query": sq, "start": 0,
        "max_results": 1 if count_only else max_results,
        "sortBy": "submittedDate", "sortOrder": "descending",
    }
    url = API + "?" + urllib.parse.urlencode(params)
    for attempt in range(3):
        try:
            raw = urllib.request.urlopen(url, timeout=90).read().decode()
            break
        except Exception:
            if attempt == 2:
                return -1, []
            time.sleep(8)
    else:
        return -1, []

    m = re.search(r"opensearch:totalResults[^>]*>(\d+)<", raw)
    total = int(m.group(1)) if m else -1
    if count_only:
        return total, []

    out = []
    for e in re.findall(r"<entry>(.*?)</entry>", raw, re.S):
        aid = re.search(r"<id>http://arxiv\.org/abs/([\d.]+)", e)
        t = re.search(r"<title>(.*?)</title>", e, re.S)
        p = re.search(r"<published>(.*?)</published>", e)
        s = re.search(r"<summary>(.*?)</summary>", e, re.S)
        c = re.search(r'<arxiv:primary_category[^>]*term="([^"]+)"', e)
        if not (aid and t):
            continue
        out.append({
            "id": aid.group(1),
            "title": " ".join(t.group(1).split()),
            "published": p.group(1)[:10] if p else "?",
            "cat": c.group(1) if c else "?",
            "summary": " ".join(s.group(1).split()) if s else "",
        })
    return total, out


def existing_ids():
    f = ROOT / "data" / "papers.yaml"
    if not f.exists():
        return set()
    papers = yaml.safe_load(f.read_text(encoding="utf-8"))["papers"]
    return {str(p["id"]) for p in papers if p.get("id")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", required=True, help="YYYY-MM-DD")
    ap.add_argument("--end", required=True, help="YYYY-MM-DD")
    ap.add_argument("--section", help="只查某节，如 2.1")
    ap.add_argument("--count", action="store_true", help="只统计数量，不列条目")
    ap.add_argument("--loose", action="store_true", help="不限主分类（放宽口径）")
    args = ap.parse_args()

    start = args.start.replace("-", "")
    end = args.end.replace("-", "")

    secs = yaml.safe_load((ROOT / "data" / "sections.yaml").read_text(encoding="utf-8"))
    known = existing_ids()

    nodes = []
    for s in secs["sections"]:
        kids = s.get("children") or []
        if kids:
            nodes += [(c["id"], c["title"], c.get("queries") or []) for c in kids]
        else:
            nodes.append((s["id"], s["title"], s.get("queries") or []))

    if args.section:
        nodes = [n for n in nodes if n[0] == args.section]
        if not nodes:
            sys.exit(f"章节 {args.section} 不存在")

    print(f"窗口 {args.start} ~ {args.end}　"
          f"口径：{'放宽（不限分类）' if args.loose else '默认（限主分类）'}")
    print("=" * 78)

    seen = set()
    grand = 0
    for sid, title, queries in nodes:
        if not queries:
            print(f"\n[{sid}] {title} —— 无 arXiv 检索词（非 arXiv 来源章节，跳过）")
            continue

        q = build_query(queries, sid, args.loose)
        total, items = fetch(q, start, end, count_only=args.count)
        grand += max(total, 0)

        fresh = [i for i in items if i["id"] not in known and i["id"] not in seen]
        for i in fresh:
            seen.add(i["id"])

        print(f"\n[{sid}] {title}")
        print(f"  召回 {total} 篇" + ("" if args.count else f"，去重后新增 {len(fresh)} 篇"))

        for i in fresh:
            print(f"    {i['published']} {i['cat']:<9} {i['id']}")
            print(f"      {i['title'][:96]}")
            print(f"      {i['summary'][:170]}...")
        time.sleep(SLEEP)

    print("\n" + "=" * 78)
    print(f"合计召回 {grand} 篇（含跨节重叠），去重后待筛 {len(seen)} 篇")
    print()
    print("⚠️  人工筛选环节不可省。GUI 库那轮实测：9 篇召回全部命中形态词，")
    print("    但近半不属收录范围。本方向噪音更大，务必逐条核对三条收录边界：")
    print("      1. Security-of-AI 而非 AI-for-Security")
    print("      2. infra 层而非纯模型层")
    print("      3. 作用点在基础设施上，而非换个环境重跑的通用越狱")


if __name__ == "__main__":
    main()
