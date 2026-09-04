#!/usr/bin/env python3
"""
从 data/papers.yaml + data/sections.yaml 生成（双语）：
  - README.md        英文主版
  - README.zh.md     中文副版
  - views/by-section/<id>.md    英文
  - views/by-boundary/<boundary>.md  英文
  - 攻击面 × 信任边界 交叉矩阵（嵌在两个 README 中）

用法：
    python3 scripts/build.py           # 生成
    python3 scripts/build.py --check   # 只校验，不写文件（CI 用）

设计约定：
  - README 与 views/ 都是产物，绝不手工编辑
  - 根目录只有两个 README 是 md，其余文档在 docs/，分组视图在 views/
  - 条目双简介：summary（英文）是主版本，summary_zh（中文）生成副版
"""
import argparse
import re
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("需要 PyYAML：pip install pyyaml")

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

REPO = "Yuxuan2003/Awesome-AI-Infra-Security"


def load():
    papers = yaml.safe_load((DATA / "papers.yaml").read_text(encoding="utf-8"))["papers"]
    secs = yaml.safe_load((DATA / "sections.yaml").read_text(encoding="utf-8"))
    return papers, secs


def flatten(sections, lang="zh"):
    """展平章节树，返回 [(id, title, desc, stock, is_leaf, depth)]。
    lang=en 时用 title_en/desc_en，缺则退回中文。"""
    out = []

    def pick(node):
        if lang == "en":
            return (node.get("title_en") or node["title"],
                    node.get("desc_en") or node.get("desc"))
        return node["title"], node.get("desc")

    for s in sections:
        kids = s.get("children") or []
        t, dsc = pick(s)
        out.append((s["id"], t, dsc, s.get("stock"), not kids, 0))
        for c in kids:
            ct, cd = pick(c)
            out.append((c["id"], ct, cd, c.get("stock"), True, 1))
    return out


def validate(papers, secs):
    """返回错误列表。CI 靠这个拦住脏数据。"""
    errs = []
    valid_secs = {i for i, *_ in flatten(secs["sections"])}
    valid_bounds = {b["id"] for b in secs["boundaries"]}
    seen_ids, seen_titles, seen_urls = {}, {}, {}

    for idx, p in enumerate(papers):
        tag = p.get("abbr") or p.get("title", "")[:40] or f"#{idx}"

        for f in ("title", "date", "section", "boundary", "summary"):
            if not p.get(f):
                errs.append(f"[{tag}] 缺少必填字段 {f}")

        if not p.get("id") and not p.get("url"):
            errs.append(f"[{tag}] 必须有 id（arXiv）或 url（非 arXiv 来源）之一")

        aid = p.get("id")
        if aid:
            if not re.fullmatch(r"\d{4}\.\d{4,5}", str(aid)):
                errs.append(f"[{tag}] arXiv ID 格式非法：{aid}（不应带版本号）")
            if "XXXXX" in str(aid).upper():
                errs.append(f"[{tag}] arXiv ID 是占位符未回填：{aid}")
            if aid in seen_ids:
                errs.append(f"[{tag}] arXiv ID 与 [{seen_ids[aid]}] 重复：{aid}")
            seen_ids[aid] = tag

        u = p.get("url")
        if u:
            if not str(u).startswith("http"):
                errs.append(f"[{tag}] url 必须是完整链接：{u}")
            if u in seen_urls:
                errs.append(f"[{tag}] url 与 [{seen_urls[u]}] 重复")
            seen_urls[u] = tag

        t = re.sub(r"\W+", "", p.get("title", "")).lower()
        if t and t in seen_titles:
            errs.append(f"[{tag}] 标题与 [{seen_titles[t]}] 近似重复")
        seen_titles[t] = tag

        d = str(p.get("date") or "")
        if d:
            if not re.fullmatch(r"\d{4}-\d{2}", d):
                errs.append(f"[{tag}] date 应为 YYYY-MM：{d}")
            elif not 1 <= int(d[5:7]) <= 12:
                errs.append(f"[{tag}] date 月份非法：{d}")

        if p.get("section") and str(p["section"]) not in valid_secs:
            errs.append(f"[{tag}] section 未定义：{p['section']}")

        # 非叶子章节不应直接挂论文
        leaf_secs = {i for i, _t, _d, _s, is_leaf, _dp in flatten(secs["sections"]) if is_leaf}
        if p.get("section") and str(p["section"]) in valid_secs \
                and str(p["section"]) not in leaf_secs:
            errs.append(f"[{tag}] section {p['section']} 是父章节，论文须挂在叶子小节")

        for b in p.get("boundary") or []:
            if b not in valid_bounds:
                errs.append(f"[{tag}] boundary 未定义：{b}")

        s = (p.get("summary") or "").strip()
        if not s:
            errs.append(f"[{tag}] 缺少 summary（英文简介，README.md 主版需要）")
        elif len(s) < 60:
            errs.append(f"[{tag}] 英文简介过短（{len(s)} 字符），惯例含动机/机制/关键数字")
        sz = (p.get("summary_zh") or "").strip()
        if not sz:
            errs.append(f"[{tag}] 缺少 summary_zh（中文副版 README 需要）")
        elif len(sz) < 50:
            errs.append(f"[{tag}] 中文简介过短（{len(sz)} 字），惯例 150–300 字")
    return errs


