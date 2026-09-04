# 信任边界：主机-设备

*CPU 与 GPU/加速器之间，含 PCIe、驱动、显存　信任边界是交叉标签，同一篇论文可能出现在多个分组中。*

> 本文件由 `scripts/build.py` 生成，请勿手工编辑。

#### JITterFlip: Uncovering Fault Attack Surfaces in JIT-Compiled LLM Serving (JITterFlip) (2026-08)
- **简介**：现代 serving 框架大量依赖 JIT 编译生成算子内核，本文系统梳理了这一层 此前未被审视的故障攻击面。作者指出 JIT 产物在运行时驻留于可被故障注入 影响的内存区域，针对性的比特翻转可以改变内核行为而不触发任何完整性检查。 这把传统硬件故障攻击与 LLM serving 的动态编译特性接在了一起， 属于本仓库「硬件与执行环境」章节里少见的 infra-native 工作。
- **信任边界**：主机-设备
- **arXiv**：[2608.29745](https://arxiv.org/abs/2608.29745)

#### Here is a GIFT: Enforcing User Data Isolation in LLM Serving via GPU Information Flow Tracking (GIFT) (2026-08)
- **简介**：LLM serving 框架在共享基础设施上处理大量用户数据，其中常含敏感信息， 而共享同一框架的用户之间缺乏强隔离保证。GIFT 把信息流追踪下沉到 GPU 层面， 在 vLLM 上实现了对用户数据流向的强制隔离。这是防御章节里少见的 系统机制级工作 —— 不是在输入输出侧加过滤器， 而是在执行基础设施内部建立可强制的隔离边界。
- **信任边界**：跨租户、主机-设备
- **arXiv**：[2608.25431](https://arxiv.org/abs/2608.25431)

#### LLMscope: Extracting LLM Assets from Edge AI Chips via Optical Probing (LLMscope) (2026-08)
- **简介**：通过光学探测手段从边缘 AI 芯片中提取模型资产，把物理层攻击引入 LLM 部署场景。 与依赖软件侧信道的工作不同，本文的威胁模型假设攻击者可物理接触设备， 这在边缘部署与终端设备场景下是现实的。收录本篇是为了让「硬件与执行环境」 一章覆盖从微架构侧信道到物理探测的完整谱系。
- **信任边界**：主机-设备、供应链
- **arXiv**：[2608.25321](https://arxiv.org/abs/2608.25321)

#### SparSEEty: Extracting Tokens from Sparsity-Exploiting LLM Serving Systems via Deterministic Side Channels (SparSEEty) (2026-08)
- **简介**：现代 LLM 存在激活稀疏性，只有部分神经元会被给定 token 激活，serving 系统 普遍利用这一性质做优化。本文指出这种优化把模型的内部激活模式暴露成了 可观测的确定性侧信道：由于稀疏模式与输入 token 强相关且执行路径确定， 攻击者可据此反推出被处理的 token。这是「性能优化把模型内部状态外化」 这一类问题的典型案例，与 KV cache 侧信道同源但作用在激活层面。
- **信任边界**：跨租户、主机-设备
- **arXiv**：[2608.02995](https://arxiv.org/abs/2608.02995)

#### MoEcho: Exploiting Side-Channel Attacks to Compromise User Privacy in Mixture-of-Experts LLMs (MoEcho) (2025-08)
- **简介**：东北大学团队的工作，是 MoE 架构侧信道这条线的代表作。核心观察是 MoE 让 模型语义决定物理执行路径：不同领域的 prompt 会激活不同的专家组合。 作者利用 CPU/GPU 上的 cache、TLB、performance counter 等侧信道推断专家 激活模式，并进一步还原 prompt 与 response 信息。这是标准的 「模型架构 × 系统安全」交叉点 —— 攻击可行性直接来自架构设计本身， 而非某个实现缺陷。发表于 CCS 2025，pp. 2159–2173。
- **信任边界**：跨租户、主机-设备 ｜ **发表**：CCS 2025
- **arXiv**：[2508.15036](https://arxiv.org/abs/2508.15036)
