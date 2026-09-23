# 评分细则 (rubrics)

> 华为杯专用的 5 维内部质量 rubric。Stage 8/9 由 `competitions/huawei/rubric_overlay.json` 特化；它不是官方评分表，也不能预测奖项。

---

## Overlay 协议 (v3.2)

| 层级 | 来源 | 加载 |
|------|------|------|
| 通用基础 | 本文件 stage 0-9 表格 | 华为杯十阶段共享 |
| 华为杯特化 dim 名 | `competitions/huawei/rubric_overlay.json` 的 `dim_whitelist` | score_artifact.py 自动合并 |
| 题型 dim 权重 | `config/dim_weights.json[huawei][<task_type>]` | compute_verdict 加权 mean |
| 样本观察 | `competitions/huawei/empirical.json` | 当前 `n=0`，不得生成数值参照 |

`task_type` 由 stage 1 选题后填入 decision_log; null 时 default 全 1.0 等价老逻辑。

---

## 华为杯内部质量视角

> 当前没有可用于统计校准的可靠标注语料；`competitions/huawei/empirical.json`
> 为 `n=0`。2026 通用论文标准和 AI 规则已核验，题面与赛中更正仍须动态获取；
> 不得从国赛、电工杯或第三方手册类推评分权重。

| 维度 | 关键检查项 |
|------|----------|
| **题意追踪** | 原文锚点 / 限定词 / 单位 / 附件字段 / 交付物完整映射 |
| **模型与实现** | 数学对象契合 / 公平基线 / 代码结果一致 / 失败边界 |
| **证据表达** | Claim IDs / 图表 registry / 结果路径 / 验证可复核 |
| **论文质量** | 摘要反查正文 / 段落职责 / 事实与解释分离 / 引用完整 |
| **提交纪律** | 当届标准文档 / AI 规则 / MD5 锁定 / PDF 上传窗口 |

---

## L1 阶段级 rubric (5 维 × 1-10)

每阶段产出后,Critic 输出以下 JSON:

```json
{
  "stage_id": 0-9,
  "iteration": 0-3,
  "scores": {
    "<dim_key_snake_case>": {"name": "中文名称", "score": 1-10, "evidence": "≤30字"},
    ...
  },
  "min_score": <number>,
  "mean_score": <number>,
  "issues": [
    {"severity": "high|medium|low", "where": "...", "anti_pattern_id": "A1|null", "fix": "..."},
    ...
  ],
  "verdict": "block | pass_early | pass | refine"
}
```

**dim key 命名约定**: 各 stage 的 5 个 `scores` 字段必须用**英文 snake_case**, 与 `feedback_layer1_critic.md §6` 各 stage 列出的固定集合精确一致 (`scripts/score_artifact.py` 加白名单校验)。下面各 stage 表第一列写中文是为了人读, 实际 JSON 输出用英文 key, **中文写在 `name` 子字段**。

退出条件: 见本文件末尾"阈值汇总"节, 与 SKILL.md / feedback_layer1_critic.md / score_artifact.py 三处统一。

---

### Stage 0 — 团队启动

| 维度 | 满分行为 (10) | 失败行为 (1) |
|------|-------------|-------------|
| 1. 角色分工明确性 | 按实际人数覆盖建模/编程/写作责任，并设置互备 | 职责和交接人不明确 |
| 2. 工具就绪度 | 题目需要的计算、写作、版本与沟通工具已验证 | 关键工具尚未试运行 |
| 3. 时间盒规划 | 按实际截止时间设置里程碑、关键路径和缓冲 | 无计划 |
| 4. 题目预扫信号 | 已识别问题域 (优化/预测/评价等) | 未读题 |
| 5. 协作约定 | 命名规范、版本控制、daily standup 时间 | 无规范 |

---

### Stage 1 — 选题

| 维度 | 满分行为 |
|------|---------|
| 1. 备选题对比深度 | 系统比较当年可选题，覆盖难度/数据/契合度/工具/资料与主要风险 |
| 2. 团队优势匹配 | 选题理由含"我们擅长 X,本题需要 X" |
| 3. 风险识别 | 覆盖最可能改变选题结论的风险，并给出预案 |
| 4. 时间可行性 | 已按实际截止时间估算阶段配额、关键路径与缓冲 |
| 5. 决策记录质量 | rationale 与关键 rejected alternatives 均有可核验依据 |

退出条件: 选定题号 + decision_log.json stage 1 节点完整 + 全维 ≥7。

---

### Stage 2 — 问题深度解析