B = {
    "en": {
        "summary": "Summary", "boundary": "Trust boundary", "venue": "Venue",
        "arxiv": "arXiv", "link": "Link", "code": "Code",
        "empty": "*No entries yet*",
        "welcome": " (see MAINTENANCE for the measured arXiv stock of this section — PRs welcome)",
    },
    "zh": {
        "summary": "简介", "boundary": "信任边界", "venue": "发表",
        "arxiv": "arXiv", "link": "链接", "code": "代码",
        "empty": "*本节暂无收录条目*",
        "welcome": "（该节实测存量见 docs/MAINTENANCE.md，欢迎 PR）",
    },
}


def entry(p, bound_label, lang="en"):
    """渲染单条目。lang=en 用 summary（英文），lang=zh 用 summary_zh。"""
    L = B[lang]
    head = p["title"]
    if p.get("abbr"):
        head += f" ({p['abbr']})"
    head += f" ({p['date']})"

    text = (p["summary_zh"] if lang == "zh" else p["summary"]) or ""
    colon = "：" if lang == "zh" else ": "
    pipe = " ｜ " if lang == "zh" else " · "
    lines = [f"#### {head}", f"- **{L['summary']}**{colon}{' '.join(text.split())}"]

    joiner = "、" if lang == "zh" else ", "
    bounds = joiner.join(bound_label.get(b, b) for b in (p.get("boundary") or []))
    meta = f"- **{L['boundary']}**{colon}{bounds}"
    if p.get("venue") and p["venue"] != "arXiv":
        meta += f"{pipe}**{L['venue']}**{colon}{p['venue']}"
    lines.append(meta)

    if p.get("id"):
        lines.append(f"- **{L['arxiv']}**{colon}[{p['id']}](https://arxiv.org/abs/{p['id']})")
    elif p.get("url"):
        lines.append(f"- **{L['link']}**{colon}{p['url']}")
    if p.get("code"):
        lines.append(f"- **{L['code']}**{colon}{p['code']}")
    return "\n".join(lines)


def sort_key(p):
    """同节内按 v1 日期倒序（新的在前）。"""
    return (p.get("date", ""), p.get("id", "") or p.get("url", ""))


def anchor_of(sid, title):
    """GitHub 风格锚点：小写、去标点、空格转连字符。
    注意标题里的 '/' 必须去掉，否则锚点失效（GUI 库实测踩过）。"""
    s = f"{sid} {title}".lower()
    s = re.sub(r"[^\w\s\u4e00-\u9fff-]", "", s)
    return re.sub(r"\s+", "-", s.strip())


