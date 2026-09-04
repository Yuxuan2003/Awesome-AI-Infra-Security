# 信任边界：节点间

*多机之间，含 RDMA、collective、EP all-to-all　信任边界是交叉标签，同一篇论文可能出现在多个分组中。*

> 本文件由 `scripts/build.py` 生成，请勿手工编辑。

#### TrainSDC: Characterizing and Mitigating Silent Data Corruption in Large Language Model Training (TrainSDC) (2026-08)
- **简介**：刻画并缓解大模型训练中的静默数据损坏。与 AEGIS 的在线检测视角互补， 本文更侧重于 SDC 在训练过程中的表现形态与传播特征。 两篇合起来能给出「本地损坏如何变成全局模型损坏」的完整图景， 也为把该问题从 reliability 推向 security 提供了必要的现象基础。
- **信任边界**：节点间
- **arXiv**：[2608.30769](https://arxiv.org/abs/2608.30769)

#### Trigger the Straggler: Load Hijack on Mixture-of-Experts LLMs (Trigger the Straggler) (2026-08)
- **简介**：专家并行是跨多 GPU 部署 MoE 的常见策略，router 的决策同时决定了激活哪些专家 以及哪块 GPU 承担负载。本文指出攻击者可以构造输入把负载定向堆到少数设备上， 人为制造 straggler，从而干扰同一部署上其他租户的延迟。 这是 Semantic-to-Resource 攻击面的一个干净样本：一段合法 prompt 经由路由机制被放大成物理层面的资源倾斜与跨租户干扰。
- **信任边界**：节点间、跨租户
- **arXiv**：[2608.10614](https://arxiv.org/abs/2608.10614)

#### Safeguarding LLM Training at Scale: Online SDC Detection and Insights from 35 Million GPU Hours (AEGIS) (2026-07)
- **简介**：清华与字节跳动基于 3500 万 GPU-hours 生产环境数据研究在线静默数据损坏检测， 是这一方向目前规模最大的实证工作。系统 AEGIS 在该规模下发现 18 起真实 SDC 与 13 块故障 GPU，运行开销仅 0.86%。这篇的价值在于用生产数据证实了 「单个 rank 的错误可经 collective 传播为全局模型污染」不是理论担忧。 目前该方向多停留在 reliability 视角，若把 accidental faulty worker 换成 malicious worker，分布式训练完整性几乎是一片空白。
- **信任边界**：节点间、供应链 ｜ **发表**：OSDI 2026
- **链接**：https://www.usenix.org/conference/osdi26/presentation/lei

#### Denial of Deadline: Network-Driven Accuracy Collapse in Distributed Inference Pipelines (Denial of Deadline) (2026-07)
- **简介**：分布式推理流水线依赖节点间网络按时交付中间结果，本文指出攻击者无需击穿 任何计算节点，只要在网络层制造有针对性的延迟，就能让流水线错过截止时间， 迫使系统退化到降级路径并造成精度崩塌。这类攻击的特殊之处在于攻击目标 既不是可用性也不是机密性，而是**推理结果的正确性**， 且从单节点视角看每个组件都在正常工作。
- **信任边界**：节点间
- **arXiv**：[2607.24692](https://arxiv.org/abs/2607.24692)
