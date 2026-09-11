# 维护手册

本文记录周更流程、检索口径设计，以及建仓与调研阶段实测踩过的坑。给未来的自己看。

## 目录约定（2026-09-04 重构）

根目录只保留两个 md：**`README.md`（英文主版）+ `README.zh.md`（中文副版）**，让读者一眼看到入口。其余：

```
data/papers.yaml     ← 唯一数据源（条目含 summary 英文 + summary_zh 中文双简介）
data/sections.yaml   ← 章节定义（每节含 title/desc 中文 + title_en/desc_en 英文）
docs/                ← CONTRIBUTING.md、MAINTENANCE.md（本文）
views/by-section/    ← 按攻击面分组的视图（英文，自动生成）
views/by-boundary/   ← 按信任边界分组的视图（英文，自动生成）
scripts/             ← build.py / check_links.py / fetch.py
```

**默认语言是英文**（README.md），中文为副版本（README.zh.md），两者由 build.py 从同一份 papers.yaml 生成。改动只需动数据源。

## 仓库定位（一句话）

竞品缺的不是论文数量，而是**按系统栈建模的那一层**。唯一活跃的大盘 `ThuCCSLab/Awesome-LM-SSP`（2.1k★、3 commits/月）有 2467 篇条目，但 infra 相关只有约 19 篇（0.8%），且 MoEcho 与 PromptPeek 被塞进 `C7.Privacy/Side-Channel` 与网络流量指纹混在一起，`B6` 和 `C7` 两个同名 Side-Channel 节并存。它是按投稿主题贴扁平标签，没有攻击面维度，也没有信任边界维度。

**这就是本仓库的位置。别偏离它去做泛安全大盘 —— 那条路要正面对上 2.1k★ 的活跃仓库。**

## 建仓时的竞品基线（2026-09-04 实测）

| 仓库 | ★ | commits/月 | 定位 |
|---|---|---|---|
| ThuCCSLab/Awesome-LM-SSP | 2.1k | 3 | 大盘泛安全，infra 占 0.8% |
| ydyjya/Awesome-LLM-Safety | 1.9k | 0 | 躺平 |
| corca-ai/awesome-llm-security | 1.7k | 0 | 躺平 |
| chawins/llm-sp | 582 | 0 | 躺平 |
| HuangOwen/Awesome-LLM-Compression | 1.9k | 367 | 能力向，纯效率无安全轴 |
| AmadeusChan/Awesome-LLM-System-Papers | 646 | 0 | 能力向 MLSys |

专库名字空间当时是全空的：`Awesome-LLM-Serving-Security`、`Awesome-AI-Infra-Security`、`Awesome-KV-Cache-Security`、`Awesome-MoE-Security` 等 25+ 组合全部 `repo not found`。

**复核活跃度用 shields.io，不要用 GitHub API**（未认证约 20 次请求就限流）：

```bash
curl -s "https://img.shields.io/github/stars/<owner>/<repo>.json"
curl -s "https://img.shields.io/github/commit-activity/m/<owner>/<repo>.json"   # 关键
curl -s "https://img.shields.io/github/last-commit/<owner>/<repo>.json"
```

`commit-activity/m` 是识别僵尸仓库的唯一可靠指标。`last-commit` 显示本月很容易误判 —— 实测某仓库 last-commit 是本月但只有 2 commits/月，且当年作者本人只动过一次。

## 检索口径（本方向最关键的工程问题）

**报存量必须连口径一起报。** 同一方向（2025-01 ~ 2026-09）不同口径差 8 倍：

| 口径 | 存量 |
|---|---|
| 宽形态 × 宽安全 | 2091 |
| 宽形态 × 严安全 | 965 |
| 严形态 × 宽安全 | 1002 |
| 严形态 × 严安全 | 519 |
| **+ 限 cs.CR/DC/OS/AR/NI** | **260** ← 本仓库标准口径 |
| 仅 cs.CR | 88 |

`scripts/fetch.py` 默认用 260 那一档。`sections.yaml` 里各节的 `stock` 字段也都是这个口径下的数字。