def build_matrix(papers, secs, lang="zh"):
    """攻击面 × 信任边界 交叉矩阵 —— 这是本仓库与竞品扁平标签的核心区别。"""
    bounds = secs["boundaries"]
    tops = [s for s in secs["sections"] if s["id"] != "7"]

    blabel = (lambda b: b.get("title_en", b["title"])) if lang == "en" \
        else (lambda b: b["title"])
    tlabel = (lambda s: s.get("title_en", s["title"])) if lang == "en" \
        else (lambda s: s["title"])

    sec2top = {}
    for s in secs["sections"]:
        sec2top[s["id"]] = s["id"]
        for c in s.get("children") or []:
            sec2top[c["id"]] = s["id"]

    grid = defaultdict(lambda: defaultdict(int))
    for p in papers:
        top = sec2top.get(str(p["section"]))
        for b in p.get("boundary") or []:
            grid[top][b] += 1

    header = "Attack surface \\ Trust boundary" if lang == "en" else "攻击面 \\ 信任边界"
    L = []
    L.append(f"| {header} | " + " | ".join(blabel(b) for b in bounds) + " |")
    L.append("|---|" + "---|" * len(bounds))
    for s in tops:
        row = [f"**{s['id']} {tlabel(s)}**"]
        for b in bounds:
            n = grid[s["id"]][b["id"]]
            row.append(str(n) if n else "·")
        L.append("| " + " | ".join(row) + " |")
    return "\n".join(L)


