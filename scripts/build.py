#!/usr/bin/env python3
"""
从 data/papers.yaml + data/sections.yaml 生成：
  - README.md
  - papers_by_section/<id>.md
  - papers_by_surface/<boundary>.md
  - 攻击面 × 信任边界 交叉矩阵（嵌在 README 中）

用法：
    python3 scripts/build.py           # 生成
    python3 scripts/build.py --check   # 只校验，不写文件（CI 用）

设计约定：README 与分组文件都是产物，绝不手工编辑。
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


def flatten(sections):
    """展平章节树，返回 [(id, title, desc, stock, is_leaf, depth)]"""
    out = []
    for s in sections:
        kids = s.get("children") or []
        out.append((s["id"], s["title"], s.get("desc"), s.get("stock"), not kids, 0))
        for c in kids:
            out.append((c["id"], c["title"], c.get("desc"), c.get("stock"), True, 1))
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
        if s and len(s) < 60:
            errs.append(f"[{tag}] 简介过短（{len(s)} 字），惯例 150–300 字含动机/机制/关键数字")
    return errs


def entry(p, bound_label):
    """渲染单条目。"""
    head = p["title"]
    if p.get("abbr"):
        head += f" ({p['abbr']})"
    head += f" ({p['date']})"

    lines = [f"#### {head}", f"- **简介**：{' '.join((p['summary'] or '').split())}"]

    bounds = "、".join(bound_label.get(b, b) for b in (p.get("boundary") or []))
    meta = f"- **信任边界**：{bounds}"
    if p.get("venue") and p["venue"] != "arXiv":
        meta += f" ｜ **发表**：{p['venue']}"
    lines.append(meta)

    if p.get("id"):
        lines.append(f"- **arXiv**：[{p['id']}](https://arxiv.org/abs/{p['id']})")
    elif p.get("url"):
        lines.append(f"- **链接**：{p['url']}")
    if p.get("code"):
        lines.append(f"- **代码**：{p['code']}")
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


def build_matrix(papers, secs):
    """攻击面 × 信任边界 交叉矩阵 —— 这是本仓库与竞品扁平标签的核心区别。"""
    bounds = secs["boundaries"]
    tops = [s for s in secs["sections"] if s["id"] != "7"]

    # 每篇论文归到其所属顶层章节
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

    L = []
    L.append("| 攻击面 \\ 信任边界 | " + " | ".join(b["title"] for b in bounds) + " |")
    L.append("|---|" + "---|" * len(bounds))
    for s in tops:
        row = [f"**{s['id']} {s['title']}**"]
        for b in bounds:
            n = grid[s["id"]][b["id"]]
            row.append(str(n) if n else "·")
        L.append("| " + " | ".join(row) + " |")
    return "\n".join(L)


def build_readme(papers, secs):
    bound_label = {b["id"]: b["title"] for b in secs["boundaries"]}
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
    L.append("> AI Infra 安全论文清单 —— LLM 推理与训练基础设施的攻击面、信任边界与防御，每篇附中文简介")
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
    L.append("## 为什么需要这个清单")
    L.append("")
    L.append(
        "AI Infra 最大的特殊性是：**用户输入的语义，会直接决定底层计算拓扑、缓存状态、"
        "GPU 内存占用、调度行为和网络通信。**"
    )
    L.append("")
    L.append(
        "普通 Web / Cloud 里，request content 与底层 resource state 通常相对解耦。"
        "但在 LLM Infra 里，一段 prompt 会同时影响 KV 分配、prefix 命中、batch 组成、"
        "抢占行为、MoE 专家路由与 GPU 间通信 —— 也就是说，**输入不仅控制模型输出，"
        "还间接控制基础设施状态**。于是攻击者可以通过完全合法的 API 请求去操纵系统。"
    )
    L.append("")
    L.append("由此产生了一批传统系统安全分类学难以归置的问题：")
    L.append("")
    L.append("- 性能优化直接变成隐私侧信道（KV prefix 共享 → 跨租户 prompt 推断）")
    L.append("- 模型语义决定物理执行路径（MoE routing → GPU/NIC 负载 → 可观测侧信道）")
    L.append("- 攻击目标从算力转向状态机（少量请求操纵调度器，而非压垮 GPU）")
    L.append("- 部署优化悄悄改变模型安全性（量化后 perplexity 不变但拒答行为崩塌）")
    L.append("- 本地损坏放大为全局污染（单个 rank 的错误张量经 collective 写入 checkpoint）")
    L.append("")
    L.append("## 这个仓库收录什么")
    L.append("")
    L.append(
        "只收录**以 LLM 推理 / 训练基础设施本身为主要研究对象**的安全工作，"
        "按「攻击面 × 信任边界」二维组织。"
    )
    L.append("")
    L.append("**不收录**（三条最容易失守的边界）：")
    L.append("")
    L.append(
        "1. **用 AI 做安全工作**（AI-for-Security）—— 如「用 MoE 做恶意软件分类」、"
        "渗透测试、漏洞挖掘。本仓库只收 Security-of-AI"
    )
    L.append(
        "2. **纯模型层工作** —— 必须涉及 serving / training 系统的状态、资源或拓扑。"
        "只在模型权重与输出层面讨论对齐的研究不收"
    )
    L.append(
        "3. **换个部署环境重跑的通用越狱** —— 攻击或防御的作用点必须在基础设施上"
    )
    L.append("")
    L.append("## 为什么按「攻击面 × 信任边界」而不按主题标签组织")
    L.append("")
    L.append(
        "现有的 LLM 安全大盘清单大多按投稿主题贴扁平标签（jailbreak / privacy / "
        "watermark …），结果是 infra 层的工作被打散：KV cache 侧信道与网络流量指纹"
        "因为同属 side-channel 而被放进同一节，而它们的攻击者能力、防御位置和"
        "受影响的系统组件完全不同。"
    )
    L.append("")
    L.append(
        "本仓库以**攻击面**（系统栈上的位置：KV / scheduler / routing / interconnect / "
        "训练 collective）为一级维度，以**信任边界**（跨租户 / 跨请求 / 主机-设备 / "
        "节点间 / 供应链 / 模型内部）为交叉标签。"
    )
    L.append("")
    L.append(
        "这样做的理由是：同一个攻击面在不同信任边界下的严重性完全不同。"
        "KV 泄露在单租户自部署里几乎无害，在多租户 serving 里是重大隐私事故。"
        "只有同时标注这两个维度，读者才能判断一篇工作是否与自己的部署形态相关。"
    )
    L.append("")
    L.append("### 攻击面 × 信任边界 分布")
    L.append("")
    L.append(build_matrix(papers, secs))
    L.append("")
    L.append("## 目录")
    L.append("")
    for sid, title, _desc, _stock, is_leaf, depth in flatten(secs["sections"]):
        L.append(f"{'  ' * depth}- [{sid} {title}](#{anchor_of(sid, title)})")
    L.append("")
    L.append("按信任边界浏览：" + " ｜ ".join(
        f"[{b['title']}](papers_by_surface/{b['id']}.md)" for b in secs["boundaries"]))
    L.append("")
    L.append("---")
    L.append("")

    for sid, title, desc, stock, is_leaf, depth in flatten(secs["sections"]):
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
                L.append(entry(p, bound_label))
                L.append("")
        else:
            note = "*本节暂无收录条目*"
            if stock:
                note += f"（arXiv 存量约 {stock} 篇待整理，欢迎 PR）"
            L.append(note)
            L.append("")

    L.append("---")
    L.append("")
    L.append("## 贡献")
    L.append("")
    L.append(
        "只需修改 `data/papers.yaml`，`README.md` 与 `papers_by_*/` 下所有文件"
        "由 GitHub Actions 自动生成。收录标准与条目格式见 [CONTRIBUTING.md](CONTRIBUTING.md)，"
        "维护流程与检索口径见 [MAINTENANCE.md](MAINTENANCE.md)。"
    )
    L.append("")
    L.append("## 相关仓库")
    L.append("")
    L.append("本仓库聚焦 LLM 基础设施自身的安全，以下方向请见：")
    L.append("")
    L.append("- GUI / Computer-Use Agent 安全：`Yuxuan2003/Awesome-GUI-Agent-Security`")
    L.append("- LLM 安全与隐私大盘（模型层为主）：`ThuCCSLab/Awesome-LM-SSP`")
    L.append("- LLM 推理系统能力向研究：`AmadeusChan/Awesome-LLM-System-Papers`")
    L.append("- 模型压缩与量化（纯效率视角）：`HuangOwen/Awesome-LLM-Compression`")
    L.append("")
    return "\n".join(L) + "\n"


def build_group(papers, heading, bound_label, note=None):
    L = [f"# {heading}", ""]
    if note:
        L += [note, ""]
    L.append("> 本文件由 `scripts/build.py` 生成，请勿手工编辑。")
    L.append("")
    if not papers:
        L += ["*暂无条目*", ""]
    for p in sorted(papers, key=sort_key, reverse=True):
        L.append(entry(p, bound_label))
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

    readme = build_readme(papers, secs)

    bad = check_anchors(readme)
    if bad:
        print(f"目录锚点失效 {len(bad)} 个：{bad}", file=sys.stderr)
        sys.exit(1)
    print("✓ 目录锚点全部有效")

    if args.check:
        return

    (ROOT / "README.md").write_text(readme, encoding="utf-8")
    print("✓ README.md")

    bound_label = {b["id"]: b["title"] for b in secs["boundaries"]}
    titles = {i: t for i, t, *_ in flatten(secs["sections"])}
    by_sec = defaultdict(list)
    for p in papers:
        by_sec[str(p["section"])].append(p)
    for sid, items in sorted(by_sec.items()):
        f = ROOT / "papers_by_section" / f"{sid}.md"
        f.write_text(build_group(items, f"{sid} {titles.get(sid, '')}", bound_label),
                     encoding="utf-8")
    print(f"✓ papers_by_section/（{len(by_sec)} 个）")

    for b in secs["boundaries"]:
        items = [p for p in papers if b["id"] in (p.get("boundary") or [])]
        f = ROOT / "papers_by_surface" / f"{b['id']}.md"
        f.write_text(
            build_group(items, f"信任边界：{b['title']}", bound_label,
                        f"*{b.get('desc', '')}　信任边界是交叉标签，"
                        f"同一篇论文可能出现在多个分组中。*"),
            encoding="utf-8")
    print(f"✓ papers_by_surface/（{len(secs['boundaries'])} 个）")


if __name__ == "__main__":
    main()