### 四个已实测的坑

**坑 1：`adversarial` / `safety` / `privacy` 在本方向是灌水词。** 各带入 140 / 190 / 225 篇 —— 它们是**模型层**安全论文的标配词。系统安全改用 `side channel` / `denial-of-service` / `multi-tenant` / `isolation` / `confidentiality` / `information flow`。

**坑 2：`disaggregated` 被跨域同名重度污染。** O-RAN（"disaggregated 6G radio access networks"）与统计学（"spatial / temporal disaggregation"）都在用这个词，抽样 60 篇里 5 篇是这类噪音。已从形态词移除，改用 `prefill-decode` / `expert parallel`。同类高危词：`router`（网络路由器）、`scheduling`（通用运筹）、`GPU`（任何用 GPU 的论文）。

**坑 3：限定主分类是提精度最有效的手段**（519 → 260）。但要按章节选：
- 侧信道 / DoS / 隔离 → `cs.CR` `cs.DC` `cs.OS` `cs.AR` `cs.NI`
- 第 3 章与 2.3 节（优化→safety 漂移、MoE routing × safety）主要投 `cs.CL` `cs.LG`，限 cs.CR 会漏掉大半

`fetch.py` 里的 `MODEL_LAYER_SECTIONS` 就是为这条服务的。

**坑 4：只看 totalResults 会严重误判，必须抽样判精度。** 宽口径 60 篇里真命中仅约 6 篇（精度 10%）。改检索词后务必抓 50 篇标题+摘要人工扫一遍，**精度低于 30% 不要拿去建库**。

### 反向验证

改动检索词后跑一次反向验证：取 10 篇已知确属本方向的论文，检查能否被新 query 命中。

建仓时实测命中 9/10 = 90%（漏的那篇是 `2608.20732`，摘要用 "LLM API reseller" 而非标准形态词）。**≥80% 才能认定实测存量是真实体量而非 query 缺陷。**

## 周更流程

增量实测 **10–12 篇/周**（2026-07: 43/月、2026-08: 51/月），可以做真周更 —— 这点比 GUI Agent 安全（4.3 篇/周，只能双周更）宽裕得多。

```bash
# 1. 确认上次实际覆盖到哪天（不是请求到哪天）
grep -o 'id: "[0-9.]*"' data/papers.yaml | sort | tail -3

# 2. 检索新窗口（与上次首尾相接）
python3 scripts/fetch.py --start 2026-09-05 --end 2026-09-11

# 3. 人工筛 —— 不可省，见 CONTRIBUTING 三条收录边界

# 4. 写入 data/papers.yaml，然后
python3 scripts/build.py
python3 scripts/check_links.py

# 5. 提 PR，分支名 update/YYYY-MM-wN
```

**当天投稿几乎必然未索引**（GUI 库那轮连续三次遇到）。窗口终点写到今天没关系，但要在 commit / PR 里标明实际覆盖区间，把缺的那天留给下一轮起点。

## 章节维护要点

**第 7 章「工程侧安全」必须单独走非 arXiv 流程。** serving 框架的真实漏洞走 CVE 与 GitHub advisory 渠道，arXiv 上搜不到。周更时不要因为 arXiv 无结果就跳过这一章。来源包括：

- vLLM / SGLang 的 GitHub Security Advisory
- CVE 数据库（已收录 CVE-2025-25183、CVE-2025-46722 相关工作）
- 厂商安全公告
- Simon Willison 那类 prompt injection 追踪

这条是 GUI 库那轮的教训迁移过来的：凡高度依赖非 arXiv 来源的章节必须显式规划检索流程，否则会整段缺失。

**第 0 章存量 48 篇但目前空着。** 优先补这一章 —— 综述与威胁模型是读者的入口，也是建立仓库权威性的地方。特别是「攻击面 × 信任边界」对照表，做出来就是本仓库独有的东西。