# ── 正文文案模板（README 开头几节，两种语言各一套） ──
INTRO = {
    "en": {
        "tagline": "A curated list of AI infrastructure security papers — attack surfaces, trust boundaries and defenses across the LLM inference & training stack, with an English summary for each entry.",
        "switch": "**[English](README.md)** ｜ [中文](README.zh.md)",
        "why_title": "Why this list",
        "why_1": "What makes AI infrastructure distinctive: **the semantics of user input directly determines the underlying compute topology, cache state, GPU memory footprint, scheduling behavior and network traffic.**",
        "why_2": "In a conventional web/cloud stack, request content is largely decoupled from low-level resource state. In LLM infra, a single prompt simultaneously shapes KV allocation, prefix-cache hits, batch composition, preemption, MoE expert routing and inter-GPU communication — **input controls not only the model's output but the state of the infrastructure itself.** An attacker can therefore manipulate the system through perfectly legitimate API requests.",
        "why_3": "This produces a class of problems that conventional system-security taxonomies struggle to place:",
        "why_bullets": [
            "Performance optimizations become privacy side channels (KV prefix sharing → cross-tenant prompt inference)",
            "Model semantics determine physical execution paths (MoE routing → GPU/NIC load → observable side channels)",
            "Attack targets shift from compute to state machines (a few requests manipulate the scheduler instead of saturating GPUs)",
            "Deployment optimizations quietly change model safety (perplexity unchanged after quantization, but refusals collapse)",
            "Local corruption amplifies into global pollution (one rank's faulty tensor propagates through collectives into the checkpoint)",
        ],
        "scope_title": "What this list covers",
        "scope_1": "Only work whose **primary object of study is the LLM inference / training infrastructure itself**, organized along two axes: *attack surface × trust boundary*.",
        "excl_title": "**Not covered** (the three boundaries that fail most often):",
        "excl": [
            "**AI-for-Security** — e.g. using an MoE for malware classification, penetration testing, vulnerability discovery. This list is Security-of-AI only.",
            "**Pure model-layer work** — the paper must engage the state, resources or topology of a serving/training system. Alignment work that only touches weights and outputs does not qualify.",
            "**Generic jailbreaks re-run in a new deployment setting** — the attack or defense must act on the infrastructure itself.",
        ],
        "org_title": "Why organize by attack surface × trust boundary, not topic tags",
        "org_1": "Existing large LLM-safety lists tag entries by submission topic (jailbreak / privacy / watermark …). Infra-layer work ends up scattered: a KV-cache side channel and a network-traffic fingerprint share the same side-channel section even though the attacker's capability, the defense location and the affected system components are entirely different.",
        "org_2": "This list takes the **attack surface** (where in the system stack: KV / scheduler / routing / interconnect / training collectives) as the primary axis, and the **trust boundary** (cross-tenant / cross-request / host-device / inter-node / supply-chain / model-internal) as a cross-cutting tag.",
        "org_3": "The reason: the same attack surface has very different severity at different trust boundaries. KV leakage is nearly harmless in single-tenant self-hosting but a serious privacy incident in multi-tenant serving. Only by labelling both dimensions can a reader tell whether a paper is relevant to their own deployment.",
        "matrix_title": "Attack surface × trust boundary distribution",
        "toc_title": "Contents",
        "browse": "Browse by trust boundary: ",
        "contrib_title": "Contributing",
        "contrib": "You only ever edit `data/papers.yaml`; `README.md`, `README.zh.md` and everything under `views/` are regenerated by GitHub Actions. Scope and entry format: [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md). Maintenance process and retrieval calibration: [docs/MAINTENANCE.md](docs/MAINTENANCE.md).",
        "related_title": "Related lists",
        "related_intro": "This list focuses on the security of LLM infrastructure itself. For adjacent areas:",
        "related": [
            "GUI / computer-use agent security: `Yuxuan2003/Awesome-GUI-Agent-Security`",
            "Broad LLM safety & privacy (mostly model-layer): `ThuCCSLab/Awesome-LM-SSP`",
            "LLM inference systems, capability-oriented: `AmadeusChan/Awesome-LLM-System-Papers`",
            "Model compression & quantization (efficiency-only): `HuangOwen/Awesome-LLM-Compression`",
        ],
    },
    "zh": {
        "tagline": "AI Infra 安全论文清单 —— LLM 推理与训练基础设施的攻击面、信任边界与防御，每篇附中文简介",
        "switch": "[English](README.md) ｜ **[中文](README.zh.md)**",
        "why_title": "为什么需要这个清单",
        "why_1": "AI Infra 最大的特殊性是：**用户输入的语义，会直接决定底层计算拓扑、缓存状态、GPU 内存占用、调度行为和网络通信。**",
        "why_2": "普通 Web / Cloud 里，request content 与底层 resource state 通常相对解耦。但在 LLM Infra 里，一段 prompt 会同时影响 KV 分配、prefix 命中、batch 组成、抢占行为、MoE 专家路由与 GPU 间通信 —— 也就是说，**输入不仅控制模型输出，还间接控制基础设施状态**。于是攻击者可以通过完全合法的 API 请求去操纵系统。",
        "why_3": "由此产生了一批传统系统安全分类学难以归置的问题：",
        "why_bullets": [
            "性能优化直接变成隐私侧信道（KV prefix 共享 → 跨租户 prompt 推断）",
            "模型语义决定物理执行路径（MoE routing → GPU/NIC 负载 → 可观测侧信道）",
            "攻击目标从算力转向状态机（少量请求操纵调度器，而非压垮 GPU）",
            "部署优化悄悄改变模型安全性（量化后 perplexity 不变但拒答行为崩塌）",
            "本地损坏放大为全局污染（单个 rank 的错误张量经 collective 写入 checkpoint）",
        ],
        "scope_title": "这个仓库收录什么",
        "scope_1": "只收录**以 LLM 推理 / 训练基础设施本身为主要研究对象**的安全工作，按「攻击面 × 信任边界」二维组织。",
        "excl_title": "**不收录**（三条最容易失守的边界）：",
        "excl": [
            "**用 AI 做安全工作**（AI-for-Security）—— 如「用 MoE 做恶意软件分类」、渗透测试、漏洞挖掘。本仓库只收 Security-of-AI",
            "**纯模型层工作** —— 必须涉及 serving / training 系统的状态、资源或拓扑。只在模型权重与输出层面讨论对齐的研究不收",
            "**换个部署环境重跑的通用越狱** —— 攻击或防御的作用点必须在基础设施上",
        ],
        "org_title": "为什么按「攻击面 × 信任边界」而不按主题标签组织",
        "org_1": "现有的 LLM 安全大盘清单大多按投稿主题贴扁平标签（jailbreak / privacy / watermark …），结果是 infra 层的工作被打散：KV cache 侧信道与网络流量指纹因为同属 side-channel 而被放进同一节，而它们的攻击者能力、防御位置和受影响的系统组件完全不同。",
        "org_2": "本仓库以**攻击面**（系统栈上的位置：KV / scheduler / routing / interconnect / 训练 collective）为一级维度，以**信任边界**（跨租户 / 跨请求 / 主机-设备 / 节点间 / 供应链 / 模型内部）为交叉标签。",
        "org_3": "这样做的理由是：同一个攻击面在不同信任边界下的严重性完全不同。KV 泄露在单租户自部署里几乎无害，在多租户 serving 里是重大隐私事故。只有同时标注这两个维度，读者才能判断一篇工作是否与自己的部署形态相关。",
        "matrix_title": "攻击面 × 信任边界 分布",
        "toc_title": "目录",
        "browse": "按信任边界浏览：",
        "contrib_title": "贡献",
        "contrib": "只需修改 `data/papers.yaml`，`README.md`、`README.zh.md` 与 `views/` 下所有文件由 GitHub Actions 自动生成。收录标准与条目格式见 [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md)，维护流程与检索口径见 [docs/MAINTENANCE.md](docs/MAINTENANCE.md)。",
        "related_title": "相关仓库",
        "related_intro": "本仓库聚焦 LLM 基础设施自身的安全，以下方向请见：",
        "related": [
            "GUI / Computer-Use Agent 安全：`Yuxuan2003/Awesome-GUI-Agent-Security`",
            "LLM 安全与隐私大盘（模型层为主）：`ThuCCSLab/Awesome-LM-SSP`",
            "LLM 推理系统能力向研究：`AmadeusChan/Awesome-LLM-System-Papers`",
            "模型压缩与量化（纯效率视角）：`HuangOwen/Awesome-LLM-Compression`",
        ],
    },
}


