# 信任边界：模型内部

*不跨越部署边界，但改变了模型自身的安全行为（如量化导致的对齐漂移）　信任边界是交叉标签，同一篇论文可能出现在多个分组中。*

> 本文件由 `scripts/build.py` 生成，请勿手工编辑。

#### SEAL: Reinforcing Global Safety in Mixture-of-Experts through Shared Expert ALignment (SEAL) (2026-09)
- **简介**：针对 MoE 安全对齐局部化的问题（即 GateBreaker 揭示的少数专家承担全部安全职责）， 提出通过共享专家对齐来强化全局安全性。思路是不再把 safety 押在个别专家上， 而是让承担安全职责的能力在专家间共享，从而抬高针对性绕过的成本。 这是本仓库防御章节中直接回应 MoE 路由攻击的工作， 建议与第 2.3 节的三篇攻击工作对照阅读。
- **信任边界**：模型内部
- **arXiv**：[2609.02293](https://arxiv.org/abs/2609.02293)

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
