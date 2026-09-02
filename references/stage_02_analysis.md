---
stage: 2
name: analysis
duration_h: 2-3
inputs:
  - "stage.1.selected"
  - "problem_pdf"
  - "attachment_data_paths"
outputs:
  - "stage.2.{problem_source, requirement_traceability, interpretation_review, ambiguities, decomposition, key_variables, key_constraints, objective_per_subproblem, data_schema, subproblem_dependency}"
  - "state/{problem_spec.md,problem_source_manifest.json,interpretation_review.md}"
loads_reference:
  - "references/problem_understanding_protocol.md"
  - "references/rubrics.md§Stage_2"
loads_template: ["templates/shared/problem_spec.md"]
feedback: ["L1"]
next: stage_03_model_selection
---

# Stage 2 — 问题深度解析与分解

**时长**: 2-3h | **反馈层**: L1

---

## 目标

把题目从**有出处的自然语言要求**转化为可追溯的数学规格：识别交付物、决策变量、目标函数、约束、单位与子问题关系。这一步质量决定后续 5/6/8 阶段的天花板。流畅的题目复述不能替代原文证据。

---

## 输入

- stage 1 输出: 选定题号 + 子问题清单 + 数据路径
- 题目原文 (再读一次)
- 附件数据 (用 pandas/Read 扫一遍 schema)

## 产出

- 子问题分解树 (全部 Qi 的输入/输出/约束/目标)
- 关键变量清单 (覆盖实际模型所需变量并标注决策/状态/参数；不设凑数下限)
- 子问题间关联图 (谁依赖谁的结果)
- 目标函数雏形 (符号级,不必精确)
- 数据 schema 与变量映射
- 题面来源清单、SHA-256 与原子要求追踪矩阵
- 一次独立复读及冲突消解记录

---

## 操作流程

### Step 0: 锁定题面版本与理解协议

读取 `references/problem_understanding_protocol.md`，复制
`templates/shared/problem_spec.md` 为 `<cwd>/state/problem_spec.md`。记录题面与附件路径，计算题面 SHA-256，并写入 `state/problem_source_manifest.json`。

只把官方题面和附件作为要求来源。网上解析、往届论文和 AI 复述只能作为候选解释，不能覆盖题面原文。

### Step 1: 原文锚定精读 (45 min)

**精读三遍,每遍不同任务:**

第一遍 (10 min): 抓动词。题目让你做什么? "求最优..." / "预测..." / "评价..." → 决定问题类型。

第二遍 (10 min): 抓约束。哪些条件不能违反? 列出来。

第三遍 (10 min): 抓数据接口。哪些参数题目会给? 哪些要从附件提? 哪些要假设?

把每个动作、定义、给定条件、约束与交付物拆成原子要求 `R01...Rn`，填写 `state/problem_spec.md`。每行必须含页/段/表/附件字段锚点、短摘录、解释、对象/范围/单位、对应子问和计划交付物。

### Step 1B: 独立复读与冲突消解 (30 min)

从原题重新提取“要交什么、给了什么、限制什么、各问如何关联”，不要查看第一次的分解文本后改写。将第二次结果写入 `state/interpretation_review.md`，再与 `problem_spec.md` 对照。

对高影响语句写出一个“看似合理但错误”的读法，并用原文细节排除。凡歧义会改变模型族、约束、评价指标或最终交付物，且无法由原文/可靠领域依据解决，记为 high issue 并 `block`，不得静默选择一种解释。

### Step 2: 子问题正式分解 (45 min)

对每个 sub-problem Qi,填写卡片:

```
Q1 卡片
├── 对应原子要求: R01, R02, ...
├── 自然语言描述: <一句话提炼>
├── 输入:
│   - 题目给定参数: ...
│   - 附件数据: 附件 1 第 X 列
│   - 上游问题结果: 无 (Q1 是入口)
├── 输出 (最终决策变量):
│   - x_1, x_2, ... (含义、单位)
├── 约束:
│   - C1: ...
│   - C2: ...
├── 目标:
│   - 最小化/最大化 <什么>
├── 问题类型: <model_catalog 第几类>
└── 难度估计: easy / medium / hard
```

**关键**: 每张 Qi 卡片的“上游依赖”列必须明确写依赖哪些结果。只有题面、数学接口或业务机制支持时才建立依赖；“题目未禁止”不构成复用证据。没有合理依赖时写“无”，并保留理由。

### Step 3: 关键变量统一编号 (30 min)

跨子问题统一符号 (anti_pattern B4: 符号重复定义):