def build_readme(papers, secs, lang="zh"):
    T = INTRO[lang]
    bound_label = ({b["id"]: b.get("title_en", b["title"]) for b in secs["boundaries"]}
                   if lang == "en" else
                   {b["id"]: b["title"] for b in secs["boundaries"]})
    by_sec = defaultdict(list)
    for p in papers:
        by_sec[str(p["section"])].append(p)

    total = len(papers)
    rounded = total // 10 * 10
    badge_papers = f"{rounded}%2B" if rounded >= 10 else str(total)
    ym = date.today().strftime("%Y.%m")

    L = []
    L.append("# Awesome-AI-Infra-Security")
    L.append("")
    L.append(T["switch"])
    L.append("")
    L.append(f"> {T['tagline']}")
    L.append("")
    L.append(
        f"![Last Update](https://img.shields.io/badge/last%20update-{ym}-brightgreen) "
        f"![Papers](https://img.shields.io/badge/papers-{badge_papers}-blue) "
        f"![Time Range](https://img.shields.io/badge/time-2025.01--{ym}-orange) "
        f"[![Link Check](https://github.com/{REPO}/actions/workflows/check.yml/badge.svg)]"
        f"(https://github.com/{REPO}/actions/workflows/check.yml) "
        "![Awesome](https://img.shields.io/badge/-awesome-ff69b4)"
    )
    L.append("")
    L.append(f"## {T['why_title']}")
    L.append("")
    L.append(T["why_1"])
    L.append("")
    L.append(T["why_2"])
    L.append("")
    L.append(T["why_3"])
    L.append("")
    for b in T["why_bullets"]:
        L.append(f"- {b}")
    L.append("")
    L.append(f"## {T['scope_title']}")
    L.append("")
    L.append(T["scope_1"])
    L.append("")
    L.append(T["excl_title"])
    L.append("")
    for i, e in enumerate(T["excl"], 1):
        L.append(f"{i}. {e}")
    L.append("")
    L.append(f"## {T['org_title']}")
    L.append("")
    L.append(T["org_1"])
    L.append("")
    L.append(T["org_2"])
    L.append("")
    L.append(T["org_3"])
    L.append("")
    L.append(f"### {T['matrix_title']}")
    L.append("")
    L.append(build_matrix(papers, secs, lang))
    L.append("")
    L.append(f"## {T['toc_title']}")
    L.append("")
    for sid, title, _desc, _stock, is_leaf, depth in flatten(secs["sections"], lang):
        L.append(f"{'  ' * depth}- [{sid} {title}](#{anchor_of(sid, title)})")
    L.append("")
    blabel = ({b["id"]: b.get("title_en", b["title"]) for b in secs["boundaries"]}
              if lang == "en" else {b["id"]: b["title"] for b in secs["boundaries"]})
    L.append(T["browse"] + " ｜ ".join(
        f"[{blabel[b['id']]}](views/by-boundary/{b['id']}.md)" for b in secs["boundaries"]))
    L.append("")
    L.append("---")
    L.append("")

    B_ = B[lang]
    for sid, title, desc, stock, is_leaf, depth in flatten(secs["sections"], lang):
        L.append(f"{'#' * (2 + depth)} {sid} {title}")
        L.append("")
        if desc:
            L.append(f"*{' '.join(str(desc).split())}*")
            L.append("")

        if not is_leaf:
            continue

        items = sorted(by_sec.get(sid, []), key=sort_key, reverse=True)
        if items:
            for p in items:
                L.append(entry(p, bound_label, lang))
                L.append("")
        else:
            note = B_["empty"]
            if stock:
                note += (f"（arXiv 存量约 {stock} 篇待整理，欢迎 PR）" if lang == "zh"
                         else f" (arXiv stock ~{stock}, to be curated — PRs welcome)")
            L.append(note)
            L.append("")

    L.append("---")
    L.append("")
    L.append(f"## {T['contrib_title']}")
    L.append("")
    L.append(T["contrib"])
    L.append("")
    L.append(f"## {T['related_title']}")
    L.append("")
    L.append(T["related_intro"])
    L.append("")
    for r in T["related"]:
        L.append(f"- {r}")
    L.append("")
    return "\n".join(L) + "\n"