**存量补齐建议顺序**（按存量与差异化程度）：
1. `1.1` KV/Prefix Cache（225 篇存量，本方向最成熟的线）
2. `2.1` Scheduler DoS（144 篇，且大盘零覆盖）
3. `3` 优化→Safety 漂移（139 篇，交叉地带无人做）
4. `1.3` 解耦推理（195 篇，但要剔 O-RAN 噪音）
5. `5` 硬件与执行环境（138 篇）
6. `6` 防御与系统机制（94 篇）

每批 15–25 篇一个 PR。

## 存量建库实测（2026-09-04 首发扩库）

用 `fetch.py --start 2025-01-01 --end 2026-09-04 --out` 全量召回，5 个并行子任务分节筛选+撰写双语条目：

| 指标 | 数值 |
|---|---|
| 粗召回（去重后候选） | 293 篇 |
| 实际收录 | 38 篇新条目 |
| **真实命中率** | **约 13%** |

**剔除主因分布（这是噪音的真实来源，周更筛选时直接对照）：**
- 纯效率向工作占绝大多数 —— KV 压缩/调度/内存管理（HiKV、MosaicKV、Oneiros）、加速器/硬件架构、prefill/decode 分离性能优化。**命中了检索词但不是安全工作。** 约占总剔除量的 70%。
- AI-for-Security —— PHP 漏洞检测、威胁狩猎、用 MoE 做恶意软件分类。
- 模型层对抗/越狱 —— 作用点不在基础设施。
- activation 仅作效率用途（压缩/稀疏化）而非泄露渠道。

**周更预期：粗召回约 10–12 篇/周，经筛选后实际收录约 1–2 篇/周。** 这个比例意味着周更时会频繁空窗，可考虑双周更，或把标准口径适当放宽后靠人工筛选兜底。

**两个实测踩坑：**
1. subagent 会把「真安全论文但归错节」的条目塞进 hint 节 —— 实测 Quantamination（量化侧信道）被塞进 2.1 应归 3，FlexServe/Confidential-TEE（隔离防御）被塞进 2.1 应归 6。**合并前必须逐条核实可疑条目的摘要**，不能只看 section 字段。
2. 不同子任务会对同一篇论文做出不同判断导致**跨文件重复** —— 实测 s3 与 s4 都收了 FlexServe。**合并脚本必须按 id + 标题双去重。**
3. **同名不同工作**会被同时收录且都通过校验 —— 实测两个都叫 CachePrune 的工作（`2605.23640` 隐私感知 KV 共享 vs `2504.21228` KV 编辑防注入）撞了缩写。判据是两个 arXiv ID 各自通过标题精确匹配、但 abbr 相同。处理：保留更贴切的那条的 abbr，另一条的 abbr 删掉以免读者混淆。

## 当前覆盖缺口（2026-09-04 首发 62 篇后）

- **第 1.3 节「解耦推理与 KV 跨节点搬运」只有 1 篇**，但这是本方向的核心创新点（RDMA KV 搬运的机密性/完整性/租户绑定/误路由）。粗召回 23 篇全是性能向工作被剔除 —— 说明这块**学术研究几乎空白**，是最值得盯的开放问题，也是最容易做出差异化的章节。周更时优先检查这一节。
- 第 0 章综述仅 1 篇，仍需补强。

## 周期更新记录

| 窗口 | 标准口径召回 | 放宽口径 | 去重候选 | 收录 | 累计 |
|---|---|---|---|---|---|
| 2025-01 ~ 2026-09-04（存量建库） | 479 | — | 293 | 38（+24 种子） | 62 |
| 2026-09-05 ~ 09-11 | 6 | 11 | 4 | **3** | 65 |

### 2026-09-05 ~ 09-11（第一个周更周期）

收录 3 篇：
- `2609.06853` → §1.1　KV timing 侧信道在多租户竞争下的可靠性刻画（Cohen's d 0.7789→0.2109）
- `2609.06674` → §1.2　detokenizer CPU cache 侧信道重建本地 LLM 输出
- `2609.11799` → §6　　SpecGuard，复用投机解码做零开销后门检测

剔除 1 篇：`2609.09338`（Osprey）—— 纯性能向投机解码加速，不谈安全。

