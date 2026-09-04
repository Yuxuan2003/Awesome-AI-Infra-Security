# 信任边界：跨请求

*同一租户不同请求之间，含会话隔离失效　信任边界是交叉标签，同一篇论文可能出现在多个分组中。*

> 本文件由 `scripts/build.py` 生成，请勿手工编辑。

#### Governing the KV Cache: Preventing Timing Side-Channel Leakage in Multi-Tenant LLM Inference (KV Governance) (2026-08)
- **简介**：KV cache 是现代 LLM 推理最主要的吞吐优化手段，它让 prefix 可以跨请求复用； 但在多租户部署下这份缓存是共享的，命中与否会体现在首 token 时延上， 于是纯粹的性能优化直接变成了隐私侧信道。本文系统刻画了 vLLM 与 SGLang 中 prefix 复用带来的 timing channel，并给出缓存治理层面的防御设计， 在保留大部分复用收益的同时切断攻击者据时延差异探测他人缓存内容的能力。
- **信任边界**：跨租户、跨请求
- **arXiv**：[2608.09225](https://arxiv.org/abs/2608.09225)

#### HijackKV: New Threat in Position-Independent KV Cache Reuse (HijackKV) (2026-07)
- **简介**：为提升复用率，新一代缓存方案允许位置无关的 KV 重用 —— 同一段文本的 KV 不再绑定在原有位置上即可被复用。本文指出这种放松引入了新的攻击面： 攻击者可以让被复用的 KV 片段在新上下文中承载与原意不同的语义， 从而在模型输入表面完全正常的情况下篡改其内部上下文。这类攻击的隐蔽性在于 prompt 本身是良性的，被改变的是模型实际看到的内部状态。
- **信任边界**：跨请求、跨租户
- **arXiv**：[2607.19957](https://arxiv.org/abs/2607.19957)

#### Cache Me, Catch You: Cache Related Security Threats in LLM Serving Frameworks (Cache Me Catch You) (2026-02)
- **简介**：系统性审计了 LLM serving 框架中各类缓存的安全问题，指出现代 serving 的缓存 已不止 KV 一种，而是 prefix cache、semantic cache、image cache 并存。 作者发现了 prefix-cache hash 碰撞、image-cache 碰撞以及 semantic cache 的语义不一致三类问题，并落地为真实漏洞（含 CVE-2025-25183、CVE-2025-46722 等）。 这篇是本仓库第 7 章「工程侧安全」与学术研究结合得最好的范例。
- **信任边界**：跨租户、跨请求 ｜ **发表**：NDSS 2026
- **链接**：https://github.com/XingTuLab/Cache_Me_Catch_You
- **代码**：https://github.com/XingTuLab/Cache_Me_Catch_You
