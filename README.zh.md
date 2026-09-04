# Awesome-AI-Infra-Security

[English](README.md) ｜ **[中文](README.zh.md)**

> AI Infra 安全论文清单 —— LLM 推理与训练基础设施的攻击面、信任边界与防御，每篇附中文简介

![Last Update](https://img.shields.io/badge/last%20update-2026.09-brightgreen) ![Papers](https://img.shields.io/badge/papers-60%2B-blue) ![Time Range](https://img.shields.io/badge/time-2025.01--2026.09-orange) [![Link Check](https://github.com/Yuxuan2003/Awesome-AI-Infra-Security/actions/workflows/check.yml/badge.svg)](https://github.com/Yuxuan2003/Awesome-AI-Infra-Security/actions/workflows/check.yml) ![Awesome](https://img.shields.io/badge/-awesome-ff69b4)

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
| **0 威胁模型与综述** | · | · | 1 | · | · | 1 |
| **1 AI State Plane 安全** | 21 | 7 | 5 | 5 | 2 | 2 |
| **2 Semantic-to-Resource 攻击面** | 5 | · | 1 | 1 | · | 3 |
| **3 Infra 优化引发的 Safety 漂移** | 1 | · | · | · | 2 | 8 |
| **4 训练侧完整性** | · | · | · | 2 | 1 | · |
| **5 硬件与执行环境** | · | · | 3 | · | 1 | · |
| **6 防御与系统机制** | 2 | 1 | 4 | 1 | · | 2 |

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

按信任边界浏览：[跨租户](views/by-boundary/cross-tenant.md) ｜ [跨请求](views/by-boundary/cross-request.md) ｜ [主机-设备](views/by-boundary/host-device.md) ｜ [节点间](views/by-boundary/inter-node.md) ｜ [供应链](views/by-boundary/supply-chain.md) ｜ [模型内部](views/by-boundary/model-internal.md)

---

## 0 威胁模型与综述

*领域综述、SoK，以及「攻击面 × 信任边界」对照表。 本章负责回答「AI Infra 的安全边界和传统 Web/Cloud 有何本质不同」。*

#### Can Transformer Memory Be Corrupted? Investigating Cache-Side Vulnerabilities in Large Language Models (MTI) (2025-10)
- **简介**：即使 prompt 与权重都已受保护，推理时的 KV cache 仍是被忽视的完整性攻击面。本文提出 MTI 框架，对选定层与时间步的缓存 key 向量施加高斯噪声、置零与正交旋转等可控扰动，并从理论上把 logit 偏移与损坏的 Frobenius 范数挂钩。在 GPT-2 与 LLaMA-2-7B 上，扰动显著改变 next-token 分布并破坏 RAG 与 agentic 流水线，把 cache corruption 确立为可复现、有理论支撑的威胁模型。
- **信任边界**：主机-设备、模型内部
- **arXiv**：[2510.17098](https://arxiv.org/abs/2510.17098)

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

#### Efficient and Privacy Aware Edge Cloud Collaborative Inference for Large Language Models (2026-07)
- **简介**：全云端推理暴露用户 prompt，纯端侧推理又受硬件所限。该框架基于端点认证的 KV cache 做端云协同：端侧负责嵌入计算、 KV cache 认证与投机草稿，云端执行带 token 校验的认证解码；所有传输数据与截断 logits 经量化并 AES-GCM 加密，缓存 访问策略保留在本地以防泄露。相比基线 split inference，每 token 时延最高降低 46.1%，下行负载最高减少 67.4%，性能 与全云端推理相当。
- **信任边界**：节点间
- **arXiv**：[2607.13093](https://arxiv.org/abs/2607.13093)

#### Agent-Assisted Side-Channel Attacks on Non-Prefix KV Cache in RAG (2026-06)
- **简介**：既有 KV cache side channel 攻击依赖严格的前缀对齐，对含私有前缀的真实 RAG 查询失效。SpliceLeak 利用 chunk 感知 内存调度在非前缀 KV cache 融合时产生的确定性 "Step-Wave" 时序特征，先推断隐藏私有 prompt 的长度，再借助边界碰撞 逐 token 抽取语义内容；在 vLLM+LMCache 上有界熵场景下抽取成功率最高达 100%，每 token 最少只需 63 个请求。 作者提出 SpliceDefense（量化 chunk 填充 + 常数时间边界融合），将 side-channel 信号压平（Delta TTFT 约 0）且吞吐开销可忽略。
- **信任边界**：跨租户
- **arXiv**：[2606.21842](https://arxiv.org/abs/2606.21842)

#### OTRO: Oblivious Tokenization Path with Square-Root ORAM (OTRO) (2026-06)
- **简介**：在 CPU+GPU TEE 机密计算推理栈中，CPU 侧 tokenizer 的查表内存访问模式会泄露用户 prompt，已有工作在生产环境 Intel TDX 上端到端恢复 prompt；直接套用 PathORAM 会带来约 13 倍 tokenizer 减速、10-58% 的 TTFT 增长。OTRO 采用 square-root ORAM，结合只读表副本池、带 dummy 访问填充的 epoch 轮换和 KV-cache 感知的分块 tokenization，在 TDX CVM + H100 上将 TTFT 开销控制在至多 4.5%，额外内存不足 0.5 GB。
- **信任边界**：跨租户、主机-设备
- **arXiv**：[2606.17358](https://arxiv.org/abs/2606.17358)

#### CacheProbe: Auditing Prompt Cache Isolation in Gateway APIs (CacheProbe) (2026-05)
- **简介**：Prompt caching 通过跨请求复用 KV cache 节省算力，但许多实现无法抵抗 timing attack 甚至基本的元数据泄露。本文在 Gu et al. (ICML 2025) 的审计方法之上，检验 OpenRouter 这类 API 网关架构是否会绕过供应商级的 per-account prompt cache 隔离：当用户经 OpenRouter 以共享组织凭证路由时，可能在所有 OpenRouter 用户之间意外形成全局 cache 共享， 破坏多租户隔离保证。
- **信任边界**：跨租户
- **arXiv**：[2605.30613](https://arxiv.org/abs/2605.30613)

#### CachePrune: Privacy-Aware and Fine-Grained KV Cache Sharing for Efficient LLM Inference (CachePrune) (2026-05)
- **简介**：跨用户共享 KV cache 会让攻击者通过探测 cache 复用推断他人输入，而彻底关闭共享又浪费了系统指令等隐私无关片段的 复用价值。CachePrune 实现 token 级的隐私感知 KV 共享：基于敏感性掩码推导可变长度的可复用片段并高效检索。在 vLLM 上实现、三个数据集评估：消除 KV 复用 side channel 的直接泄露，同时 TTFT 降低 4.5 倍、cache 命中率较 SOTA 提升 44%。
- **信任边界**：跨租户
- **arXiv**：[2605.23640](https://arxiv.org/abs/2605.23640)

#### Continuous Discovery of Vulnerabilities in LLM Serving Systems with Fuzzing (2026-05)
- **简介**：LLM serving 层的高危故障（KV cache、prefix sharing、投机解码、多租户调度的共享状态交互）只在真实并发负载下出现， 常规模型/API 测试无法覆盖。灰盒模糊测试器 GRIEF 将带时序的多请求轨迹作为一等输入，用轻量 oracle 检测崩溃、挂起、 性能病态与静默输出污染，并通过受控重放与 log-probability 校验确认可复现故障。在 vLLM 与 SGLang 早期 campaign 中 发现 15 个漏洞（10 个获开发者确认，含 2 个 CVE），涵盖 KV-cache 隔离失效、跨请求干扰与嘈杂邻居 DoS。
- **信任边界**：跨租户、跨请求
- **arXiv**：[2605.11202](https://arxiv.org/abs/2605.11202)

#### Bit-Flip Vulnerability of Shared KV-Cache Blocks in LLM Serving Systems (2026-04)
- **简介**：vLLM Prefix Caching 中共享的 KV-cache block 只有一份物理拷贝且无完整性保护，是与 GPU Rowhammer 类似但未被检验的攻击面。 软件故障注入刻画出三点性质：16 个 BF16 比特位中 13 个产生静默偏移（输出连贯但已被篡改）；只有共享该前缀的请求受影响； 损伤随请求线性累积、无时间衰减。作者给出调度时校验和防御，可将累积损伤约束在单个 batch 内，开销可忽略。
- **信任边界**：跨租户、跨请求
- **arXiv**：[2604.17249](https://arxiv.org/abs/2604.17249)

#### PrefixWall: Mitigating Prefix Caching Side Channels in Shared LLM Systems (PrefixWall) (2026-03)
- **简介**：Automatic Prefix Caching (APC) 的命中/未命中时延差异构成 timing side channel，多租户攻击者可据此逐步重构他人请求； 现有防御一律关闭 APC，牺牲所有用户的效率。PrefixWall 监控跨用户 cache 复用、标记可疑共享，并仅在必要时选择性隔离 前缀。评估显示，与隔离式防御相比，PrefixWall 带来最高 70% 的 cache 复用提升和 30% 的推理时延下降，兼顾安全与性能。
- **信任边界**：跨租户
- **arXiv**：[2603.10726](https://arxiv.org/abs/2603.10726)

#### CacheTrap: Unveiling a Stealthier Gray-Box Trojan against LLMs (CacheTrap) (2025-11)
- **简介**：CacheTrap 是首个针对 LLM KV cache 的灰盒木马：在 KV cache 中翻转单个比特作为瞬态触发器，即可在不改动输入与模型 权重的情况下诱导目标行为。其高效搜索算法无需访问权重或数据集即可定位易受攻击的 cache 位置。在 5 个开源 LLM 上， 触发时攻击成功率达 100%，未触发时良性精度保持不变，代价仅是 KV cache 中的一个比特翻转。
- **信任边界**：模型内部
- **arXiv**：[2511.22681](https://arxiv.org/abs/2511.22681)

#### Shadow in the Cache: Unveiling and Mitigating Privacy Risks of KV-cache in LLM Inference (2025-08)
- **简介**：本文首次系统分析 LLM 推理中 KV-cache 的隐私风险，证明攻击者可直接从 KV-cache 重构敏感用户输入，并给出三条攻击 路径：直接反演攻击、适用范围更广的碰撞攻击和基于语义的注入攻击。防御方案 KV-Cloak 将可逆矩阵混淆与算子融合结合， 把重构质量压到随机噪声水平，同时几乎不损失模型精度、性能开销极小。
- **信任边界**：跨租户
- **arXiv**：[2508.09442](https://arxiv.org/abs/2508.09442)

#### CachePrune: Teaching LLMs What Not to Follow via KV-Cache Editing (2025-04)
- **简介**：LLM 无法区分 prompt 上下文中的数据与指令，因而易受间接 prompt injection 攻击。CachePrune 在对上下文进行 KV cache 编码时识别并剪除与指令遵从相关的神经元，引导模型把上下文纯粹当作数据处理；神经元识别由 preferential attribution loss 驱动，理论上与 DPO 目标的上界相关联。防御只作用于 cache 编码阶段、响应生成零额外开销，在显著降低攻击成功率 的同时保留正常指令遵从能力。
- **信任边界**：模型内部
- **arXiv**：[2504.21228](https://arxiv.org/abs/2504.21228)

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

#### MOSAIC: Masked Outsourcing of Secure AI Computations (MOSAIC) (2026-07)
- **简介**：面向把 Transformer 推理外包给不可信加速器的场景，要求客户端输入与模型都对服务端保密。MOSAIC 通过矩阵乘法 掩码协议引入少量噪声（安全性归约到 LWE/LPN 假设），并用随机 Hadamard 旋转抑制跨层误差累积；在 70B 模型上困惑度接近 BF16，HumanEval 上与之持平，客户端开销比已有方案低数个数量级。
- **信任边界**：节点间、主机-设备
- **arXiv**：[2607.29221](https://arxiv.org/abs/2607.29221)

#### (A)iSpy: Parasitic Trojans for Machine Learning Infrastructure ((A)iSpy) (2026-07)
- **简介**：寄生在 ML 运行时中的基础设施木马（基于 ONNX Runtime 训练与推理引擎实现），以"观察-执行"范式直接读取 计算图中的瞬时张量状态。它可将关键训练超参经由模型权重或输出 logits 隐蔽外泄，还能充当梯度放大器， 把成功率接近 0 的弱数据投毒放大为 100% 的后门攻击，并可绕过常规恶意软件扫描与模型审查工具。
- **信任边界**：供应链
- **arXiv**：[2607.17550](https://arxiv.org/abs/2607.17550)

#### Image Prompt Reconstruction Attacks on Distributed MLLM Inference Frameworks (2026-06)
- **简介**：针对分布式多模态 LLM 推理的首个图像提示重建攻击：参与节点间传输的中间 embedding 会泄露视觉输入。 作者先以 100% 准确率从几乎所有层中提取图像 embedding，再做像素级重建（MPAA）与基于扩散引导的语义 重建（IEDA）两种被动黑盒攻击，在 Gemma 3、Phi 4 Multimodal、Qwen 2.5 VL、Llama 4 Scout 四个模型族 上均取得稳定重建效果。
- **信任边界**：节点间、跨租户
- **arXiv**：[2606.18710](https://arxiv.org/abs/2606.18710)

#### Bifrost: Hybrid TEE-FHE Inference for Privacy-Preserving Transformer and LLM Serving (Bifrost) (2026-06)
- **简介**：混合 TEE-FHE 推理架构：密钥只发放给经远程证明的 CPU TEE，加速器、显存与驱动栈均在 TCB 之外；线性层 以 CKKS 密文委托给加速器，非线性算子与 KV 状态转移全部留在 TEE 内。Bifrost+ 进一步在 TEE 内构建 prompt 侧 KV，使估算延迟降低 9.25-9.91 倍，TTFT 较纯 FHE 部署降低 14.6-53.4 倍。
- **信任边界**：主机-设备、跨租户
- **arXiv**：[2606.17421](https://arxiv.org/abs/2606.17421)

#### The Vision Encoder as a Privacy Boundary: Visual-Token Side Channels in Encoder-Free Vision-Language Models (2026-06)
- **简介**：无编码器 VLM 将图像 patch 直接送入语言模型 token 流，使中间 visual token 成为输出前的 side channel。作者在 Gemma4 与 Fuyu 上反演 visual-token 流，恢复出可辨识的图像结构和可读的留出访问码，而带编码器的对照模型无法恢复精确字符串。 Gemma4 第 0 层 KV cache 张量可被直接反演，意味着泄露点就位于生产 serving 栈持久化的 KV cache 中；攻击对加噪和量化 等数值级防御有抵抗力，有效缓解必须降低空间采样率。
- **信任边界**：跨租户
- **arXiv**：[2606.14783](https://arxiv.org/abs/2606.14783)

#### Defense Against Prompt Inversion Attacks: An Information-Theoretic Approach for LLM Collaborative Inference (2026-06)
- **简介**：面向端云协同 LLM 推理中 prompt inversion（攻击者从传输的中间 activation 重建用户输入）的信息论防御。 通过低维信息瓶颈实现的 privacy adapter 显式最小化 activation 与输入 prompt 之间的互信息，并给出重建 误差与 token 级精度的理论界；在保持任务效用与延迟约束下，攻击成功率较已有防御最多降低 35%。
- **信任边界**：节点间
- **arXiv**：[2606.11592](https://arxiv.org/abs/2606.11592)

#### Good-Enough LLM Obfuscation (GELO) (GELO) (2026-03)
- **简介**：在共享加速器上，能读取设备内存的攻击者可观测 KV cache 与 hidden state，威胁 prompt 隐私；MPC/FHE 慢 1-2 个数量级。 GELO 对每个卸载的投影采样随机矩阵 A，卸载 U=AH 后回传再施加 A^{-1}，输出不变且混合矩阵绝不跨 batch 复用，攻击者 只剩单 batch 盲源分离问题；非正交混合掩盖 Gram 矩阵，高能 "shield" 向量污染高阶统计。Llama-2 7B 上 float32 输出 逐位不变，计算侧开销约 20-30%，60M 参数的 transformer 解混合攻击亦失败。
- **信任边界**：主机-设备
- **arXiv**：[2603.05035](https://arxiv.org/abs/2603.05035)

#### Attacks on Approximate Caches in Text-to-Image Diffusion Models (2025-08)
- **简介**：对文生图扩散模型服务中 approximate cache（复用相似 prompt 的中间状态）安全性的系统评估，指出该优化 破坏了用户间隔离。作者通过服务系统远程实现三类攻击：注入特殊关键词、数天后仍可恢复的隐蔽信道； 通过缓存命中恢复他人已缓存 prompt 的窃取攻击；向被盗 prompt 嵌入攻击者 logo、使命中缓存的后续请求 渲染出该 logo 的投毒攻击。
- **信任边界**：跨租户、跨请求
- **arXiv**：[2508.20424](https://arxiv.org/abs/2508.20424)

#### I Know What You Said: Unveiling Hardware Cache Side-Channels in Local Large Language Model Inference (2025-05)
- **简介**：揭示本地 LLM 推理中的硬件 cache 侧信道：从 token embedding 查表的缓存访问模式推断 token 值，从自回归 解码阶段的时序推断 token 位置，从而同时泄露输入与输出文本。无需特权、不与受害模型交互的窃听框架在 Llama、Falcon、Gemma 等部署上重建文本的平均编辑距离为输入 17.3%、输出 5.2%，余弦相似度约 98%。
- **信任边界**：跨租户
- **arXiv**：[2505.06738](https://arxiv.org/abs/2505.06738)

#### Spill The Beans: Exploiting CPU Cache Side-Channels to Leak Tokens from Large Language Models (Spill The Beans) (2025-05)
- **简介**：Flush+Reload 式 CPU cache 侧信道：攻击进程与受害 LLM 共置于同一硬件，监测共享末级缓存中 embedding 向量的访问命中并反推出生成的 token。通过在监测词表规模与缓存驱逐压力之间权衡，单次监测即可恢复 高熵 API key 的 80-90%，英文文本恢复率约 40%，暴露了 LLM 推理部署对传统侧信道的脆弱性。
- **信任边界**：跨租户
- **arXiv**：[2505.00817](https://arxiv.org/abs/2505.00817)

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

#### Grounded Cache Routing for Retrieval-Augmented Generation: When Is It Safe to Reuse an Answer? (2026-05)
- **简介**：RAG 中的输出级语义答案缓存很脆弱：检索证据随语料更新漂移，且对抗性碰撞攻击可劫持缓存响应。GroundedCache 提出 "何时复用才安全" 的框架，仅在查询相似度、证据重叠、来源版本有效性和词汇支撑四道门同时满足时才放行缓存答案。 在 Qwen2.5-7B + vLLM 的 12,000 次真实生成上以 unsafe-served rate (USR) 衡量：HotpotQA 各 regime 降至 0.0% （朴素缓存为 15-35%），mtRAG 文档漂移场景降至 1.5%（对比 51.5%），p50 端到端时延仅为无缓存基线的 1.04-1.07 倍。
- **信任边界**：跨租户、跨请求
- **arXiv**：[2605.27494](https://arxiv.org/abs/2605.27494)

#### Cache Me, Catch You: Cache Related Security Threats in LLM Serving Frameworks (Cache Me Catch You) (2026-02)
- **简介**：系统性审计了 LLM serving 框架中各类缓存的安全问题，指出现代 serving 的缓存 已不止 KV 一种，而是 prefix cache、semantic cache、image cache 并存。 作者发现了 prefix-cache hash 碰撞、image-cache 碰撞以及 semantic cache 的语义不一致三类问题，并落地为真实漏洞（含 CVE-2025-25183、CVE-2025-46722 等）。 这篇是本仓库第 7 章「工程侧安全」与学术研究结合得最好的范例。
- **信任边界**：跨租户、跨请求 ｜ **发表**：NDSS 2026
- **链接**：https://github.com/XingTuLab/Cache_Me_Catch_You
- **代码**：https://github.com/XingTuLab/Cache_Me_Catch_You

## 2 Semantic-to-Resource 攻击面

*这是 AI Infra 最根本的独特性：**用户输入的语义会直接决定底层计算拓扑、 缓存状态、GPU 内存占用、调度行为与网络通信**。普通 Web/Cloud 里 request content 与底层 resource state 相对解耦；LLM Infra 里一段 prompt 可以同时改变 KV 分配、 prefix 命中、batch 组成、抢占行为、MoE 专家路由与 GPU 间通信。 于是攻击者可以通过完全合法的 API 输入去操纵系统状态。*

### 2.1 Scheduler 状态操纵与延迟 DoS

*不打 GPU FLOPS，而是打 LLM serving 的状态机 —— 用少量精心构造的请求 操纵输出长度、KV 占用、batch 生命周期，诱发反复抢占与重算*

#### Bit-Exact AI Inference Verification Without Performance Tradeoffs (BitExactVerify) (2026-05)
- **简介**：针对利用 serving 自由度隐匿行为的隐蔽对手——隐写、未报告的推理软件改动、或通过未申报的 batch 元素夹带秘密计算（如 vLLM）。指出现代推理引擎输出确定但非不变，无需相同硬件即可通过纯软件仿真在多种 NVIDIA GPU 上逐比特复现，使浮点舍入误差累积成为可审计的软硬件指纹，而非可验证性的障碍。
- **信任边界**：跨租户
- **arXiv**：[2606.00279](https://arxiv.org/abs/2606.00279)

#### Rethinking Latency Denial-of-Service: Attacking the LLM Serving Framework, Not the Model (Fill and Squeeze) (2026-02)
- **简介**：传统 DoS 靠海量请求压垮算力，本文指出 LLM serving 存在更廉价的路径： 攻击的不是 GPU FLOPS，而是 serving 框架的状态机。作者提出 Fill and Squeeze 两阶段攻击 —— Fill 阶段用精心构造的请求占满全局 KV cache， Squeeze 阶段迫使调度器对其他租户的请求反复抢占与重算。 评估中受害者的首 token 时延劣化可达数十至数百倍量级， 而攻击者只需少量完全合法的 API 请求。
- **信任边界**：跨租户
- **arXiv**：[2602.07878](https://arxiv.org/abs/2602.07878)

#### RepetitionCurse: Measuring and Understanding Router Imbalance in Mixture-of-Experts LLMs under DoS Stress (RepetitionCurse) (2025-12)
- **简介**：揭示在专家并行推理中，分布外提示词可操纵 MoE 路由，使全部 token 集中落到同一组 top-k 专家上，导致部分设备过载、其余空转，把效率机制变为 DoS 攻击面。黑盒策略 RepetitionCurse 仅用重复 token 模式即可模型无关地构造对抗输入，在 Mixtral-8x7B 上将端到端延迟放大 3.063 倍，破坏 TTFT 服务等级协议。
- **信任边界**：跨租户
- **arXiv**：[2512.23995](https://arxiv.org/abs/2512.23995)

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

#### Speculative Decoding at Temperature Zero: A Scoped Safety-Invariance Screen with a 48,072-Sample Expansion (TAIS) (2026-06)
- **简介**：检验投机解码在零温度下是否会让草稿模型的行为渗入目标模型的安全输出。TAIS 等价性筛查覆盖 16,783 条确认样本加 44,066 条扩展样本（含 DPO 对抗草稿、GPTQ-4bit 草稿、fp16/bf16 执行），要求字节一致且满足 ±3pp 的 TOST 等价：refusal 率的最大 Cohen's h 仅 0.024，27 项对比中 25 项通过等价检验，未检出安全性漂移。
- **信任边界**：模型内部
- **arXiv**：[2606.25097](https://arxiv.org/abs/2606.25097)

#### AnchorKV: Safety-Aware KV Cache Compression via Soft Penalty with a Refusal Anchor (AnchorKV) (2026-06)
- **简介**：指出现有 KV cache 压缩虽能保住良性负载精度，却会在激进淘汰下削弱越狱防御、破坏拒答对齐。AnchorKV 借鉴 difference-of-means 表示工程，在 key 投影空间离线构建「拒答锚点」，对 token 保留分施加软惩罚，以很小的 utility 代价显著恢复安全对齐；惩罚系数为零时严格退化为原压缩器，可作为 drop-in 修改直接接入现有压缩流程。
- **信任边界**：模型内部
- **arXiv**：[2606.17872](https://arxiv.org/abs/2606.17872)

#### Alignment Collapse Under KV Cache Quantization: Diagnosis and Mitigation (Alignment Collapse) (2026-06)
- **简介**：本文给出了「infra 优化偷偷改变模型安全性」最直接的证据： KV cache 量化可以在 perplexity 几乎不变的情况下显著破坏模型的拒答与对齐行为。 这个现象很反直觉 —— 按传统 infra 视角，量化只是 performance/accuracy 的权衡， 而 accuracy 指标显示一切正常。作者进一步诊断了漂移的来源并给出缓解方案。 这篇支撑了本章的核心问题：safety 是否应当成为 infra optimization 的 invariant。
- **信任边界**：模型内部
- **arXiv**：[2606.09864](https://arxiv.org/abs/2606.09864)

#### Quantamination: Dynamic Quantization Leaks Your Data Across the Batch (Quantamination) (2026-04)
- **简介**：揭示主流框架广泛用于优化服务的动态量化会引入跨租户侧信道：攻击者将输入与受害者同批次推理时，可借助共享的运行时量化参数窃取对方数据。至少 4 个最流行的 ML 框架默认或可选配置会跨 batch 边界泄露信息，攻击者理论上可部分甚至完整恢复同批次其他用户输入，对现有 ML 服务框架构成严重隐私风险。
- **信任边界**：跨租户
- **arXiv**：[2604.26505](https://arxiv.org/abs/2604.26505)

#### Enhancing Trustworthiness with Mixed Precision: Benchmarks, Opportunities, and Challenges (QuantTrust) (2025-11)
- **简介**：系统考察量化对四类可信性指标（对抗鲁棒性、公平性、机器伦理、OOD 鲁棒性）的影响——这正是只盯 perplexity 与分类精度的主流量化框架所忽略的。实验发现可信性随压缩率与量化方法不稳定波动，并据此提出精度集成投票：融合同一模型多个混合精度变体的预测，使可信性指标最高提升 5.8%，为金融、医疗等高风险场景的量化部署敲响警钟。
- **信任边界**：模型内部
- **arXiv**：[2511.22483](https://arxiv.org/abs/2511.22483)

#### Fewer Weights, More Problems: A Practical Attack on LLM Pruning (FewerWeights) (2025-10)
- **简介**：首个针对部署侧剪枝的实用攻击：攻击者发布表面无害的模型，把恶意行为藏入不易被剪掉的参数，再用即将被剪的参数抵消其在完整模型中的表现，使用户经 vLLM 剪枝（Magnitude/Wanda/SparseGPT）后恶意行为才显现。在五个模型上越狱成功率最高 95.7%、良性指令拒答 98.7%、定向内容注入 99.5%，暴露「下载后剪枝再部署」这一供应链环节的安全缺口。
- **信任边界**：模型内部、供应链
- **arXiv**：[2510.07985](https://arxiv.org/abs/2510.07985)

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

#### CloakLM: Obfuscating GPU Memory Layout to Mitigate Model Ex-filtration for Serving (CloakLM) (2026-06)
- **简介**：在第三方或共享加速基础设施上，模型权重存储于大而连续、被反复访问的内存区域，使 PCIe 嗅探与 HBM dump 足以重建模型结构与参数。CloakLM 用纯软件方式消除这种结构规律性：PCIe 流量整形、层间与层内权重洗牌、HBM 物理页重映射。授权执行保持逻辑视图不变，未授权观察者只能看到碎片化、语义不连贯的状态。集成 vLLM 与 PyTorch，性能接近原生。
- **信任边界**：主机-设备
- **arXiv**：[2606.18400](https://arxiv.org/abs/2606.18400)

## 6 防御与系统机制

*按防御在系统栈上的介入层次组织：cache 隔离（如 cache salt）、 信息流追踪、隔离调度、确定性执行、审计与可观测性*

#### SEAL: Reinforcing Global Safety in Mixture-of-Experts through Shared Expert ALignment (SEAL) (2026-09)
- **简介**：针对 MoE 安全对齐局部化的问题（即 GateBreaker 揭示的少数专家承担全部安全职责）， 提出通过共享专家对齐来强化全局安全性。思路是不再把 safety 押在个别专家上， 而是让承担安全职责的能力在专家间共享，从而抬高针对性绕过的成本。 这是本仓库防御章节中直接回应 MoE 路由攻击的工作， 建议与第 2.3 节的三篇攻击工作对照阅读。
- **信任边界**：模型内部
- **arXiv**：[2609.02293](https://arxiv.org/abs/2609.02293)

#### Speculative Probing: LLM Monitoring at Speculative-Decoding Cost (SpecProbe) (2026-08)
- **简介**：把 serving 栈中本已驻留的投机解码模块复用为上下文感知的安全监控分类器：在目标序列尾部附加训练好的 soft prompt，推理时 KV cache 已在显存中，分类几乎零额外开销，无需再跑 Llama Guard 一类的独立 guard 模型。在四个模型上，小探针稳定超过零样本 GPT-5.4-mini，并在多语言提示安全任务上追平或超过 Qwen3Guard-Gen-8B、Llama-Guard-3-8B 等专用 8B 安全分类器。
- **信任边界**：模型内部
- **arXiv**：[2608.28099](https://arxiv.org/abs/2608.28099)

#### Here is a GIFT: Enforcing User Data Isolation in LLM Serving via GPU Information Flow Tracking (GIFT) (2026-08)
- **简介**：LLM serving 框架在共享基础设施上处理大量用户数据，其中常含敏感信息， 而共享同一框架的用户之间缺乏强隔离保证。GIFT 把信息流追踪下沉到 GPU 层面， 在 vLLM 上实现了对用户数据流向的强制隔离。这是防御章节里少见的 系统机制级工作 —— 不是在输入输出侧加过滤器， 而是在执行基础设施内部建立可强制的隔离边界。
- **信任边界**：跨租户、主机-设备
- **arXiv**：[2608.25431](https://arxiv.org/abs/2608.25431)

#### HadAgent: Harness-Aware Decentralized Agentic AI Serving with Proof-of-Inference Blockchain Consensus (HadAgent) (2026-04)
- **简介**：去中心化智能体 serving 系统，以 Proof-of-Inference 替代哈希挖矿：节点通过执行确定性 LLM 推理获得出块权，跨节点验证只需重放一次前向传播。三通道区块体各自带独立 Merkle 根实现细粒度篡改检测；harness 层以心跳探针与确定性重算做异常检测，并按历史行为将节点分层为可信/不可信。篡改记录检测率 100%、误报率 0%，对抗节点两轮内被隔离，诚实节点五轮内晋升可信。
- **信任边界**：节点间
- **arXiv**：[2604.18614](https://arxiv.org/abs/2604.18614)

#### AgenTEE: Confidential LLM Agent Execution on Edge Devices (AgenTEE) (2026-04)
- **简介**：面向边缘设备的机密 LLM 智能体执行系统：将智能体运行时、推理引擎与第三方应用分别放入 Arm CCA 上独立可远程证明的机密虚拟机（cVM），组件间仅经显式、可验证的通道交互，在恶意用户与不可信 OS 的威胁模型下保护系统提示词、模型权重与运行时状态。多 cVM 架构相比普通多进程部署的运行时开销低于 5.15%，接近原生性能。
- **信任边界**：主机-设备
- **arXiv**：[2604.18231](https://arxiv.org/abs/2604.18231)

#### FlexServe: A Fast and Secure LLM Serving System for Mobile Devices with Flexible Resource Isolation (FlexServe) (2026-03)
- **简介**：面向 OS 内核被攻破的威胁模型保护端侧 LLM 推理中的模型权重与用户数据：基于 ARM TrustZone 的灵活资源隔离机制（Flex-Mem 与 Flex-NPU）让内存页和 NPU 在保护与未保护模式间高效切换，配合 LLM 感知内存管理与安全推理流水线，相比 TrustZone 朴素方案取得平均 10.05 倍 TTFT 加速，多模型智能体工作流端到端最高加速 24.30 倍。
- **信任边界**：主机-设备
- **arXiv**：[2603.09046](https://arxiv.org/abs/2603.09046)

#### SuperLocalMemory: Privacy-Preserving Multi-Agent Memory with Bayesian Trust Defense Against Memory Poisoning (SuperLocalMemory) (2026-02)
- **简介**：本地优先的多智能体记忆系统，针对 OWASP ASI06 记忆投毒威胁，以架构隔离加贝叶斯信任评分阻断被投毒记忆跨会话、跨用户传播，全程不依赖云端与 LLM 调用。SQLite+FTS5 存储、逐智能体溯源与 Leiden 知识图谱聚类支撑下，中位检索延迟 10.6ms，10 个并发智能体零冲突；信任分离度达 0.90，对潜伏型（sleeper）攻击的信任衰减 72%，行为数据独立建库并支持 GDPR 第 17 条删除权。
- **信任边界**：跨请求
- **arXiv**：[2603.02240](https://arxiv.org/abs/2603.02240)

#### Confidential LLM Inference: Performance and Cost Across CPU and GPU TEEs (cLLM-TEE) (2025-09)
- **简介**：首次系统评估将端到端 LLM 推理完整置于 CPU 与 GPU TEE 内实现机密推理服务的可行性与代价：Llama2 7B/13B/70B 在 Intel TDX/SGX 中结合 AMX 加速，吞吐量开销低于 10%、延迟开销低于 20%；H100 机密计算 GPU 吞吐损失 4-8% 且随 batch 增大而缩小，并给出 12 条关于性能-成本-安全权衡的实证结论。
- **信任边界**：主机-设备
- **arXiv**：[2509.18886](https://arxiv.org/abs/2509.18886)

#### Selective KV-Cache Sharing to Mitigate Timing Side-Channels in LLM Inference (SafeKV) (2025-08)
- **简介**：全局 KV cache 共享在多租户推理中引入了 API 可见的 timing 侧信道，攻击者可据共享条目推断他人输入。SafeKV 把隐私执行与缓存管理做系统级协同设计：三层异步检测流水线把隐私分类与推理解耦，radix-tree 内存管理器支持敏感度感知驱逐，RDR 引导的运行时防护约束残余泄漏。相比完全隔离，TTFT 开销最高降低 40.58%，吞吐最高提升 2.66 倍。
- **信任边界**：跨租户
- **arXiv**：[2508.08438](https://arxiv.org/abs/2508.08438)

## 7 工程侧安全（非 arXiv 来源）

*本章以 CVE、厂商安全公告、框架 issue/PR、fuzzing 工具为主。 原因：serving 框架的真实漏洞走的是 CVE 与 GitHub advisory 渠道而非 arXiv， 而学术清单普遍不收这类条目 —— 这是本仓库最容易形成差异化的部分。 沿用 GUI Agent 安全那轮的教训：凡高度依赖非 arXiv 来源的章节必须显式规划 检索流程，否则会整段缺失。周更时本章需单独走 CVE / advisory 流程， 不要因为 arXiv 无结果就跳过。*

#### vLLM Automatic Prefix Caching: Cache Isolation for Security (cache_salt) (cache_salt) (2025-06)
- **简介**：vLLM 针对 prefix cache timing 侧信道的官方防御机制。请求可携带 cache_salt 参数，该值会被注入首个 cache block 的 hash 计算，使不同租户即使 prefix 相同 也不会命中彼此的缓存。官方文档明确说明其目的是 "prevents timing-based attacks where an adversary could infer cached content by observing latency differences"。这条是学术攻击工作直接推动工程侧防御落地的 范例，也是第 7 章「工程侧安全」的典型条目形态。
- **信任边界**：跨租户 ｜ **发表**：vLLM 官方文档
- **链接**：https://docs.vllm.ai/en/latest/design/prefix_caching.html

---

## 贡献

只需修改 `data/papers.yaml`，`README.md`、`README.zh.md` 与 `views/` 下所有文件由 GitHub Actions 自动生成。收录标准与条目格式见 [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md)，维护流程与检索口径见 [docs/MAINTENANCE.md](docs/MAINTENANCE.md)。

## 相关仓库

本仓库聚焦 LLM 基础设施自身的安全，以下方向请见：

- GUI / Computer-Use Agent 安全：`Yuxuan2003/Awesome-GUI-Agent-Security`
- LLM 安全与隐私大盘（模型层为主）：`ThuCCSLab/Awesome-LM-SSP`
- LLM 推理系统能力向研究：`AmadeusChan/Awesome-LLM-System-Papers`
- 模型压缩与量化（纯效率视角）：`HuangOwen/Awesome-LLM-Compression`