**本周期是低产周，且已确认不是 query 缺陷：**
1. 09-11 当天召回 0 篇 —— 当天投稿未被 arXiv 索引，符合预期，留给下一轮起点
2. **放宽口径（`--loose`，不限主分类）也只有 11 篇** —— 这是关键诊断。若标准口径低而放宽口径正常，说明分类限定过严；两者都低则是该周期客观产出少
3. 实际收录 3 篇，与 MAINTENANCE 先前估计的「1–2 篇/周」基本吻合

**归类判断留档**：SpecGuard 的 section_hint 是 3（优化→Safety 漂移），但它不是「优化导致 safety 退化」，而是**把 infra 既有组件（投机解码）转为防御设施**，因此归 §6。这类「复用 infra 机制做防御」的工作以后都归 §6，不要因为标题里有 speculative decoding 就放进 §3。

**下一轮窗口起点：2026-09-11**（本轮未覆盖当天投稿）。

## CI 说明

两层校验：

| 脚本 | 检查内容 | 触发 |
|---|---|---|
| `build.py --check` | 结构、必填字段、ID 格式、重复、章节归属、锚点 | 每个 PR（快，不联网） |
| `check_links.py` | arXiv 可达性、**标题精确匹配**、v1 日期一致性 | PR 抽样 12 条；每周一全量 |

**标题精确匹配这条不能省。** 只查 HTTP 200 拦不住「ID 指向另一篇真实论文」的错误。建仓时这条 CI 当场抓出一个真实错误：`2608.27512` 的标题被我截短了，漏掉副标题 "and the Validation--Deployment Gap"，相似度 0.830 被拦下。GUI 库那轮也抓出过两个（标题写错 + v1 日期写成 v2 月份）。

`check.yml` 的 `push` 触发**故意不加 paths 过滤** —— 首次推送时 `data/**` 属新增文件，paths 过滤不会匹配，导致 CI 在建仓时跑不起来（GUI 库实测踩过）。

### 建仓时必做的一次性设置

**新仓库的 Actions 默认是只读权限，`build.yml` 回推产物会失败。** 建仓当天实测：构建步骤全部成功，但最后一步「提交产物」失败，原因是 `GITHUB_TOKEN` 只有 read 权限，尽管 workflow 里已经写了 `permissions: contents: write`（仓库级设置优先级更高）。

修法二选一：

```bash
# 方式 A：API（推荐，可脚本化）
curl -X PUT -H "Authorization: Bearer $TOK" \
  https://api.github.com/repos/<owner>/<repo>/actions/permissions/workflow \
  -d '{"default_workflow_permissions":"write","can_approve_pull_request_reviews":false}'
```

方式 B：网页 Settings → Actions → General → Workflow permissions → 选 "Read and write permissions"。

**这个设置只需做一次，但不做的话每次 data 变更后 README 都不会自动重建**，会退化成手工维护多文件、进而出现「目录与正文不同步」—— 正是本仓库架构要避免的问题。

### 从姊妹仓库照搬 workflow 时要全文搜一遍路径名

建仓时 `build.yml` 是从 GUI 库复制的，里面的 `git add` 还写着那边的目录名 `papers_by_env`，而本仓库叫 `papers_by_surface`，导致 Build 报 `fatal: pathspec 'papers_by_env' did not match any files`（exit 128）。

**这个错误的迷惑性在于：构建步骤全部成功、README 也正确生成了，只有最后一步回推失败**，很容易误判成权限问题去改 Actions 权限（我就先改了一轮权限才发现真因）。

照搬 workflow / 脚本后，用一句话自查：

```bash
grep -rn 'papers_by_env\|Awesome-GUI-Agent-Security' .github scripts
```

同理，`scripts/build.py` 里的 `REPO` 常量、README 徽章链接也都要改。

## 相关

- 姊妹仓库：`Yuxuan2003/Awesome-GUI-Agent-Security`（GUI/CUA agent 安全，按攻防轴组织）
- 两者定位区分：本仓库管**基础设施层**（KV / scheduler / routing / collective），那个管**agent 交互层**（提示注入 / 环境注入 / 越权）。互为上下游，可互相引流。
