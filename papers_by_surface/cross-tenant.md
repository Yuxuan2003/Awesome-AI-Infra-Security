# 信任边界：跨租户

*同一 serving 实例上不同用户/组织之间　信任边界是交叉标签，同一篇论文可能出现在多个分组中。*

> 本文件由 `scripts/build.py` 生成，请勿手工编辑。

#### Here is a GIFT: Enforcing User Data Isolation in LLM Serving via GPU Information Flow Tracking (GIFT) (2026-08)
- **简介**：LLM serving 框架在共享基础设施上处理大量用户数据，其中常含敏感信息， 而共享同一框架的用户之间缺乏强隔离保证。GIFT 把信息流追踪下沉到 GPU 层面， 在 vLLM 上实现了对用户数据流向的强制隔离。这是防御章节里少见的 系统机制级工作 —— 不是在输入输出侧加过滤器， 而是在执行基础设施内部建立可强制的隔离边界。
- **信任边界**：跨租户、主机-设备
- **arXiv**：[2608.25431](https://arxiv.org/abs/2608.25431)

#### Uncovering and Understanding Hidden Dependencies in the LLM API Reseller Ecosystem via Prefix-Cache Side Channels (Reseller Probing) (2026-08)
- **简介**：LLM API 转售商已成为访问模型服务的重要一层，但多级转售让供应链变得不透明： 用户的请求可能经过若干未披露的上游。本文把 prefix-cache 侧信道用作探针， 通过构造探测 prompt 并观测缓存命中特征，反推出转售商背后的真实上游依赖关系。 这是一个把 infra 侧信道用于生态测绘的有趣转向 —— 侧信道不止能偷 prompt， 还能揭示服务提供方刻意隐藏的拓扑结构，对合规与数据流向审计都有直接意义。
- **信任边界**：跨租户、供应链
- **arXiv**：[2608.20732](https://arxiv.org/abs/2608.20732)

#### Trigger the Straggler: Load Hijack on Mixture-of-Experts LLMs (Trigger the Straggler) (2026-08)
- **简介**：专家并行是跨多 GPU 部署 MoE 的常见策略，router 的决策同时决定了激活哪些专家 以及哪块 GPU 承担负载。本文指出攻击者可以构造输入把负载定向堆到少数设备上， 人为制造 straggler，从而干扰同一部署上其他租户的延迟。 这是 Semantic-to-Resource 攻击面的一个干净样本：一段合法 prompt 经由路由机制被放大成物理层面的资源倾斜与跨租户干扰。
- **信任边界**：节点间、跨租户
- **arXiv**：[2608.10614](https://arxiv.org/abs/2608.10614)

#### Governing the KV Cache: Preventing Timing Side-Channel Leakage in Multi-Tenant LLM Inference (KV Governance) (2026-08)
- **简介**：KV cache 是现代 LLM 推理最主要的吞吐优化手段，它让 prefix 可以跨请求复用； 但在多租户部署下这份缓存是共享的，命中与否会体现在首 token 时延上， 于是纯粹的性能优化直接变成了隐私侧信道。本文系统刻画了 vLLM 与 SGLang 中 prefix 复用带来的 timing channel，并给出缓存治理层面的防御设计， 在保留大部分复用收益的同时切断攻击者据时延差异探测他人缓存内容的能力。
- **信任边界**：跨租户、跨请求
- **arXiv**：[2608.09225](https://arxiv.org/abs/2608.09225)

#### SparSEEty: Extracting Tokens from Sparsity-Exploiting LLM Serving Systems via Deterministic Side Channels (SparSEEty) (2026-08)
- **简介**：现代 LLM 存在激活稀疏性，只有部分神经元会被给定 token 激活，serving 系统 普遍利用这一性质做优化。本文指出这种优化把模型的内部激活模式暴露成了 可观测的确定性侧信道：由于稀疏模式与输入 token 强相关且执行路径确定， 攻击者可据此反推出被处理的 token。这是「性能优化把模型内部状态外化」 这一类问题的典型案例，与 KV cache 侧信道同源但作用在激活层面。
- **信任边界**：跨租户、主机-设备
- **arXiv**：[2608.02995](https://arxiv.org/abs/2608.02995)

#### HijackKV: New Threat in Position-Independent KV Cache Reuse (HijackKV) (2026-07)
- **简介**：为提升复用率，新一代缓存方案允许位置无关的 KV 重用 —— 同一段文本的 KV 不再绑定在原有位置上即可被复用。本文指出这种放松引入了新的攻击面： 攻击者可以让被复用的 KV 片段在新上下文中承载与原意不同的语义， 从而在模型输入表面完全正常的情况下篡改其内部上下文。这类攻击的隐蔽性在于 prompt 本身是良性的，被改变的是模型实际看到的内部状态。
- **信任边界**：跨请求、跨租户
- **arXiv**：[2607.19957](https://arxiv.org/abs/2607.19957)

#### Cache Me, Catch You: Cache Related Security Threats in LLM Serving Frameworks (Cache Me Catch You) (2026-02)
- **简介**：系统性审计了 LLM serving 框架中各类缓存的安全问题，指出现代 serving 的缓存 已不止 KV 一种，而是 prefix cache、semantic cache、image cache 并存。 作者发现了 prefix-cache hash 碰撞、image-cache 碰撞以及 semantic cache 的语义不一致三类问题，并落地为真实漏洞（含 CVE-2025-25183、CVE-2025-46722 等）。 这篇是本仓库第 7 章「工程侧安全」与学术研究结合得最好的范例。
- **信任边界**：跨租户、跨请求 ｜ **发表**：NDSS 2026
- **链接**：https://github.com/XingTuLab/Cache_Me_Catch_You
- **代码**：https://github.com/XingTuLab/Cache_Me_Catch_You

#### Rethinking Latency Denial-of-Service: Attacking the LLM Serving Framework, Not the Model (Fill and Squeeze) (2026-02)
- **简介**：传统 DoS 靠海量请求压垮算力，本文指出 LLM serving 存在更廉价的路径： 攻击的不是 GPU FLOPS，而是 serving 框架的状态机。作者提出 Fill and Squeeze 两阶段攻击 —— Fill 阶段用精心构造的请求占满全局 KV cache， Squeeze 阶段迫使调度器对其他租户的请求反复抢占与重算。 评估中受害者的首 token 时延劣化可达数十至数百倍量级， 而攻击者只需少量完全合法的 API 请求。
- **信任边界**：跨租户
- **arXiv**：[2602.07878](https://arxiv.org/abs/2602.07878)

#### MoEcho: Exploiting Side-Channel Attacks to Compromise User Privacy in Mixture-of-Experts LLMs (MoEcho) (2025-08)
- **简介**：东北大学团队的工作，是 MoE 架构侧信道这条线的代表作。核心观察是 MoE 让 模型语义决定物理执行路径：不同领域的 prompt 会激活不同的专家组合。 作者利用 CPU/GPU 上的 cache、TLB、performance counter 等侧信道推断专家 激活模式，并进一步还原 prompt 与 response 信息。这是标准的 「模型架构 × 系统安全」交叉点 —— 攻击可行性直接来自架构设计本身， 而非某个实现缺陷。发表于 CCS 2025，pp. 2159–2173。
- **信任边界**：跨租户、主机-设备 ｜ **发表**：CCS 2025
- **arXiv**：[2508.15036](https://arxiv.org/abs/2508.15036)

#### vLLM Automatic Prefix Caching: Cache Isolation for Security (cache_salt) (cache_salt) (2025-06)
- **简介**：vLLM 针对 prefix cache timing 侧信道的官方防御机制。请求可携带 cache_salt 参数，该值会被注入首个 cache block 的 hash 计算，使不同租户即使 prefix 相同 也不会命中彼此的缓存。官方文档明确说明其目的是 "prevents timing-based attacks where an adversary could infer cached content by observing latency differences"。这条是学术攻击工作直接推动工程侧防御落地的 范例，也是第 7 章「工程侧安全」的典型条目形态。
- **信任边界**：跨租户 ｜ **发表**：vLLM 官方文档
- **链接**：https://docs.vllm.ai/en/latest/design/prefix_caching.html

#### I Know What You Asked: Prompt Leakage via KV-Cache Sharing in Multi-Tenant LLM Serving (PromptPeek) (2025-02)
- **简介**：南方科技大学与字节跳动的工作，是 KV prefix 共享攻击这条线的奠基论文之一。 作者提出 PromptPeek 攻击：在多租户 serving 中，攻击者通过构造候选 prefix 并测量首 token 时延判断缓存是否命中，据此逐步推断出其他用户 prompt 的内容。 该工作直接推动了工程侧的防御响应 —— vLLM 随后引入 cache_salt 机制， 把租户标识注入首个 cache block 的 hash 以隔离这条 timing channel。
- **信任边界**：跨租户 ｜ **发表**：NDSS 2025
- **链接**：https://www.ndss-symposium.org/ndss-paper/i-know-what-you-asked-prompt-leakage-via-kv-cache-sharing-in-multi-tenant-llm-serving/