| 维度 | 满分行为 |
|------|---------|
| 1. 子问题分解清晰度 | 每个 sub-problem 的输入/输出/约束明确，且覆盖全部原子要求 |
| 2. 关键变量识别 | 覆盖题面与模型实际使用的变量，区分类型、单位并标注 Requirement ID |
| 3. 数学化程度 | 每个数学对象、目标与硬约束均可回溯到题面锚点或显式假设 |
| 4. 数据契合度 | 题目附件数据已扫描，字段含义/单位与变量映射清楚 |
| 5. 子问题关联性 | 独立复读已完成并消解冲突；依赖或独立理由可追踪，无阻断歧义 |

---

### Stage 3 — 模型选型

| 维度 | 满分行为 |
|------|---------|
| 1. 候选数量与多样性 | 比较足以支撑决策的结构性不同候选；没有合理替代时说明原因 |
| 2. 选型理由 | 每个候选有 (a) 适配理由 (b) 不选的原因 |
| 3. 模型命名真实性 | 名称准确反映实际机制、约束或组合，不用空泛修饰词制造创新感 |
| 4. 求解可行性 | 已确认求解环境存在、时间复杂度可承受；定量图由 MATLAB 生成 |
| 5. 文献支撑 | 关键方法与假设有可靠来源；引用数量由实际使用决定 |

championship 模式额外：red-team 提出最可能推翻模型选择的反例或证据缺口，并给出验证动作。

---

### Stage 4 — Foundation (假设 + 符号 + 术语)

| 维度 | 满分行为 |
|------|---------|
| 1. 假设必要性 | 只保留模型真正依赖的假设；数量由题目与方法决定 |
| 2. 假设支撑 | 每条配 (a) 文献 / (b) 数据观察 / (c) 物理意义 三选一 |
| 3. 符号唯一性 | 同一符号不跨语境换义；需要单位的量均标明单位 |
| 4. 与模型一致性 | stage 5 后回检,无矛盾 |
| 5. 术语规范 | 专业术语首次出现给定义,中英对照 |

---

### Stage 5 — 子问题递归循环 (per Qi)

每个 sub-problem 跑一次 5 维 rubric,**外加** stage-level overall:

#### Per-Qi rubric:

| 维度 | 满分行为 |
|------|---------|
| 1. 模型与问题契合 | 目标函数 / 决策变量 / 约束 与题面一一对应 |
| 2. 数学严谨性 | 推导无跳跃,符号一致,边界条件齐全 |
| 3. 求解正确性 | 代码可运行,结果数量级合理,通过 sanity check |
| 4. 结果证据呈现 | 图表绑定明确论点、源结果与生成脚本，单位/不确定性/最终尺寸可读；不按数量凑图 |
| 5. 现实意义讨论 | 把数值翻译为题目语境中的意义、范围与限制 |

#### Stage-level (跨子问题):

- **复用链**: 题目存在依赖时，上游结果的版本、单位与误差传播是否可追踪；独立子问题不强行建立复用
- **变量一致性**: 不同子问题间变量符号统一

退出条件: 所有 Qi 通过 + 复用链满足 + 全维 ≥7。

---

### Stage 6 — 全局灵敏度 / 稳健性

| 维度 | 满分行为 |
|------|---------|
| 1. 验证设计契合度 | 按核心风险选择 OAT、联合扰动、重采样、数据留出、情景或边界分析，并说明理由 |
| 2. 扰动/验证域合理 | 范围、切分和场景来自数据、测量、物理边界或明确的假设 |
| 3. 输出指标完备 | 报告题目相关的性能、决策变化、可行性和失败样本 |
| 4. 范围定量可复核 | 给出测试域、样本/种子、区间算法、判断标准与证据路径 |
| 5. 失效边界诚实 | 报告观察到的边界；未发现时说明测试域，不虚构临界参数 |

L2 触发: 末尾跨阶段回检 stage 3 的模型选择前提是否被本节结果推翻。

---

### Stage 7 — 模型评价 + 推广

| 维度 | 满分行为 |
|------|---------|
| 1. 优点具体 | 每项都有证据路径、适用范围与不外推声明 |
| 2. 缺点真实 | 每项说明证据、受影响结论、替代方案与验证代价 |
| 3. 改进方向 | 区分 planned/tested/adopted/rejected；未做对照实验时不填写收益 |
| 4. 推广场景 | 说明可复用结构、重新标定、新风险与最低验证；证据不足时不强行推广 |
| 5. 自我批判可信度 | 不写"假设理想化"等套话 (anti_patterns.md 自动检) |

