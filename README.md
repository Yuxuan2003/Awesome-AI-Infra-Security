# Awesome-AI-Infra-Security

**[English](README.md)** ｜ [中文](README.zh.md)

> A curated list of AI infrastructure security papers — attack surfaces, trust boundaries and defenses across the LLM inference & training stack, with an English summary for each entry.

![Last Update](https://img.shields.io/badge/last%20update-2026.09-brightgreen) ![Papers](https://img.shields.io/badge/papers-60%2B-blue) ![Time Range](https://img.shields.io/badge/time-2025.01--2026.09-orange) [![Link Check](https://github.com/Yuxuan2003/Awesome-AI-Infra-Security/actions/workflows/check.yml/badge.svg)](https://github.com/Yuxuan2003/Awesome-AI-Infra-Security/actions/workflows/check.yml) ![Awesome](https://img.shields.io/badge/-awesome-ff69b4)

## Why this list

What makes AI infrastructure distinctive: **the semantics of user input directly determines the underlying compute topology, cache state, GPU memory footprint, scheduling behavior and network traffic.**

In a conventional web/cloud stack, request content is largely decoupled from low-level resource state. In LLM infra, a single prompt simultaneously shapes KV allocation, prefix-cache hits, batch composition, preemption, MoE expert routing and inter-GPU communication — **input controls not only the model's output but the state of the infrastructure itself.** An attacker can therefore manipulate the system through perfectly legitimate API requests.

This produces a class of problems that conventional system-security taxonomies struggle to place:

- Performance optimizations become privacy side channels (KV prefix sharing → cross-tenant prompt inference)
- Model semantics determine physical execution paths (MoE routing → GPU/NIC load → observable side channels)
- Attack targets shift from compute to state machines (a few requests manipulate the scheduler instead of saturating GPUs)
- Deployment optimizations quietly change model safety (perplexity unchanged after quantization, but refusals collapse)
- Local corruption amplifies into global pollution (one rank's faulty tensor propagates through collectives into the checkpoint)

## What this list covers

Only work whose **primary object of study is the LLM inference / training infrastructure itself**, organized along two axes: *attack surface × trust boundary*.

**Not covered** (the three boundaries that fail most often):

1. **AI-for-Security** — e.g. using an MoE for malware classification, penetration testing, vulnerability discovery. This list is Security-of-AI only.
2. **Pure model-layer work** — the paper must engage the state, resources or topology of a serving/training system. Alignment work that only touches weights and outputs does not qualify.
3. **Generic jailbreaks re-run in a new deployment setting** — the attack or defense must act on the infrastructure itself.

## Why organize by attack surface × trust boundary, not topic tags

Existing large LLM-safety lists tag entries by submission topic (jailbreak / privacy / watermark …). Infra-layer work ends up scattered: a KV-cache side channel and a network-traffic fingerprint share the same side-channel section even though the attacker's capability, the defense location and the affected system components are entirely different.

This list takes the **attack surface** (where in the system stack: KV / scheduler / routing / interconnect / training collectives) as the primary axis, and the **trust boundary** (cross-tenant / cross-request / host-device / inter-node / supply-chain / model-internal) as a cross-cutting tag.

The reason: the same attack surface has very different severity at different trust boundaries. KV leakage is nearly harmless in single-tenant self-hosting but a serious privacy incident in multi-tenant serving. Only by labelling both dimensions can a reader tell whether a paper is relevant to their own deployment.

### Attack surface × trust boundary distribution

| Attack surface \ Trust boundary | Cross-tenant | Cross-request | Host–device | Inter-node | Supply chain | Model-internal |
|---|---|---|---|---|---|---|
| **0 Threat Models & Surveys** | · | · | 1 | · | · | 1 |
| **1 AI State Plane Security** | 23 | 7 | 6 | 5 | 2 | 2 |
| **2 Semantic-to-Resource Attack Surface** | 5 | · | 1 | 1 | · | 3 |
| **3 Infra Optimization Induces Safety Drift** | 1 | · | · | · | 2 | 8 |
| **4 Training-Side Integrity** | · | · | · | 2 | 1 | · |
| **5 Hardware & Execution Environment** | · | · | 3 | · | 1 | · |
| **6 Defenses & System Mechanisms** | 2 | 1 | 4 | 1 | 1 | 3 |

## Contents

- [0 Threat Models & Surveys](#0-threat-models-surveys)
- [1 AI State Plane Security](#1-ai-state-plane-security)
  - [1.1 KV / Prefix Cache Side Channels & Leakage](#11-kv-prefix-cache-side-channels-leakage)
  - [1.2 Activation / Embedding State Leakage](#12-activation-embedding-state-leakage)
  - [1.3 Disaggregated Inference & Cross-Node KV Transfer](#13-disaggregated-inference-cross-node-kv-transfer)
  - [1.4 Cache Coherence & Semantic Cache](#14-cache-coherence-semantic-cache)
- [2 Semantic-to-Resource Attack Surface](#2-semantic-to-resource-attack-surface)
  - [2.1 Scheduler Manipulation & Latency DoS](#21-scheduler-manipulation-latency-dos)
  - [2.2 MoE Routing Side Channels](#22-moe-routing-side-channels)
  - [2.3 MoE Routing Manipulation & Safety Degradation](#23-moe-routing-manipulation-safety-degradation)
  - [2.4 Expert-Parallel Communication & Load Hijacking](#24-expert-parallel-communication-load-hijacking)
- [3 Infra Optimization Induces Safety Drift](#3-infra-optimization-induces-safety-drift)
- [4 Training-Side Integrity](#4-training-side-integrity)
- [5 Hardware & Execution Environment](#5-hardware-execution-environment)
- [6 Defenses & System Mechanisms](#6-defenses-system-mechanisms)
- [7 Engineering-Side Security (non-arXiv)](#7-engineering-side-security-non-arxiv)

Browse by trust boundary: [Cross-tenant](views/by-boundary/cross-tenant.md) ｜ [Cross-request](views/by-boundary/cross-request.md) ｜ [Host–device](views/by-boundary/host-device.md) ｜ [Inter-node](views/by-boundary/inter-node.md) ｜ [Supply chain](views/by-boundary/supply-chain.md) ｜ [Model-internal](views/by-boundary/model-internal.md)

---

## 0 Threat Models & Surveys

*Field surveys, SoK, and attack-surface × trust-boundary frameworks. This section answers what fundamentally distinguishes AI-infra security boundaries from conventional web/cloud.*

#### Can Transformer Memory Be Corrupted? Investigating Cache-Side Vulnerabilities in Large Language Models (MTI) (2025-10)
- **Summary**: Treats the inference-time KV cache as an overlooked integrity attack surface even when prompts and weights are secured. The MTI framework perturbs cached key vectors via noise, zeroing, and rotations; on GPT-2 and LLaMA-2-7B it shifts next-token distributions and destabilizes RAG/agent pipelines.
- **Trust boundary**: Host–device, Model-internal
- **arXiv**: [2510.17098](https://arxiv.org/abs/2510.17098)

## 1 AI State Plane Security

*Conventional systems have only a Control Plane and a Data Plane; LLM serving adds an AI State Plane — KV, activations, embeddings, expert routing, adapter and speculative state flowing between machines. These intermediate states carry user input, yet most infra designs treat them first as performance objects, not tenant security boundaries.*

### 1.1 KV / Prefix Cache Side Channels & Leakage

*Timing channels from prefix reuse, cross-tenant prompt inference, cache-hit probing.*

#### Characterizing Contention-Induced Reliability Collapse in KV-Cache Timing Side Channels for Multi-Tenant LLM Serving (Contention Collapse) (2026-09)
- **Summary**: Prior work shows KV-cache prefix reuse leaks whether a prefix is cached, but not how reliable such attacks stay under realistic multi-tenant contention. Seven experiments on a live vLLM server (DeepSeek-R1-Distill-Llama-8B on NVIDIA GB10) show mean Cohen's d collapsing from 0.7789 with no competing workers to 0.2109 with two (t=8.412), and AUROC falling from 0.650 at ambient to 0.531 near 61% overlap. A 120-run sparse-overlap test places the breakpoint at tau=0 (95% CI [0.000,0.113]), indicating an ambient-versus-loaded regime change rather than a physical threshold; concurrency-depth variance is the strongest correlate of effect size (r=-0.416).
- **Trust boundary**: Cross-tenant
- **arXiv**: [2609.06853](https://arxiv.org/abs/2609.06853)

#### Uncovering and Understanding Hidden Dependencies in the LLM API Reseller Ecosystem via Prefix-Cache Side Channels (Reseller Probing) (2026-08)
- **Summary**: Multi-level LLM API reselling hides the supply chain: requests may traverse undisclosed upstreams. This work uses the prefix-cache side channel as a probe, recovering resellers' hidden upstream dependencies from cache-hit signatures of crafted prompts—useful for compliance and data-flow auditing.
- **Trust boundary**: Cross-tenant, Supply chain
- **arXiv**: [2608.20732](https://arxiv.org/abs/2608.20732)

#### Governing the KV Cache: Preventing Timing Side-Channel Leakage in Multi-Tenant LLM Inference (KV Governance) (2026-08)
- **Summary**: KV-cache prefix reuse is LLM serving's key throughput optimization, but under multi-tenancy cache hits leak via first-token latency. This work characterizes the timing channel in vLLM and SGLang and designs cache-governance defenses keeping most reuse gains while blocking cross-tenant probing.
- **Trust boundary**: Cross-tenant, Cross-request
- **arXiv**: [2608.09225](https://arxiv.org/abs/2608.09225)

#### Efficient and Privacy Aware Edge Cloud Collaborative Inference for Large Language Models (2026-07)
- **Summary**: Cloud LLM inference exposes user prompts, while on-device inference is infeasible for most edge hardware. This framework splits inference on endpoint-authenticated KV cache: endpoints handle embedding, KV cache authentication and speculative drafting, the cloud runs authenticated decoder inference, and all transmitted data is quantized and AES-GCM encrypted with cache access policies kept local. It cuts per-token latency by up to 46.1% and downlink payloads by up to 67.4% over baseline split inference.
- **Trust boundary**: Inter-node
- **arXiv**: [2607.13093](https://arxiv.org/abs/2607.13093)

#### Agent-Assisted Side-Channel Attacks on Non-Prefix KV Cache in RAG (2026-06)
- **Summary**: Existing KV cache side channels require strict prefix alignment and fail on RAG queries with private prefixes. SpliceLeak exploits the deterministic "Step-Wave" timing signature of chunk-aware non-prefix KV cache fusion in vLLM+LMCache, fingerprinting hidden prompt lengths and extracting content token-by-token with up to 100% success, needing as few as 63 requests per token. The SpliceDefense mitigation (QCP + CTBF) flattens the signal (Delta TTFT ~ 0).
- **Trust boundary**: Cross-tenant
- **arXiv**: [2606.21842](https://arxiv.org/abs/2606.21842)

#### OTRO: Oblivious Tokenization Path with Square-Root ORAM (OTRO) (2026-06)
- **Summary**: CPU-side tokenizers in TEE-based LLM serving leak prompts via table-lookup memory access patterns, with end-to-end prompt recovery shown on production Intel TDX. Tree-based ORAM fixes incur ~13x tokenizer slowdown. OTRO uses square-root ORAM with replica pools, epoch-based rotation with dummy-access padding, and KV-cache-aware chunked tokenization, limiting TTFT overhead to at most 4.5% with under 0.5 GB extra memory.
- **Trust boundary**: Cross-tenant, Host–device
- **arXiv**: [2606.17358](https://arxiv.org/abs/2606.17358)

#### CacheProbe: Auditing Prompt Cache Isolation in Gateway APIs (CacheProbe) (2026-05)
- **Summary**: Prompt caching reuses KV cache across requests, but many implementations are vulnerable to timing attacks or metadata disclosure. Building on Gu et al. (ICML 2025), this paper audits whether OpenRouter's API gateway architecture undermines provider-level per-account prompt cache isolation: routing through OpenRouter with shared organizational credentials risks creating global cache sharing across all OpenRouter users.
- **Trust boundary**: Cross-tenant
- **arXiv**: [2605.30613](https://arxiv.org/abs/2605.30613)

#### CachePrune: Privacy-Aware and Fine-Grained KV Cache Sharing for Efficient LLM Inference (CachePrune) (2026-05)
- **Summary**: Unrestricted cross-user KV cache sharing lets adversaries infer user inputs via cache-reuse probing; disabling sharing entirely wastes reuse of privacy-irrelevant segments. CachePrune enables token-level, privacy-aware KV sharing with sensitivity masking, deriving reusable variable-length segments and retrieving them efficiently. Implemented on vLLM over three datasets, it eliminates direct leakage through reuse side channels while reducing TTFT by 4.5x and raising hit rates by 44%.
- **Trust boundary**: Cross-tenant
- **arXiv**: [2605.23640](https://arxiv.org/abs/2605.23640)

#### Continuous Discovery of Vulnerabilities in LLM Serving Systems with Fuzzing (2026-05)
- **Summary**: Serving-layer failures emerge only under concurrent workloads and evade standard model and API tests. GRIEF, a greybox fuzzer for LLM inference engines, treats timed multi-request traces as first-class inputs and uses controlled replay with log-probability checks to confirm reproducible failures. Early campaigns on vLLM and SGLang found 15 vulnerabilities (10 developer-confirmed, 2 CVEs), spanning KV-cache isolation failures, cross-request interference, and silent output corruption.
- **Trust boundary**: Cross-tenant, Cross-request
- **arXiv**: [2605.11202](https://arxiv.org/abs/2605.11202)

#### Bit-Flip Vulnerability of Shared KV-Cache Blocks in LLM Serving Systems (2026-04)
- **Summary**: Shared prefix-caching blocks in vLLM exist as a single physical copy without integrity protection, a Rowhammer-analogous target. Software fault injection shows: 13 of 16 BF16 bit positions yield silent divergence (coherent but altered outputs); only requests sharing the prefix are affected; damage accumulates linearly with no temporal decay. A scheduling-time checksum bounds cumulative damage to one batch with negligible overhead.
- **Trust boundary**: Cross-tenant, Cross-request
- **arXiv**: [2604.17249](https://arxiv.org/abs/2604.17249)

#### PrefixWall: Mitigating Prefix Caching Side Channels in Shared LLM Systems (PrefixWall) (2026-03)
- **Summary**: Automatic Prefix Caching (APC) creates timing side channels: hit/miss latency differences let multi-tenant attackers incrementally reconstruct another user's request. Existing defenses disable APC entirely. PrefixWall instead monitors cross-user cache reuse, flags suspicious sharing, and selectively isolates prefixes only when necessary, enabling up to 70% higher cache reuse and 30% lower inference latency than isolation-based defenses.
- **Trust boundary**: Cross-tenant
- **arXiv**: [2603.10726](https://arxiv.org/abs/2603.10726)

#### CacheTrap: Unveiling a Stealthier Gray-Box Trojan against LLMs (CacheTrap) (2025-11)
- **Summary**: CacheTrap is the first gray-box Trojan targeting the LLM KV cache: a single-bit flip in the KV cache acts as a transient trigger that induces targeted behaviors without changing inputs or model weights. An efficient search locates vulnerable cache positions independent of weights or datasets. On five open-source LLMs it reaches 100% attack success rate with the trigger while preserving benign accuracy, by flipping just one bit.
- **Trust boundary**: Model-internal
- **arXiv**: [2511.22681](https://arxiv.org/abs/2511.22681)

#### Shadow in the Cache: Unveiling and Mitigating Privacy Risks of KV-cache in LLM Inference (2025-08)
- **Summary**: This first comprehensive analysis of KV-cache privacy risks shows attackers can reconstruct sensitive user inputs directly from the KV cache via three vectors: a direct Inversion Attack, a broader Collision Attack, and a semantic Injection Attack. The KV-Cloak defense combines reversible matrix-based obfuscation with operator fusion, reducing reconstruction quality to random noise with virtually no accuracy loss and minimal performance overhead.
- **Trust boundary**: Cross-tenant
- **arXiv**: [2508.09442](https://arxiv.org/abs/2508.09442)

#### CachePrune: Teaching LLMs What Not to Follow via KV-Cache Editing (2025-04)
- **Summary**: LLMs cannot distinguish data from instructions in prompt context, enabling indirect prompt injection. CachePrune prunes instruction-following neurons during KV cache encoding of the context, steering the model to treat context purely as data. Neurons are identified via preferential attribution loss theoretically tied to a DPO upper bound. The defense runs at cache encoding time with zero test-time overhead, significantly reducing attack success rate while preserving instruction-following.
- **Trust boundary**: Model-internal
- **arXiv**: [2504.21228](https://arxiv.org/abs/2504.21228)

#### I Know What You Asked: Prompt Leakage via KV-Cache Sharing in Multi-Tenant LLM Serving (PromptPeek) (2025-02)
- **Summary**: A foundational KV prefix-sharing attack (SUSTech & ByteDance): PromptPeek measures first-token latency on candidate prefixes in multi-tenant serving to reconstruct other users' prompts. It directly drove vLLM's cache_salt defense, which injects tenant identity into the first cache block's hash.
- **Trust boundary**: Cross-tenant · **Venue**: NDSS 2025
- **Link**: https://www.ndss-symposium.org/ndss-paper/i-know-what-you-asked-prompt-leakage-via-kv-cache-sharing-in-multi-tenant-llm-serving/

### 1.2 Activation / Embedding State Leakage

*Recovering original input from intermediate activations, sparsity patterns and hidden states.*

#### Detokenization Leaks: Reconstructing Local LLM Outputs From Cache Traces (Detokenization Leaks) (2026-09)
- **Summary**: Reconstructs text generated by locally hosted LLMs by observing CPU cache activity during detokenization. Unlike prior attacks requiring shared data memory, CPU offloading or MoE architectures, it targets the detokenizer present in default inference pipelines: Flush+Reload on shared tokenizer code detects when decoding occurs, enabling well-timed Prime+Probe to isolate token-dependent cache activity, then a clustering plus language-model pipeline recovers text. Evaluated across multiple datasets, hardware platforms, inference frameworks and model families, it recovers semantically accurate outputs from real local deployments including agentic systems.
- **Trust boundary**: Cross-tenant, Host–device
- **arXiv**: [2609.06674](https://arxiv.org/abs/2609.06674)

#### SparSEEty: Extracting Tokens from Sparsity-Exploiting LLM Serving Systems via Deterministic Side Channels (SparSEEty) (2026-08)
- **Summary**: Serving systems exploit LLM activation sparsity for optimization, but this externalizes internal activation patterns as a deterministic side channel: sparse patterns correlate strongly with input tokens, so attackers can recover processed tokens—an activation-layer analog of KV-cache side channels.
- **Trust boundary**: Cross-tenant, Host–device
- **arXiv**: [2608.02995](https://arxiv.org/abs/2608.02995)

#### MOSAIC: Masked Outsourcing of Secure AI Computations (MOSAIC) (2026-07)
- **Summary**: Masking protocol for outsourcing transformer inference to untrusted accelerators while hiding both input and model. Small result noise (security from LWE/LPN) gives optimal client overhead and Hadamard rotations bound cross-layer error; on 70B models perplexity matches BF16 on HumanEval.
- **Trust boundary**: Inter-node, Host–device
- **arXiv**: [2607.29221](https://arxiv.org/abs/2607.29221)

#### (A)iSpy: Parasitic Trojans for Machine Learning Infrastructure ((A)iSpy) (2026-07)
- **Summary**: Parasitic Trojan inside ML runtimes (implemented in ONNX Runtime) that observes live tensor states during training and inference. It exfiltrates hyperparameters via model weights or logits and amplifies weak data poisoning into backdoors, raising attack success from near zero to 100%.
- **Trust boundary**: Supply chain
- **arXiv**: [2607.17550](https://arxiv.org/abs/2607.17550)

#### Image Prompt Reconstruction Attacks on Distributed MLLM Inference Frameworks (2026-06)
- **Summary**: First image-prompt reconstruction attacks on distributed MLLM inference, where intermediate embeddings shared among participants leak visual inputs. A 100%-accurate extraction step enables pixel-level (MPAA) and diffusion-guided (IEDA) reconstruction on Gemma 3, Phi 4, Qwen 2.5 VL and Llama 4.
- **Trust boundary**: Inter-node, Cross-tenant
- **arXiv**: [2606.18710](https://arxiv.org/abs/2606.18710)

#### Bifrost: Hybrid TEE-FHE Inference for Privacy-Preserving Transformer and LLM Serving (Bifrost) (2026-06)
- **Summary**: Hybrid TEE-FHE serving: secrets stay in an attested CPU TEE, linear layers run as CKKS ciphertext on untrusted accelerators, and KV-state transitions never leave the TEE. Bifrost+ builds prompt-side KV in the TEE, cutting projected latency 9.25-9.91x and TTFT by 14.6-53.4x versus direct FHE.
- **Trust boundary**: Host–device, Cross-tenant
- **arXiv**: [2606.17421](https://arxiv.org/abs/2606.17421)

#### The Vision Encoder as a Privacy Boundary: Visual-Token Side Channels in Encoder-Free Vision-Language Models (2026-06)
- **Summary**: Encoder-free VLMs route image patches directly into the LLM token stream, turning intermediate visual tokens into a pre-output side channel. Decoders invert visual-token streams from Gemma4 and Fuyu, recovering recognizable image structure and readable held-out access codes; Gemma4 layer-0 KV cache tensors are directly invertible, placing the channel inside KV caches persisted by production serving stacks. The attack resists additive noise and quantization.
- **Trust boundary**: Cross-tenant
- **arXiv**: [2606.14783](https://arxiv.org/abs/2606.14783)

#### Defense Against Prompt Inversion Attacks: An Information-Theoretic Approach for LLM Collaborative Inference (2026-06)
- **Summary**: Information-theoretic defense against prompt inversion in edge-cloud collaborative inference, where transmitted intermediate activations leak user prompts. Information-bottleneck privacy adapters minimize activation-input mutual information, cutting attack success by up to 35% over prior defenses.
- **Trust boundary**: Inter-node
- **arXiv**: [2606.11592](https://arxiv.org/abs/2606.11592)

#### Good-Enough LLM Obfuscation (GELO) (GELO) (2026-03)
- **Summary**: On shared accelerators, an adversary reading device memory can observe KV caches and hidden states; MPC/FHE are 1-2 orders of magnitude too slow. GELO hides hidden states with fresh per-batch invertible mixing (U = AH offloaded, A^{-1} applied on return), leaving the attacker a single-batch blind source separation problem. On Llama-2 7B it preserves float32 outputs exactly with ~20-30% compute overhead, and a 60M-parameter transformer unmixing attack fails.
- **Trust boundary**: Host–device
- **arXiv**: [2603.05035](https://arxiv.org/abs/2603.05035)

#### Attacks on Approximate Caches in Text-to-Image Diffusion Models (2025-08)
- **Summary**: Security assessment of approximate caching in text-to-image diffusion serving, which reuses intermediate states across similar prompts and breaks user isolation. Shows a remote covert channel lasting days, prompt stealing from cache hits, and poisoning rendering attacker logos on later hits.
- **Trust boundary**: Cross-tenant, Cross-request
- **arXiv**: [2508.20424](https://arxiv.org/abs/2508.20424)

#### I Know What You Said: Unveiling Hardware Cache Side-Channels in Local Large Language Model Inference (2025-05)
- **Summary**: Hardware cache side-channels on local LLM inference leak token values via embedding-lookup access patterns and token positions via decoding timing. An unprivileged eavesdropper reconstructs input/output text on Llama, Falcon and Gemma with average edit distance of 17.3% (input) and 5.2% (output).
- **Trust boundary**: Cross-tenant
- **arXiv**: [2505.06738](https://arxiv.org/abs/2505.06738)

#### Spill The Beans: Exploiting CPU Cache Side-Channels to Leak Tokens from Large Language Models (Spill The Beans) (2025-05)
- **Summary**: Flush+reload attack co-located with a victim LLM that watches shared CPU caches for embedding-vector accesses and maps cache hits back to generated tokens. Balancing monitored vocabulary against eviction, one shot recovers 80-90% of a high-entropy API key and about 40% of English text.
- **Trust boundary**: Cross-tenant
- **arXiv**: [2505.00817](https://arxiv.org/abs/2505.00817)

### 1.3 Disaggregated Inference & Cross-Node KV Transfer

*Prefill/decode disaggregation, RDMA KV transfer, KV tenant/request binding, stale KV, replay, misrouting, cross-tenant KV injection.*

#### Denial of Deadline: Network-Driven Accuracy Collapse in Distributed Inference Pipelines (Denial of Deadline) (2026-07)
- **Summary**: Distributed inference pipelines rely on timely inter-node delivery. Without compromising any compute node, targeted network delay makes the pipeline miss deadlines and forces degraded paths, collapsing accuracy—the target is correctness of results while every component looks healthy in isolation.
- **Trust boundary**: Inter-node
- **arXiv**: [2607.24692](https://arxiv.org/abs/2607.24692)

### 1.4 Cache Coherence & Semantic Cache

*Prefix-cache hash collisions, image-cache collisions, semantic-cache inconsistency.*

#### HijackKV: New Threat in Position-Independent KV Cache Reuse (HijackKV) (2026-07)
- **Summary**: Position-independent KV reuse decouples KV blocks from their original positions to raise hit rates. This paper shows it opens a new attack surface: reused KV segments can carry different semantics in new contexts, tampering with the model's internal context while the surface prompt stays benign.
- **Trust boundary**: Cross-request, Cross-tenant
- **arXiv**: [2607.19957](https://arxiv.org/abs/2607.19957)

#### Grounded Cache Routing for Retrieval-Augmented Generation: When Is It Safe to Reuse an Answer? (2026-05)
- **Summary**: Output-level semantic answer caches in RAG are fragile: evidence drifts and adversarial collision attacks hijack cached responses. GroundedCache admits a cached answer only when 4 gates hold (query similarity, evidence overlap, source-version validity, lexical support). With the unsafe-served rate (USR) metric on 12,000 generations (Qwen2.5-7B on vLLM), it drives USR to 0.0% on HotpotQA (vs. 15-35% naive) and 1.5% on mtRAG drift (vs. 51.5%), at 1.04-1.07x p50 latency.
- **Trust boundary**: Cross-tenant, Cross-request
- **arXiv**: [2605.27494](https://arxiv.org/abs/2605.27494)

#### Cache Me, Catch You: Cache Related Security Threats in LLM Serving Frameworks (Cache Me Catch You) (2026-02)
- **Summary**: A systematic audit of cache security in LLM serving frameworks, covering prefix, semantic, and image caches. It uncovers prefix-cache hash collisions, image-cache collisions, and semantic inconsistency, landed as real vulnerabilities including CVE-2025-25183 and CVE-2025-46722.
- **Trust boundary**: Cross-tenant, Cross-request · **Venue**: NDSS 2026
- **Link**: https://github.com/XingTuLab/Cache_Me_Catch_You
- **Code**: https://github.com/XingTuLab/Cache_Me_Catch_You

## 2 Semantic-to-Resource Attack Surface

*The most fundamental property of AI infra: the semantics of user input directly determines compute topology, cache state, GPU memory, scheduling and network traffic. A single prompt shapes KV allocation, prefix hits, batch composition, preemption, MoE routing and inter-GPU traffic — input controls not only model output but infrastructure state. Attackers can therefore manipulate the system through perfectly legitimate API requests.*

### 2.1 Scheduler Manipulation & Latency DoS

*Attacking the serving state machine, not GPU FLOPS — a few crafted requests manipulate output length, KV occupancy and batch lifetime to trigger repeated preemption and recomputation.*

#### Bit-Exact AI Inference Verification Without Performance Tradeoffs (BitExactVerify) (2026-05)
- **Summary**: Counters covert adversaries abusing serving freedom—steganography, unreported software changes, or computation hidden in vLLM batch elements. Engines are deterministic but non-invariant, enabling bit-exact re-computation via software-only GPU emulation, making rounding errors an auditable signature.
- **Trust boundary**: Cross-tenant
- **arXiv**: [2606.00279](https://arxiv.org/abs/2606.00279)

#### Rethinking Latency Denial-of-Service: Attacking the LLM Serving Framework, Not the Model (Fill and Squeeze) (2026-02)
- **Summary**: Rather than flooding GPU FLOPS, this attack targets the serving framework's state machine: Fill occupies the global KV cache with crafted requests, Squeeze forces repeated preemption and recomputation. Victim TTFT degrades tens to hundreds of times using only a few perfectly legal API calls.
- **Trust boundary**: Cross-tenant
- **arXiv**: [2602.07878](https://arxiv.org/abs/2602.07878)

#### RepetitionCurse: Measuring and Understanding Router Imbalance in Mixture-of-Experts LLMs under DoS Stress (RepetitionCurse) (2025-12)
- **Summary**: Shows OOD prompts can hijack MoE routing under expert parallelism, concentrating all tokens on the same top-k experts so some devices overload while others idle. Black-box RepetitionCurse uses repetitive token patterns, inflating latency 3.063x on Mixtral-8x7B and violating TTFT SLOs.
- **Trust boundary**: Cross-tenant
- **arXiv**: [2512.23995](https://arxiv.org/abs/2512.23995)

### 2.2 MoE Routing Side Channels

*Inferring expert activation via cache/TLB/performance counters/latency/network, and from it the input semantics.*

#### MoEcho: Exploiting Side-Channel Attacks to Compromise User Privacy in Mixture-of-Experts LLMs (MoEcho) (2025-08)
- **Summary**: A representative MoE side-channel work: MoE makes semantics determine physical execution paths, so prompts activate different expert sets. Cache, TLB, and performance-counter channels on CPU/GPU reveal expert activation patterns and prompt/response content. CCS 2025, pp. 2159–2173.
- **Trust boundary**: Cross-tenant, Host–device · **Venue**: CCS 2025
- **arXiv**: [2508.15036](https://arxiv.org/abs/2508.15036)

### 2.3 MoE Routing Manipulation & Safety Degradation

*Safety behavior is concentrated in a few experts; manipulating routing strengthens jailbreaks. Entries here must act on the routing mechanism itself, not re-run a generic jailbreak on an MoE model.*

#### Misrouter: Exploiting Routing Mechanisms for Input-Only Attacks on Mixture-of-Experts LLMs (Misrouter) (2026-05)
- **Summary**: Misrouter manipulates MoE routing through inputs alone—no weight changes or internal access. Crafted inputs alter the router's expert selection so inference bypasses safety experts. This API-only threat model fits real deployments and shows routing itself is an attack surface.
- **Trust boundary**: Model-internal
- **arXiv**: [2605.04446](https://arxiv.org/abs/2605.04446)

#### RouteHijack: Routing-Aware Attack on Mixture-of-Experts LLMs (RouteHijack) (2026-05)
- **Summary**: A routing-aware attack on MoE LLMs, complementing GateBreaker and Misrouter in establishing routing as MoE's weak point. The three differ in threat-model strength: neuron-level intervention, input-only manipulation, and—here—modeling and exploiting routing behavior.
- **Trust boundary**: Model-internal
- **arXiv**: [2605.02946](https://arxiv.org/abs/2605.02946)

#### GateBreaker: Gate-Guided Attacks on Mixture-of-Expert LLMs (GateBreaker) (2025-12)
- **Summary**: MoE models have "safety experts" over-routed on harmful inputs, and refusal depends heavily on them. Disabling only ~3% of neurons via a gate-guided attack raises attack success from 7.4% to 64.9%, showing MoE safety alignment is localized and fragile. USENIX Security 2026.
- **Trust boundary**: Model-internal · **Venue**: USENIX Security 2026
- **arXiv**: [2512.21008](https://arxiv.org/abs/2512.21008)

### 2.4 Expert-Parallel Communication & Load Hijacking

*EP all-to-all hotspots, straggler induction, cross-tenant latency interference.*

#### Trigger the Straggler: Load Hijack on Mixture-of-Experts LLMs (Trigger the Straggler) (2026-08)
- **Summary**: In expert-parallel MoE, the router decides both which experts activate and which GPUs carry the load. Crafted inputs steer load onto a few devices, creating artificial stragglers that degrade co-tenant latency—a legal prompt amplified via routing into physical resource skew.
- **Trust boundary**: Inter-node, Cross-tenant
- **arXiv**: [2608.10614](https://arxiv.org/abs/2608.10614)

## 3 Infra Optimization Induces Safety Drift

*Conventional infra optimization is a performance/accuracy tradeoff: maximize throughput subject to accuracy >= X. But for aligned models, quantization and cache compression can significantly degrade refusal behavior with almost unchanged perplexity — utility holds while safety drops. This section asks whether Model Safety should be an invariant of infra optimization: subject to utility >= X AND safety >= Y.*

#### Quantization-Triggered Backdoors in Language Models: Cross-Quantizer Transferability and the Validation--Deployment Gap (Quant Backdoor) (2026-08)
- **Summary**: Quantization-triggered backdoors: models behave normally at full precision and turn malicious only after quantized deployment. The backdoor transfers across quantizers, so routine deployment becomes the trigger—auditing full-precision weights alone cannot guarantee post-deployment safety.
- **Trust boundary**: Supply chain, Model-internal
- **arXiv**: [2608.27512](https://arxiv.org/abs/2608.27512)

#### Preserving Fairness and Safety in Quantized LLMs Through Critical Weight Protection (Critical Weight Protection) (2026-07)
- **Summary**: Counters fairness and safety degradation from quantization by protecting critical weights, treating both as explicit protection targets rather than only perplexity—pushing infra optimization from "accuracy >= X" to "utility >= X AND safety >= Y". Findings of ACL 2026, pp. 19831–19855.
- **Trust boundary**: Model-internal · **Venue**: Findings of ACL 2026
- **Link**: https://aclanthology.org/2026.findings-acl.993/

#### When Efficiency Meets Safety: A Benchmark Security Analysis of KV Cache Compression in Large Language Models (Safe-CAM) (2026-07)
- **Summary**: A benchmark study of KV-cache compression versus jailbreak safety: different compression methods affect safety inconsistently—some weaken, some strengthen—refuting the intuition that compression necessarily harms safety. Safe-CAM is proposed as mitigation. ACL 2026 Long Paper, pp. 24472–24485.
- **Trust boundary**: Model-internal · **Venue**: ACL 2026
- **Link**: https://aclanthology.org/2026.acl-long.1123/

#### Speculative Decoding at Temperature Zero: A Scoped Safety-Invariance Screen with a 48,072-Sample Expansion (TAIS) (2026-06)
- **Summary**: Screens whether temperature-zero speculative decoding leaks draft-side behavior into safety outputs. Over 16,783 confirmatory plus 44,066 expansion samples (bf16, DPO-adversarial, GPTQ-4bit drafts), TAIS requires TOST equivalence at +/-3pp: refusal Cohen's h peaks at 0.024, 25/27 contrasts pass.
- **Trust boundary**: Model-internal
- **arXiv**: [2606.25097](https://arxiv.org/abs/2606.25097)

#### AnchorKV: Safety-Aware KV Cache Compression via Soft Penalty with a Refusal Anchor (AnchorKV) (2026-06)
- **Summary**: Finds accuracy-preserving KV cache compression still breaks jailbreak defense and refusal alignment under aggressive eviction. AnchorKV builds an offline refusal anchor via difference-of-means in key-projection space and softly penalizes retention scores, restoring safety at small utility cost.
- **Trust boundary**: Model-internal
- **arXiv**: [2606.17872](https://arxiv.org/abs/2606.17872)

#### Alignment Collapse Under KV Cache Quantization: Diagnosis and Mitigation (Alignment Collapse) (2026-06)
- **Summary**: Direct evidence that infra optimization silently changes model safety: KV-cache quantization breaks refusal and alignment behavior while perplexity stays nearly unchanged—traditional metrics report all normal. The authors diagnose the drift's source and propose mitigations.
- **Trust boundary**: Model-internal
- **arXiv**: [2606.09864](https://arxiv.org/abs/2606.09864)

#### Quantamination: Dynamic Quantization Leaks Your Data Across the Batch (Quantamination) (2026-04)
- **Summary**: Reveals dynamic quantization opens a cross-tenant side channel in serving: an adversary co-batched with victims can recover their data via shared runtime quantization parameters. At least 4 popular ML frameworks leak across the batch boundary, enabling partial to full input recovery.
- **Trust boundary**: Cross-tenant
- **arXiv**: [2604.26505](https://arxiv.org/abs/2604.26505)

#### Enhancing Trustworthiness with Mixed Precision: Benchmarks, Opportunities, and Challenges (QuantTrust) (2025-11)
- **Summary**: Measures how weight/activation/KV quantization shifts four trustworthiness metrics—robustness, fairness, ethics, OOD—that perplexity-focused frameworks omit. Trustworthiness varies unstably across ratios and methods; precision-ensemble voting over mixed-precision variants lifts it by up to 5.8%.
- **Trust boundary**: Model-internal
- **arXiv**: [2511.22483](https://arxiv.org/abs/2511.22483)

#### Fewer Weights, More Problems: A Practical Attack on LLM Pruning (FewerWeights) (2025-10)
- **Summary**: First practical attack on deployment-time pruning: a shipped model looks benign but turns malicious once pruned, hiding payloads in pruning-surviving parameters masked by pruned-away ones. Under vLLM Magnitude/Wanda/SparseGPT: up to 95.7% jailbreak, 98.7% benign-refusal, 99.5% content injection.
- **Trust boundary**: Model-internal, Supply chain
- **arXiv**: [2510.07985](https://arxiv.org/abs/2510.07985)

## 4 Training-Side Integrity

*Distributed training has a special security property: local corruption can become global model corruption — a single rank's faulty tensor propagates through collectives into the checkpoint. Most work here is still framed as reliability (SDC detection); pushing it toward security (malicious instead of accidentally-faulty workers) is largely open.*

#### TrainSDC: Characterizing and Mitigating Silent Data Corruption in Large Language Model Training (TrainSDC) (2026-08)
- **Summary**: Characterizes and mitigates silent data corruption in LLM training, complementing AEGIS's online detection with a focus on how SDCs manifest and propagate—together giving a full picture of how local corruption becomes global model damage, and a basis for moving from reliability to security.
- **Trust boundary**: Inter-node
- **arXiv**: [2608.30769](https://arxiv.org/abs/2608.30769)

#### Safeguarding LLM Training at Scale: Online SDC Detection and Insights from 35 Million GPU Hours (AEGIS) (2026-07)
- **Summary**: Tsinghua and ByteDance's online SDC detection study over 35 million GPU-hours of production data—the largest to date. AEGIS found 18 real SDCs and 13 faulty GPUs at 0.86% overhead, confirming one rank's error can propagate via collectives into global model contamination. OSDI 2026.
- **Trust boundary**: Inter-node, Supply chain · **Venue**: OSDI 2026
- **Link**: https://www.usenix.org/conference/osdi26/presentation/lei

## 5 Hardware & Execution Environment

*GPU microarchitectural side channels, optical/physical probing, TEE and confidential computing, remote attestation.*

#### JITterFlip: Uncovering Fault Attack Surfaces in JIT-Compiled LLM Serving (JITterFlip) (2026-08)
- **Summary**: JIT-compiled kernels in modern serving frameworks are an unaudited fault-attack surface: JIT artifacts reside in memory exposed to fault injection, and targeted bit flips alter kernel behavior without triggering integrity checks—connecting classic hardware fault attacks with dynamic compilation.
- **Trust boundary**: Host–device
- **arXiv**: [2608.29745](https://arxiv.org/abs/2608.29745)

#### LLMscope: Extracting LLM Assets from Edge AI Chips via Optical Probing (LLMscope) (2026-08)
- **Summary**: Extracts LLM assets from edge AI chips via optical probing, bringing physical-layer attacks to LLM deployment. The threat model assumes physical device access—realistic for edge scenarios—extending hardware-side threats from microarchitectural side channels to physical probing.
- **Trust boundary**: Host–device, Supply chain
- **arXiv**: [2608.25321](https://arxiv.org/abs/2608.25321)

#### CloakLM: Obfuscating GPU Memory Layout to Mitigate Model Ex-filtration for Serving (CloakLM) (2026-06)
- **Summary**: On third-party/shared accelerators, weights sit in large contiguous memory regions, so PCIe snooping or HBM dumps can reconstruct models. CloakLM removes this regularity via PCIe traffic shaping, weight shuffling, and HBM page remapping—software-only, vLLM/PyTorch-integrated, near-native overhead.
- **Trust boundary**: Host–device
- **arXiv**: [2606.18400](https://arxiv.org/abs/2606.18400)

## 6 Defenses & System Mechanisms

*Organized by where the defense sits in the system stack: cache isolation (e.g. cache salt), information-flow tracking, isolated scheduling, deterministic execution, auditing and observability.*

#### SpecGuard: Inference-Time Backdoor Detection For Free (SpecGuard) (2026-09)
- **Summary**: Models fine-tuned, shared or downloaded from third parties may carry hidden backdoors, so runtime monitoring matters for frequently updated deployments—yet existing inference-time detectors either assume a trigger form or need extra model computation. SpecGuard repurposes speculative decoding at zero added model-computation cost: the draft-verify step already exposes a signal, since a triggered target model shifts toward attacker behavior while a clean draft model does not, making the acceptance pattern itself a detector.
- **Trust boundary**: Supply chain, Model-internal
- **arXiv**: [2609.11799](https://arxiv.org/abs/2609.11799)

#### SEAL: Reinforcing Global Safety in Mixture-of-Experts through Shared Expert ALignment (SEAL) (2026-09)
- **Summary**: Responds to the localized MoE safety alignment revealed by GateBreaker: instead of betting safety on a few experts, SEAL shares safety capability across experts through shared expert alignment, raising the cost of targeted bypass. Read alongside the Section 2.3 routing attacks.
- **Trust boundary**: Model-internal
- **arXiv**: [2609.02293](https://arxiv.org/abs/2609.02293)

#### Speculative Probing: LLM Monitoring at Speculative-Decoding Cost (SpecProbe) (2026-08)
- **Summary**: Repurposes the speculative-decoding module already in serving stacks into a context-aware safety classifier: a trained soft prompt reuses the on-GPU KV cache at negligible cost. Across four models, probes beat zero-shot GPT-5.4-mini and match or beat 8B guards (Qwen3Guard-Gen-8B, Llama-Guard-3-8B).
- **Trust boundary**: Model-internal
- **arXiv**: [2608.28099](https://arxiv.org/abs/2608.28099)

#### Here is a GIFT: Enforcing User Data Isolation in LLM Serving via GPU Information Flow Tracking (GIFT) (2026-08)
- **Summary**: Serving frameworks handle sensitive user data on shared infrastructure without strong inter-user isolation. GIFT enforces isolation via GPU-level information flow tracking on vLLM—a system-mechanism defense building enforceable boundaries inside the execution infrastructure, not I/O filters.
- **Trust boundary**: Cross-tenant, Host–device
- **arXiv**: [2608.25431](https://arxiv.org/abs/2608.25431)

#### HadAgent: Harness-Aware Decentralized Agentic AI Serving with Proof-of-Inference Blockchain Consensus (HadAgent) (2026-04)
- **Summary**: Decentralized agentic serving with Proof-of-Inference consensus: nodes earn block rights via deterministic inference, verified by one replayed forward pass. Merkle-rooted lanes and recomputation trust tiers give 100% tamper detection at 0% false positives, isolating malicious nodes in two rounds.
- **Trust boundary**: Inter-node
- **arXiv**: [2604.18614](https://arxiv.org/abs/2604.18614)

#### AgenTEE: Confidential LLM Agent Execution on Edge Devices (AgenTEE) (2026-04)
- **Summary**: Runs confidential LLM agent pipelines on edge devices: agent runtime, inference engine, and third-party apps sit in independently attested Arm CCA cVMs linked by verifiable channels. Prompts, weights, and runtime state stay safe from malicious users and compromised OS at under 5.15% overhead.
- **Trust boundary**: Host–device
- **arXiv**: [2604.18231](https://arxiv.org/abs/2604.18231)

#### FlexServe: A Fast and Secure LLM Serving System for Mobile Devices with Flexible Resource Isolation (FlexServe) (2026-03)
- **Summary**: Protects on-device LLM serving from a compromised OS kernel via flexible ARM TrustZone isolation of memory (Flex-Mem) and NPU (Flex-NPU). With LLM-aware memory management and a secure pipeline, it gains 10.05x average TTFT speedup over a strawman and up to 24.30x for agent workflows.
- **Trust boundary**: Host–device
- **arXiv**: [2603.09046](https://arxiv.org/abs/2603.09046)

#### SuperLocalMemory: Privacy-Preserving Multi-Agent Memory with Bayesian Trust Defense Against Memory Poisoning (SuperLocalMemory) (2026-02)
- **Summary**: Local-first multi-agent memory against OWASP ASI06 memory poisoning via architectural isolation and Bayesian trust scoring, with no cloud dependency. Per-agent provenance plus Leiden clustering give 10.6ms median search latency, a trust gap of 0.90, and 72% trust degradation under sleeper attacks.
- **Trust boundary**: Cross-request
- **arXiv**: [2603.02240](https://arxiv.org/abs/2603.02240)

#### Confidential LLM Inference: Performance and Cost Across CPU and GPU TEEs (cLLM-TEE) (2025-09)
- **Summary**: First comprehensive study of end-to-end LLM inference inside CPU and GPU TEEs. Llama2 7B/13B/70B in Intel TDX/SGX with AMX incurs under 10% throughput and 20% latency overhead; H100 Confidential Compute shows 4-8% throughput penalties, yielding 12 cost-security insights.
- **Trust boundary**: Host–device
- **arXiv**: [2509.18886](https://arxiv.org/abs/2509.18886)

#### Selective KV-Cache Sharing to Mitigate Timing Side-Channels in LLM Inference (SafeKV) (2025-08)
- **Summary**: Global KV-cache sharing creates a cross-tenant API timing channel. SafeKV couples privacy enforcement with cache management—three-tier detection, sensitivity-aware radix-tree memory management, RDR-guided leakage bounds—cutting TTFT overhead 40.58% vs full isolation, 2.66x throughput.
- **Trust boundary**: Cross-tenant
- **arXiv**: [2508.08438](https://arxiv.org/abs/2508.08438)

## 7 Engineering-Side Security (non-arXiv)

*CVEs, vendor advisories, framework issues/PRs, fuzzing tools. Real serving-framework vulnerabilities travel via CVE and GitHub advisory, not arXiv — and academic lists rarely collect them. This is where the list most easily differentiates. This section needs a dedicated non-arXiv retrieval flow; do not skip it just because arXiv returns nothing.*

#### vLLM Automatic Prefix Caching: Cache Isolation for Security (cache_salt) (cache_salt) (2025-06)
- **Summary**: vLLM's official defense against prefix-cache timing side channels: a cache_salt parameter is mixed into the first cache block's hash, so tenants with identical prefixes never share cache entries—officially "prevents timing-based attacks" that infer cached content from latency differences.
- **Trust boundary**: Cross-tenant · **Venue**: vLLM 官方文档
- **Link**: https://docs.vllm.ai/en/latest/design/prefix_caching.html

---

## Contributing

You only ever edit `data/papers.yaml`; `README.md`, `README.zh.md` and everything under `views/` are regenerated by GitHub Actions. Scope and entry format: [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md). Maintenance process and retrieval calibration: [docs/MAINTENANCE.md](docs/MAINTENANCE.md).

## Related lists

This list focuses on the security of LLM infrastructure itself. For adjacent areas:

- GUI / computer-use agent security: `Yuxuan2003/Awesome-GUI-Agent-Security`
- Broad LLM safety & privacy (mostly model-layer): `ThuCCSLab/Awesome-LM-SSP`
- LLM inference systems, capability-oriented: `AmadeusChan/Awesome-LLM-System-Papers`
- Model compression & quantization (efficiency-only): `HuangOwen/Awesome-LLM-Compression`

