# 信任边界：供应链

*模型权重、框架依赖、编译工具链、镜像　信任边界是交叉标签，同一篇论文可能出现在多个分组中。*

> 本文件由 `scripts/build.py` 生成，请勿手工编辑。

#### Quantization-Triggered Backdoors in Language Models: Cross-Quantizer Transferability and the Validation--Deployment Gap (Quant Backdoor) (2026-08)
- **简介**：研究一类由量化触发的后门：模型在全精度下表现完全正常，只有在被量化部署后 恶意行为才显现。本文进一步考察了这种后门在不同量化器之间的可迁移性， 说明攻击并不依赖某个特定量化实现。这条线把 infra 优化与供应链安全接在了一起 —— 部署环节的常规操作成为攻击的触发条件， 意味着仅审计发布的全精度权重不足以保证部署后的安全。
- **信任边界**：供应链、模型内部
- **arXiv**：[2608.27512](https://arxiv.org/abs/2608.27512)

#### LLMscope: Extracting LLM Assets from Edge AI Chips via Optical Probing (LLMscope) (2026-08)
- **简介**：通过光学探测手段从边缘 AI 芯片中提取模型资产，把物理层攻击引入 LLM 部署场景。 与依赖软件侧信道的工作不同，本文的威胁模型假设攻击者可物理接触设备， 这在边缘部署与终端设备场景下是现实的。收录本篇是为了让「硬件与执行环境」 一章覆盖从微架构侧信道到物理探测的完整谱系。
- **信任边界**：主机-设备、供应链
- **arXiv**：[2608.25321](https://arxiv.org/abs/2608.25321)

#### Uncovering and Understanding Hidden Dependencies in the LLM API Reseller Ecosystem via Prefix-Cache Side Channels (Reseller Probing) (2026-08)
- **简介**：LLM API 转售商已成为访问模型服务的重要一层，但多级转售让供应链变得不透明： 用户的请求可能经过若干未披露的上游。本文把 prefix-cache 侧信道用作探针， 通过构造探测 prompt 并观测缓存命中特征，反推出转售商背后的真实上游依赖关系。 这是一个把 infra 侧信道用于生态测绘的有趣转向 —— 侧信道不止能偷 prompt， 还能揭示服务提供方刻意隐藏的拓扑结构，对合规与数据流向审计都有直接意义。
- **信任边界**：跨租户、供应链
- **arXiv**：[2608.20732](https://arxiv.org/abs/2608.20732)

#### Safeguarding LLM Training at Scale: Online SDC Detection and Insights from 35 Million GPU Hours (AEGIS) (2026-07)
- **简介**：清华与字节跳动基于 3500 万 GPU-hours 生产环境数据研究在线静默数据损坏检测， 是这一方向目前规模最大的实证工作。系统 AEGIS 在该规模下发现 18 起真实 SDC 与 13 块故障 GPU，运行开销仅 0.86%。这篇的价值在于用生产数据证实了 「单个 rank 的错误可经 collective 传播为全局模型污染」不是理论担忧。 目前该方向多停留在 reliability 视角，若把 accidental faulty worker 换成 malicious worker，分布式训练完整性几乎是一片空白。
- **信任边界**：节点间、供应链 ｜ **发表**：OSDI 2026
- **链接**：https://www.usenix.org/conference/osdi26/presentation/lei
