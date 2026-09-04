# Awesome-AI-Infra-Security

> AI Infra 安全论文清单 —— LLM 推理与训练基础设施的攻击面、信任边界与防御，每篇附中文简介

![Last Update](https://img.shields.io/badge/last%20update-2026.09-brightgreen) ![Papers](https://img.shields.io/badge/papers-20%2B-blue) ![Time Range](https://img.shields.io/badge/time-2025.01--2026.09-orange) [![Link Check](https://github.com/Yuxuan2003/Awesome-AI-Infra-Security/actions/workflows/check.yml/badge.svg)](https://github.com/Yuxuan2003/Awesome-AI-Infra-Security/actions/workflows/check.yml) ![Awesome](https://img.shields.io/badge/-awesome-ff69b4)

## 为什么需要这个清单

AI Infra 最大的特殊性是：**用户输入的语义，会直接决定底层计算拓扑、缓存状态、GPU 内存占用、调度行为和网络通信。**

普通 Web / Cloud 里，request content 与底层 resource state 通常相对解耦。但在 LLM Infra 里，一段 prompt 会同时影响 KV 分配、prefix 命中、batch 组成、抢占行为、MoE 专家路由与 GPU 间通信 —— 也就是说，**输入不仅控制模型输出，还间接控制基础设施状态**。于是攻击者可以通过完全合法的 API 请求去操纵系统。

由此产生了一批传统系统安全分类学难以归置的问题：

- 性能优化直接变成隐私侧信道（KV prefix 共享 → 跨租户 prompt 推断）
- 模型语义决定物理执行路径（MoE routing → GPU/NIC 负载 → 可观测侧信道）
- 攻击目标从算力转向状态机（少量请求操纵调度器，而非压垮 GPU）
- 部署优化悄悄改变模型安全性（量化后 perplexity 不变但拒答行为崩塌）
- 本地损坏放大为全局污染（单个 rank 的错误张量经 collective 写入 checkpoint）

## 这个仓库收录什么

只收录**以 LLM 推理 / 训练基础设施本身为主要研究对象**的安全工作，按「攻击面 × 信任边界」二维组织。

**不收录**（三条最容易失守的边界）：

1. **用 AI 做安全工作**（AI-for-Security）—— 如「用 MoE 做恶意软件分类」、渗透测试、漏洞挖掘。本仓库只收 Security-of-AI
2. **纯模型层工作** —— 必须涉及 serving / training 系统的状态、资源或拓扑。只在模型权重与输出层面讨论对齐的研究不收
3. **换个部署环境重跑的通用越狱** —— 攻击或防御的作用点必须在基础设施上

## 为什么按「攻击面 × 信任边界」而不按主题标签组织

现有的 LLM 安全大盘清单大多按投稿主题贴扁平标签（jailbreak / privacy / watermark …），结果是 infra 层的工作被打散：KV cache 侧信道与网络流量指纹因为同属 side-channel 而被放进同一节，而它们的攻击者能力、防御位置和受影响的系统组件完全不同。

本仓库以**攻击面**（系统栈上的位置：KV / scheduler / routing / interconnect / 训练 collective）为一级维度，以**信任边界**（跨租户 / 跨请求 / 主机-设备 / 节点间 / 供应链 / 模型内部）为交叉标签。

这样做的理由是：同一个攻击面在不同信任边界下的严重性完全不同。KV 泄露在单租户自部署里几乎无害，在多租户 serving 里是重大隐私事故。只有同时标注这两个维度，读者才能判断一篇工作是否与自己的部署形态相关。

### 攻击面 × 信任边界 分布

| 攻击面 \ 信任边界 | 跨租户 | 跨请求 | 主机-设备 | 节点间 | 供应链 | 模型内部 |
|---|---|---|---|---|---|---|
| **0 威胁模型与综述** | · | · | · | · | · | · |
| **1 AI State Plane 安全** | 6 | 3 | 1 | 1 | 1 | · |
| **2 Semantic-to-Resource 攻击面** | 3 | · | 1 | 1 | · | 3 |
| **3 Infra 优化引发的 Safety 漂移** | · | · | · | · | 1 | 4 |
| **4 训练侧完整性** | · | · | · | 2 | 1 | · |
| **5 硬件与执行环境** | · | · | 2 | · | 1 | · |
| **6 防御与系统机制** | 1 | · | 1 | · | · | 1 |

## 目录

- [0 威胁模型与综述](#0-威胁模型与综述)
- [1 AI State Plane 安全](#1-ai-state-plane-安全)
  - [1.1 KV / Prefix Cache 侧信道与泄露](#11-kv-prefix-cache-侧信道与泄露)
  - [1.2 Activation / Embedding 状态泄露](#12-activation-embedding-状态泄露)
  - [1.3 解耦推理与 KV 跨节点搬运](#13-解耦推理与-kv-跨节点搬运)
  - [1.4 缓存一致性与语义缓存](#14-缓存一致性与语义缓存)
- [2 Semantic-to-Resource 攻击面](#2-semantic-to-resource-攻击面)
  - [2.1 Scheduler 状态操纵与延迟 DoS](#21-scheduler-状态操纵与延迟-dos)
  - [2.2 MoE 路由侧信道](#22-moe-路由侧信道)
  - [2.3 MoE 路由操纵与 Safety 削弱](#23-moe-路由操纵与-safety-削弱)
  - [2.4 专家并行通信与负载劫持](#24-专家并行通信与负载劫持)
- [3 Infra 优化引发的 Safety 漂移](#3-infra-优化引发的-safety-漂移)
- [4 训练侧完整性](#4-训练侧完整性)
- [5 硬件与执行环境](#5-硬件与执行环境)
- [6 防御与系统机制](#6-防御与系统机制)
- [7 工程侧安全（非 arXiv 来源）](#7-工程侧安全非-arxiv-来源)

按信任边界浏览：[跨租户](papers_by_surface/cross-tenant.md) ｜ [跨请求](papers_by_surface/cross-request.md) ｜ [主机-设备](papers_by_surface/host-device.md) ｜ [节点间](papers_by_surface/inter-node.md) ｜ [供应链](papers_by_surface/supply-chain.md) ｜ [模型内部](papers_by_surface/model-internal.md)

---

## 0 威胁模型与综述

*领域综述、SoK，以及「攻击面 × 信任边界」对照表。 本章负责回答「AI Infra 的安全边界和传统 Web/Cloud 有何本质不同」。*

*本节暂无收录条目*（arXiv 存量约 48 篇待整理，欢迎 PR）

## 1 AI State Plane 安全

*传统系统只有 Control Plane 与 Data Plane，LLM serving 多出了一层 「AI State Plane」—— KV、activation、embedding、expert routing、adapter、 speculative state 在机器之间流动。这些中间状态携带用户输入的信息， 却在多数 infra 设计中首先被当作 performance object 而非 tenant security boundary。*

### 1.1 KV / Prefix Cache 侧信道与泄露

*prefix 复用带来的 timing channel、跨租户 prompt 推断、cache 命中探测*

#### Uncovering and Understanding Hidden Dependencies in the LLM API Reseller Ecosystem via Prefix-Cache Side Channels (Reseller Probing) (2026-08)
- **简介**：LLM API 转售商已成为访问模型服务的重要一层，但多级转售让供应链变得不透明： 用户的请求可能经过若干未披露的上游。本文把 prefix-cache 侧信道用作探针， 通过构造探测 prompt 并观测缓存命中特征，反推出转售商背后的真实上游依赖关系。 这是一个把 infra 侧信道用于生态测绘的有趣转向 —— 侧信道不止能偷 prompt， 还能揭示服务提供方刻意隐藏的拓扑结构，对合规与数据流向审计都有直接意义。
- **信任边界**：跨租户、供应链
- **arXiv**：[2608.20732](https://arxiv.org/abs/2608.20732)

#### Governing the KV Cache: Preventing Timing Side-Channel Leakage in Multi-Tenant LLM Inference (KV Governance) (2026-08)
- **简介**：KV cache 是现代 LLM 推理最主要的吞吐优化手段，它让 prefix 可以跨请求复用； 但在多租户部署下这份缓存是共享的，命中与否会体现在首 token 时延上， 于是纯粹的性能优化直接变成了隐私侧信道。本文系统刻画了 vLLM 与 SGLang 中 prefix 复用带来的 timing channel，并给出缓存治理层面的防御设计， 在保留大部分复用收益的同时切断攻击者据时延差异探测他人缓存内容的能力。
- **信任边界**：跨租户、跨请求
- **arXiv**：[2608.09225](https://arxiv.org/abs/2608.09225)

#### I Know What You Asked: Prompt Leakage via KV-Cache Sharing in Multi-Tenant LLM Serving (PromptPeek) (2025-02)
- **简介**：南方科技大学与字节跳动的工作，是 KV prefix 共享攻击这条线的奠基论文之一。 作者提出 PromptPeek 攻击：在多租户 serving 中，攻击者通过构造候选 prefix 并测量首 token 时延判断缓存是否命中，据此逐步推断出其他用户 prompt 的内容。 该工作直接推动了工程侧的防御响应 —— vLLM 随后引入 cache_salt 机制， 把租户标识注入首个 cache block 的 hash 以隔离这条 timing channel。
- **信任边界**：跨租户 ｜ **发表**：NDSS 2025
- **链接**：https://www.ndss-symposium.org/ndss-paper/i-know-what-you-asked-prompt-leakage-via-kv-cache-sharing-in-multi-tenant-llm-serving/

### 1.2 Activation / Embedding 状态泄露

*中间激活、稀疏模式、hidden state 反演出原始输入*

#### SparSEEty: Extracting Tokens from Sparsity-Exploiting LLM Serving Systems via Deterministic Side Channels (SparSEEty) (2026-08)
- **简介**：现代 LLM 存在激活稀疏性，只有部分神经元会被给定 token 激活，serving 系统 普遍利用这一性质做优化。本文指出这种优化把模型的内部激活模式暴露成了 可观测的确定性侧信道：由于稀疏模式与输入 token 强相关且执行路径确定， 攻击者可据此反推出被处理的 token。这是「性能优化把模型内部状态外化」 这一类问题的典型案例，与 KV cache 侧信道同源但作用在激活层面。
- **信任边界**：跨租户、主机-设备
- **arXiv**：[2608.02995](https://arxiv.org/abs/2608.02995)

### 1.3 解耦推理与 KV 跨节点搬运

*prefill/decode 分离、RDMA 传输 KV、KV 的租户绑定与请求绑定、 stale KV、重放、误路由、跨租户 KV 注入*

#### Denial of Deadline: Network-Driven Accuracy Collapse in Distributed Inference Pipelines (Denial of Deadline) (2026-07)
- **简介**：分布式推理流水线依赖节点间网络按时交付中间结果，本文指出攻击者无需击穿 任何计算节点，只要在网络层制造有针对性的延迟，就能让流水线错过截止时间， 迫使系统退化到降级路径并造成精度崩塌。这类攻击的特殊之处在于攻击目标 既不是可用性也不是机密性，而是**推理结果的正确性**， 且从单节点视角看每个组件都在正常工作。
- **信任边界**：节点间
- **arXiv**：[2607.24692](https://arxiv.org/abs/2607.24692)

### 1.4 缓存一致性与语义缓存

*prefix-cache hash 碰撞、image cache 碰撞、semantic cache 语义不一致*

#### HijackKV: New Threat in Position-Independent KV Cache Reuse (HijackKV) (2026-07)
- **简介**：为提升复用率，新一代缓存方案允许位置无关的 KV 重用 —— 同一段文本的 KV 不再绑定在原有位置上即可被复用。本文指出这种放松引入了新的攻击面： 攻击者可以让被复用的 KV 片段在新上下文中承载与原意不同的语义， 从而在模型输入表面完全正常的情况下篡改其内部上下文。这类攻击的隐蔽性在于 prompt 本身是良性的，被改变的是模型实际看到的内部状态。
- **信任边界**：跨请求、跨租户
- **arXiv**：[2607.19957](https://arxiv.org/abs/2607.19957)

#### Cache Me, Catch You: Cache Related Security Threats in LLM Serving Frameworks (Cache Me Catch You) (2026-02)
- **简介**：系统性审计了 LLM serving 框架中各类缓存的安全问题，指出现代 serving 的缓存 已不止 KV 一种，而是 prefix cache、semantic cache、image cache 并存。 作者发现了 prefix-cache hash 碰撞、image-cache 碰撞以及 semantic cache 的语义不一致三类问题，并落地为真实漏洞（含 CVE-2025-25183、CVE-2025-46722 等）。 这篇是本仓库第 7 章「工程侧安全」与学术研究结合得最好的范例。
- **信任边界**：跨租户、跨请求 ｜ **发表**：NDSS 2026
- **链接**：https://github.com/XingTuLab/Cache_Me_Catch_You
- **代码**：https://github.com/XingTuLab/Cache_Me_Catch_You

## 2 Semantic-to-Resource 攻击面

*这是 AI Infra 最根本的独特性：**用户输入的语义会直接决定底层计算拓扑、 缓存状态、GPU 内存占用、调度行为与网络通信**。普通 Web/Cloud 里 request content 与底层 resource state 相对解耦；LLM Infra 里一段 prompt 可以同时改变 KV 分配、 prefix 命中、batch 组成、抢占行为、MoE 专家路由与 GPU 间通信。 于是攻击者可以通过完全合法的 API 输入去操纵系统状态。*

### 2.1 Scheduler 状态操纵与延迟 DoS

*不打 GPU FLOPS，而是打 LLM serving 的状态机 —— 用少量精心构造的请求 操纵输出长度、KV 占用、batch 生命周期，诱发反复抢占与重算*

#### Rethinking Latency Denial-of-Service: Attacking the LLM Serving Framework, Not the Model (Fill and Squeeze) (2026-02)
- **简介**：传统 DoS 靠海量请求压垮算力，本文指出 LLM serving 存在更廉价的路径： 攻击的不是 GPU FLOPS，而是 serving 框架的状态机。作者提出 Fill and Squeeze 两阶段攻击 —— Fill 阶段用精心构造的请求占满全局 KV cache， Squeeze 阶段迫使调度器对其他租户的请求反复抢占与重算。 评估中受害者的首 token 时延劣化可达数十至数百倍量级， 而攻击者只需少量完全合法的 API 请求。
- **信任边界**：跨租户
- **arXiv**：[2602.07878](https://arxiv.org/abs/2602.07878)

### 2.2 MoE 路由侧信道

*经 cache / TLB / performance counter / 时延 / 网络流量反推专家激活，进而还原输入语义*

#### MoEcho: Exploiting Side-Channel Attacks to Compromise User Privacy in Mixture-of-Experts LLMs (MoEcho) (2025-08)
- **简介**：东北大学团队的工作，是 MoE 架构侧信道这条线的代表作。核心观察是 MoE 让 模型语义决定物理执行路径：不同领域的 prompt 会激活不同的专家组合。 作者利用 CPU/GPU 上的 cache、TLB、performance counter 等侧信道推断专家 激活模式，并进一步还原 prompt 与 response 信息。这是标准的 「模型架构 × 系统安全」交叉点 —— 攻击可行性直接来自架构设计本身， 而非某个实现缺陷。发表于 CCS 2025，pp. 2159–2173。
- **信任边界**：跨租户、主机-设备 ｜ **发表**：CCS 2025
- **arXiv**：[2508.15036](https://arxiv.org/abs/2508.15036)

### 2.3 MoE 路由操纵与 Safety 削弱

*safety 行为与部分专家强相关，操纵 routing 可增强越狱。 这一节要求论文的攻击手段必须作用于**路由机制本身**， 而不是把普通越狱换个 MoE 模型重跑一遍*

#### Misrouter: Exploiting Routing Mechanisms for Input-Only Attacks on Mixture-of-Experts LLMs (Misrouter) (2026-05)
- **简介**：与需要改动权重或访问内部状态的攻击不同，本文探讨仅通过输入操纵路由的可能性。 攻击者不接触模型参数，只构造输入去改变 router 的专家选择， 使推理绕开承担安全职责的专家。这个威胁模型比 GateBreaker 更贴近真实部署 （攻击者通常只有 API 访问权），也因此更值得关注 —— 它说明 MoE 的路由机制本身就是一个可被合法输入操纵的攻击面。
- **信任边界**：模型内部
- **arXiv**：[2605.04446](https://arxiv.org/abs/2605.04446)

#### RouteHijack: Routing-Aware Attack on Mixture-of-Experts LLMs (RouteHijack) (2026-05)
- **简介**：从路由感知的角度构造针对 MoE 的攻击，与 GateBreaker、Misrouter 共同勾勒出 「routing 是 MoE 安全薄弱环节」这一判断。三篇工作的差异在威胁模型强度： GateBreaker 需要神经元级干预，Misrouter 限定为仅输入操纵， 本文则聚焦攻击者对路由行为的建模与利用。 收录这三篇是为了让读者能直接对比同一攻击面下不同威胁模型的可行性边界。
- **信任边界**：模型内部
- **arXiv**：[2605.02946](https://arxiv.org/abs/2605.02946)

#### GateBreaker: Gate-Guided Attacks on Mixture-of-Expert LLMs (GateBreaker) (2025-12)
- **简介**：发现 MoE 模型中存在一批在有害输入上被过度路由的「safety experts」， 模型的拒答行为高度依赖这少数专家。作者据此提出门控引导的攻击： 只需禁用约 3% 的神经元，攻击成功率就从 7.4% 抬升到 64.9%。 这个结果的意义在于揭示了 MoE 的安全对齐在架构层面是**局部且脆弱**的 —— 对齐信号集中在少量专家上，因而可以被针对性地绕过。已被 USENIX Security 2026 接收。
- **信任边界**：模型内部 ｜ **发表**：USENIX Security 2026
- **arXiv**：[2512.21008](https://arxiv.org/abs/2512.21008)

### 2.4 专家并行通信与负载劫持

*EP all-to-all 流量热点、straggler 诱导、跨租户延迟干扰*

#### Trigger the Straggler: Load Hijack on Mixture-of-Experts LLMs (Trigger the Straggler) (2026-08)
- **简介**：专家并行是跨多 GPU 部署 MoE 的常见策略，router 的决策同时决定了激活哪些专家 以及哪块 GPU 承担负载。本文指出攻击者可以构造输入把负载定向堆到少数设备上， 人为制造 straggler，从而干扰同一部署上其他租户的延迟。 这是 Semantic-to-Resource 攻击面的一个干净样本：一段合法 prompt 经由路由机制被放大成物理层面的资源倾斜与跨租户干扰。
- **信任边界**：节点间、跨租户
- **arXiv**：[2608.10614](https://arxiv.org/abs/2608.10614)

## 3 Infra 优化引发的 Safety 漂移

*传统 infra optimization 被理解为 performance / accuracy 的 tradeoff： `maximize throughput subject to accuracy >= X`。 但对 aligned 模型，量化与缓存压缩可以在 perplexity 几乎不变的情况下显著 破坏 refusal 行为 —— 也就是说 **utility 守住了，safety 掉了**。 本章追问：Model Safety 是否应当成为 Infra Optimization 的 invariant， 即目标是否应改为 `subject to utility >= X AND safety >= Y`。*

#### Quantization-Triggered Backdoors in Language Models: Cross-Quantizer Transferability and the Validation--Deployment Gap (Quant Backdoor) (2026-08)
- **简介**：研究一类由量化触发的后门：模型在全精度下表现完全正常，只有在被量化部署后 恶意行为才显现。本文进一步考察了这种后门在不同量化器之间的可迁移性， 说明攻击并不依赖某个特定量化实现。这条线把 infra 优化与供应链安全接在了一起 —— 部署环节的常规操作成为攻击的触发条件， 意味着仅审计发布的全精度权重不足以保证部署后的安全。
- **信任边界**：供应链、模型内部
- **arXiv**：[2608.27512](https://arxiv.org/abs/2608.27512)

#### Preserving Fairness and Safety in Quantized LLMs Through Critical Weight Protection (Critical Weight Protection) (2026-07)
- **简介**：针对量化导致公平性与安全性退化的问题，提出通过保护关键权重来维持这两项属性。 与只关注 perplexity 或下游任务准确率的常规量化工作不同， 本文把 fairness 与 safety 当作需要显式保护的目标。 这正是本章想推动的范式转变：infra 优化的约束条件应从 `accuracy >= X` 扩展为 `utility >= X AND safety >= Y`。 Findings of ACL 2026，pp. 19831–19855。
- **信任边界**：模型内部 ｜ **发表**：Findings of ACL 2026
- **链接**：https://aclanthology.org/2026.findings-acl.993/

#### When Efficiency Meets Safety: A Benchmark Security Analysis of KV Cache Compression in Large Language Models (Safe-CAM) (2026-07)
- **简介**：系统研究了 KV cache 压缩与越狱之间的关系，是这一交叉方向上少见的 benchmark 级工作。作者发现不同压缩方法对安全性的影响方向并不一致 —— 有的削弱安全性，有的反而增强，说明「压缩必然损害 safety」的直觉过于简化。 文中提出 Safe-CAM 作为缓解方案。ACL 2026 Long Paper，pp. 24472–24485。
- **信任边界**：模型内部 ｜ **发表**：ACL 2026
- **链接**：https://aclanthology.org/2026.acl-long.1123/

#### Alignment Collapse Under KV Cache Quantization: Diagnosis and Mitigation (Alignment Collapse) (2026-06)
- **简介**：本文给出了「infra 优化偷偷改变模型安全性」最直接的证据： KV cache 量化可以在 perplexity 几乎不变的情况下显著破坏模型的拒答与对齐行为。 这个现象很反直觉 —— 按传统 infra 视角，量化只是 performance/accuracy 的权衡， 而 accuracy 指标显示一切正常。作者进一步诊断了漂移的来源并给出缓解方案。 这篇支撑了本章的核心问题：safety 是否应当成为 infra optimization 的 invariant。
- **信任边界**：模型内部
- **arXiv**：[2606.09864](https://arxiv.org/abs/2606.09864)

## 4 训练侧完整性

*分布式训练有一个很特殊的安全属性：**local corruption can become global model corruption** —— 单个 rank 产生的错误张量经 collective 传播到全部 rank 并写入 checkpoint。目前这块大部分工作停留在 reliability 视角（SDC 检测），往 security 推一步（把 accidental faulty worker 换成 malicious worker）后基本还是空白。*

#### TrainSDC: Characterizing and Mitigating Silent Data Corruption in Large Language Model Training (TrainSDC) (2026-08)
- **简介**：刻画并缓解大模型训练中的静默数据损坏。与 AEGIS 的在线检测视角互补， 本文更侧重于 SDC 在训练过程中的表现形态与传播特征。 两篇合起来能给出「本地损坏如何变成全局模型损坏」的完整图景， 也为把该问题从 reliability 推向 security 提供了必要的现象基础。
- **信任边界**：节点间
- **arXiv**：[2608.30769](https://arxiv.org/abs/2608.30769)

#### Safeguarding LLM Training at Scale: Online SDC Detection and Insights from 35 Million GPU Hours (AEGIS) (2026-07)
- **简介**：清华与字节跳动基于 3500 万 GPU-hours 生产环境数据研究在线静默数据损坏检测， 是这一方向目前规模最大的实证工作。系统 AEGIS 在该规模下发现 18 起真实 SDC 与 13 块故障 GPU，运行开销仅 0.86%。这篇的价值在于用生产数据证实了 「单个 rank 的错误可经 collective 传播为全局模型污染」不是理论担忧。 目前该方向多停留在 reliability 视角，若把 accidental faulty worker 换成 malicious worker，分布式训练完整性几乎是一片空白。
- **信任边界**：节点间、供应链 ｜ **发表**：OSDI 2026
- **链接**：https://www.usenix.org/conference/osdi26/presentation/lei

## 5 硬件与执行环境

*GPU 微架构侧信道、光学/物理探测、TEE 与机密计算、远程证明*

#### JITterFlip: Uncovering Fault Attack Surfaces in JIT-Compiled LLM Serving (JITterFlip) (2026-08)
- **简介**：现代 serving 框架大量依赖 JIT 编译生成算子内核，本文系统梳理了这一层 此前未被审视的故障攻击面。作者指出 JIT 产物在运行时驻留于可被故障注入 影响的内存区域，针对性的比特翻转可以改变内核行为而不触发任何完整性检查。 这把传统硬件故障攻击与 LLM serving 的动态编译特性接在了一起， 属于本仓库「硬件与执行环境」章节里少见的 infra-native 工作。
- **信任边界**：主机-设备
- **arXiv**：[2608.29745](https://arxiv.org/abs/2608.29745)

#### LLMscope: Extracting LLM Assets from Edge AI Chips via Optical Probing (LLMscope) (2026-08)
- **简介**：通过光学探测手段从边缘 AI 芯片中提取模型资产，把物理层攻击引入 LLM 部署场景。 与依赖软件侧信道的工作不同，本文的威胁模型假设攻击者可物理接触设备， 这在边缘部署与终端设备场景下是现实的。收录本篇是为了让「硬件与执行环境」 一章覆盖从微架构侧信道到物理探测的完整谱系。
- **信任边界**：主机-设备、供应链
- **arXiv**：[2608.25321](https://arxiv.org/abs/2608.25321)

## 6 防御与系统机制

*按防御在系统栈上的介入层次组织：cache 隔离（如 cache salt）、 信息流追踪、隔离调度、确定性执行、审计与可观测性*

#### SEAL: Reinforcing Global Safety in Mixture-of-Experts through Shared Expert ALignment (SEAL) (2026-09)
- **简介**：针对 MoE 安全对齐局部化的问题（即 GateBreaker 揭示的少数专家承担全部安全职责）， 提出通过共享专家对齐来强化全局安全性。思路是不再把 safety 押在个别专家上， 而是让承担安全职责的能力在专家间共享，从而抬高针对性绕过的成本。 这是本仓库防御章节中直接回应 MoE 路由攻击的工作， 建议与第 2.3 节的三篇攻击工作对照阅读。
- **信任边界**：模型内部
- **arXiv**：[2609.02293](https://arxiv.org/abs/2609.02293)

#### Here is a GIFT: Enforcing User Data Isolation in LLM Serving via GPU Information Flow Tracking (GIFT) (2026-08)
- **简介**：LLM serving 框架在共享基础设施上处理大量用户数据，其中常含敏感信息， 而共享同一框架的用户之间缺乏强隔离保证。GIFT 把信息流追踪下沉到 GPU 层面， 在 vLLM 上实现了对用户数据流向的强制隔离。这是防御章节里少见的 系统机制级工作 —— 不是在输入输出侧加过滤器， 而是在执行基础设施内部建立可强制的隔离边界。
- **信任边界**：跨租户、主机-设备
- **arXiv**：[2608.25431](https://arxiv.org/abs/2608.25431)

## 7 工程侧安全（非 arXiv 来源）

*本章以 CVE、厂商安全公告、框架 issue/PR、fuzzing 工具为主。 原因：serving 框架的真实漏洞走的是 CVE 与 GitHub advisory 渠道而非 arXiv， 而学术清单普遍不收这类条目 —— 这是本仓库最容易形成差异化的部分。 沿用 GUI Agent 安全那轮的教训：凡高度依赖非 arXiv 来源的章节必须显式规划 检索流程，否则会整段缺失。周更时本章需单独走 CVE / advisory 流程， 不要因为 arXiv 无结果就跳过。*

#### vLLM Automatic Prefix Caching: Cache Isolation for Security (cache_salt) (cache_salt) (2025-06)
- **简介**：vLLM 针对 prefix cache timing 侧信道的官方防御机制。请求可携带 cache_salt 参数，该值会被注入首个 cache block 的 hash 计算，使不同租户即使 prefix 相同 也不会命中彼此的缓存。官方文档明确说明其目的是 "prevents timing-based attacks where an adversary could infer cached content by observing latency differences"。这条是学术攻击工作直接推动工程侧防御落地的 范例，也是第 7 章「工程侧安全」的典型条目形态。
- **信任边界**：跨租户 ｜ **发表**：vLLM 官方文档
- **链接**：https://docs.vllm.ai/en/latest/design/prefix_caching.html

---

## 贡献

只需修改 `data/papers.yaml`，`README.md` 与 `papers_by_*/` 下所有文件由 GitHub Actions 自动生成。收录标准与条目格式见 [CONTRIBUTING.md](CONTRIBUTING.md)，维护流程与检索口径见 [MAINTENANCE.md](MAINTENANCE.md)。

## 相关仓库

本仓库聚焦 LLM 基础设施自身的安全，以下方向请见：

- GUI / Computer-Use Agent 安全：`Yuxuan2003/Awesome-GUI-Agent-Security`
- LLM 安全与隐私大盘（模型层为主）：`ThuCCSLab/Awesome-LM-SSP`
- LLM 推理系统能力向研究：`AmadeusChan/Awesome-LLM-System-Papers`
- 模型压缩与量化（纯效率视角）：`HuangOwen/Awesome-LLM-Compression`