def build_group(papers, heading, bound_label, note=None, lang="en"):
    L = [f"# {heading}", ""]
    if note:
        L += [note, ""]
    L.append("> Generated by `scripts/build.py` — do not edit by hand. "
             "由 `scripts/build.py` 生成，请勿手工编辑。")
    L.append("")
    if not papers:
        L += ["*No entries yet. 暂无条目*", ""]
    for p in sorted(papers, key=sort_key, reverse=True):
        L.append(entry(p, bound_label, lang))
        L.append("")
    return "\n".join(L)


def check_anchors(readme):
    """校验目录锚点都能对上标题。中文标题与含 '/' 的标题最容易出问题。"""
    # 只取目录区的锚点链接，避免把正文里的普通链接算进来
    links = re.findall(r"^\s*- \[[^\]]+\]\(#([^)]+)\)", readme, re.M)
    heads = [
        re.sub(r"\s+", "-", re.sub(r"[^\w\s\u4e00-\u9fff-]", "", h.strip().lower()))
        for h in re.findall(r"^#{2,4} (.+)$", readme, re.M)
    ]
    return [l for l in links if l not in heads]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="只校验，不写文件")
    args = ap.parse_args()

    papers, secs = load()

    errs = validate(papers, secs)
    if errs:
        print(f"校验失败，{len(errs)} 个问题：\n", file=sys.stderr)
        for e in errs:
            print(f"  ✗ {e}", file=sys.stderr)
        sys.exit(1)
    print(f"✓ 校验通过：{len(papers)} 篇")

    readme_en = build_readme(papers, secs, "en")
    readme_zh = build_readme(papers, secs, "zh")

    for name, rm in (("README.md", readme_en), ("README.zh.md", readme_zh)):
        bad = check_anchors(rm)
        if bad:
            print(f"{name} 目录锚点失效 {len(bad)} 个：{bad}", file=sys.stderr)
            sys.exit(1)
    print("✓ 两个 README 目录锚点全部有效")

    if args.check:
        return

    (ROOT / "README.md").write_text(readme_en, encoding="utf-8")
    (ROOT / "README.zh.md").write_text(readme_zh, encoding="utf-8")
    print("✓ README.md（英文主版）+ README.zh.md（中文副版）")

    # views/ 用英文（标题本身是英文，视图为导航性质）
    bound_label = {b["id"]: b.get("title_en", b["title"]) for b in secs["boundaries"]}
    titles = {i: t for i, t, *_ in flatten(secs["sections"], "en")}
    by_sec = defaultdict(list)
    for p in papers:
        by_sec[str(p["section"])].append(p)
    for sid, items in sorted(by_sec.items()):
        f = ROOT / "views" / "by-section" / f"{sid}.md"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(build_group(items, f"{sid} {titles.get(sid, '')}", bound_label),
                     encoding="utf-8")
    print(f"✓ views/by-section/（{len(by_sec)} 个）")

    for b in secs["boundaries"]:
        items = [p for p in papers if b["id"] in (p.get("boundary") or [])]
        f = ROOT / "views" / "by-boundary" / f"{b['id']}.md"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(
            build_group(items, f"Trust boundary · {b.get('title_en', b['title'])}",
                        bound_label,
                        f"*{b.get('desc_en', b.get('desc', ''))}*"),
            encoding="utf-8")
    print(f"✓ views/by-boundary/（{len(secs['boundaries'])} 个）")


if __name__ == "__main__":
    main()