---

### Stage 8 — 论文写作

| 维度 | 满分行为 |
|------|---------|
| 1. 摘要信息闭环 | 每个数字与比较词绑定 Claim ID、正文证据、验证与边界；不机械凑段或字数 |
| 2. 章节完整性 | 题面 Requirement IDs 与证据链所需章节齐全，无空节或失联交付物 |
| 3. 公式 / 图表 / 引用 | 公式可回溯实现，图表有 registry/sidecar，引用已核实且格式合规 |
| 4. 语言质量 | 段落职责明确，区分事实/输出/假设/解释，无空泛创新或未经证据支持的强结论 |
| 5. 视觉一致性 | 字号/配色/字体/单位/精度统一，最终 PDF 尺寸可读，无默认或误导性编码 |

---

### Stage 9 — 终稿审核

5 视角 panel (Layer 3),每个 panelist 独立打分:

| Panelist | 关注 |
|----------|------|
| **数学严谨** | 定理引用、推导、边界条件、单位 |
| **模型贡献** | 设计必要性、基线比较、实质改动证据 |
| **代码正确** | 复现性、注释、变量名、可读性 |
| **写作呈现** | 摘要、章节、图表、引用、配色 |
| **评委视角** | 30 秒内能否看懂核心问题、方法、结果与可信度 |

每位 panelist 输出:
```json
{"panelist": "...", "scores": {"1_dim": {"score": 8, "evidence": "..."}}, "issues": [], "verdict": "ready|refine|block"}
```

聚合器:
- 任一 high-severity issue 保持 `block`，权重不能覆盖
- 找最低分与高影响 issue，定向修补对应阶段一次
- 只让受影响视角复核；时间压力不把已知违规或错误变成 `ready`

---

## 阈值汇总 (与 SKILL.md / feedback_layer1_critic.md / score_artifact.py 统一)

**verdict 优先级 (从高到低)**:

| verdict | 触发条件 | 行为 |
|---------|---------|-----|
| `block` | issues 含 ≥1 high-severity | 暂停 skill, 用户介入 |
| `pass_early` | raw_min ≥ 9 AND weighted_mean ≥ 9 | iter-1 早退, 节省 token |
| `pass` | raw_min ≥ 7 AND weighted_mean ≥ 8 | 进下一阶段 |
| `pass_with_review` *(stage 5)* | 任 Qi mark_for_review 但加权阈值满足 | 进 stage 6, L2 必读 review_qis |
| `refine` | 其他 | section-patch 精修, iter+=1 (cap 3) |
| `refine_partial` *(stage 5)* | 任 Qi.min < 7, 但其他 Qi 已 pass | 仅 refine 标记 Qi, 不动其他 |
| `carryover` | iter == 3 仍 refine 或 refine_partial | 进下一阶段, 标记由 L2 处理 |

`weighted_mean` = Σ(s_i × w_i) / Σ(w_i), 其中 w_i 来自 `config/dim_weights.json` 题型加权 (clamp [0.7, 1.5]); `task_type=default` 全 1.0 等价老逻辑。

**内部质量档位**（用于工作流自检，不对应、也不预测竞赛奖项）：

| 档位 | 单维最低 | 均值 |
|---|---:|---:|
| 强 | ≥8 | ≥9 |
| 可交付 | ≥7 | ≥8 |
| 待复核 | ≥6 | ≥7 |
| 阻塞 | <6 | - |

---

## 与 winning_patterns / anti_patterns / empirical 的对应

本文件 rubric 项 ↔ `competitions/huawei/winning_patterns.md` 段落:
- abstract.* (stage 8 dim 1) → patterns §1, §9 + anti_patterns §A
- paper.section_completeness (stage 8 dim 2) → patterns §2 + anti_patterns §I
- paper.figure_density → patterns §3 + anti_patterns §E
- model.naming (stage 3 dim 3) → patterns §4 + anti_patterns §C1
- subproblems.cross_reference (stage 5 stage-level dim 2) → patterns §5 + anti_patterns §G
- assumptions.support (stage 4 dim 2) → patterns §6 + anti_patterns §B
- sensitivity.multivariate (stage 6 dim 1) → patterns §7 + anti_patterns §F
- evaluation.limitations_real (stage 7 dim 2) → patterns §8 + anti_patterns §H
- evaluation.real_critique → patterns §8

字数、图表数和公式数不作为官方硬阈值。华为杯 `empirical.json` 当前为 `n=0`；Critic 不得输出论文分位、估计区间或获奖概率。