```
全局变量表 (stage 4 会复制到论文)

| 符号 | 含义 | 单位 | 类型 | 出现于 |
|------|-----|------|------|-------|
| x_i | 第 i 个产品的产量 | 件 | 决策变量 | Q1, Q2 |
| p_i | 第 i 个产品的单价 | 元/件 | 参数 (附件 1) | Q1, Q3 |
| α  | 折扣率 | 无量纲 | 参数 | Q3 |
| ξ  | 需求随机扰动 | 件 | 随机变量 | Q3 |
| ... |
```

只收录在目标、约束、数据映射或验证中实际使用的变量；缺少必要变量要补齐，无用途变量要删除。

### Step 4: 数据 schema 扫描 (30 min)

用 pandas 快速扫附件:

```python
import pandas as pd
df = pd.read_excel("附件1.xlsx")
print(df.shape)
print(df.dtypes)
print(df.describe())
print(df.isnull().sum())
```

输出 schema 卡片:
```
附件 1 (xlsx):
- 行数/列数: `<由扫描结果写入>`
- 时间跨度: `<由原始字段计算>`
- 缺失: `<列名、计数与比例；不得预填>`
- 异常: `<检测口径与实际命中；不得预填>`
- 与变量映射: p_i ← 列 "价格", d_i ← 列 "需求量"
```

### Step 5: 子问题关系图 (15 min)

以 mermaid / ASCII 表达:

```
<上游 Qi> (<任务>)
  ↓ <有证据支持的输出接口>
<下游 Qj> (<任务>)
  ↓ <有证据支持的输出接口>
最终: <题面要求的交付>
```

写入 `decision_log.stages.2.decomposition`。

### Step 6: 目标函数雏形 (30 min)

每个 Qi 写出符号化目标 (不必完整,要框架):

```
Q1: max  Σ_i p_i * x_i  - C(x)
    s.t. Σ_i x_i ≤ B (预算)
         x_i ≥ 0, x_i ∈ Z

Q2: 在 Q1 基础上加约束 K_i ≤ K_max
    
Qi: <与该子问题匹配的符号化目标>
    若使用上游结果或 warm start，注明接口与依据；否则保持独立
```

每个目标、硬约束和最终输出必须标注对应 Requirement ID。若一个数学对象找不到题面要求或已记录假设作为来源，先删除或回到题意审查，而不是让模型自行补全题目。

### Step 7: 输出移交 (5 min)

写入 `decision_log.stages.2`:
```json
{
  "problem_source": {"path": "...", "sha256": "...", "official_url": "..."},
  "requirement_traceability": [{"id": "R01", "source_anchor": "...", "subproblem": "Q1", "deliverable": "..."}],
  "interpretation_review": {"path": "state/interpretation_review.md", "conflicts_resolved": 0, "blocking_conflicts": 0},
  "ambiguities": [],
  "decomposition": [...],
  "key_variables": [...],
  "key_constraints": [...],
  "objective_per_subproblem": {"<Qi>": "..."},
  "data_schema": {...},
  "subproblem_dependency": {"<Qi>": ["<only evidence-backed upstream IDs>"]}
}
```

---

## L1 Rubric (`rubrics.md` Stage 2)

| 维度 | 满分行为 |
|------|---------|
| 1. 子问题分解清晰度 | 每 Qi 卡片完整 |
| 2. 关键变量识别 | 覆盖目标、约束与数据接口，标注类型与 Requirement ID，无占位变量 |
| 3. 数学化程度 | 每 Qi 有目标雏形，且目标/硬约束可回溯到题面或显式假设 |
| 4. 数据契合度 | schema 已扫,变量映射清楚 |
| 5. 子问题关联性 | 原子要求覆盖完整，独立复读已消解冲突；每个 Qi 的依赖或独立理由均已识别 |

---

## 常见坑

- 题目仅读一次就开干 → 强制读 3 遍
- 用流畅复述代替原文证据 → 每条要求保留来源锚点与短摘录
- AI 两次改写被误当作独立复读 → 第二遍必须从原题重新提取
- 子问题间符号不统一 (B4) → 统一变量表
- 附件数据没扫 → strictly 必做 Step 4
- 为了“串起来”强行复用上游结果 (G1) → 只保留题面、数学或业务机制支持的依赖

---

## 退出条件

1. `problem_source_manifest.json`、`problem_spec.md` 与独立复读记录存在
2. 题面全部请求均映射到子问题和计划交付物，且阻断歧义为 0
3. 题面中的全部子问题卡片完整
4. 全局变量表覆盖后续模型实际所需项且无凑数项
5. 数据 schema 扫描完成
6. 每个 Qi 的依赖关系明确 (依赖 / 独立,均有理由)
7. L1 rubric 全维 ≥7；任何未解决的高影响理解冲突优先 `block`

→ 跳转 `stage_03_model_selection.md`
