---
stage: 2
name: analysis
duration_h: 2-3
inputs:
  - "stage.1.selected"
  - "problem_pdf"
  - "attachment_data_paths"
outputs:
  - "stage.2.{problem_source, requirement_traceability, interpretation_review, ambiguities, decomposition, key_variables, key_constraints, objective_per_subproblem, data_schema, subproblem_dependency, question_contracts, interpretation_approval}"
  - "state/{problem_spec.md,problem_source_manifest.json,interpretation_review.md,questions/<Qi>/question_contract.json}"
loads_reference:
  - "references/problem_understanding_protocol.md"
  - "references/question_contract_protocol.md"
  - "references/rubrics.md§Stage_2"
loads_template: ["templates/shared/problem_spec.md", "templates/shared/question_contract.json"]
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
- 每个 Qi 的独立 question contract 草稿，锁定题意、数据边界与依赖关系
- 参赛者对逐题理解和数据边界的显式确认

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
├── 输出/交付物:
│   - <预测、评价、方案、参数、决策变量或解释> (含义、单位/编码)
├── 约束:
│   - C1: ...
│   - C2: ...
├── 数学任务:
│   - <估计/预测/评价/分类/优化/仿真/机制分析；只写题目实际要求>
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

### Step 4B: 建立“分析问题—决策”登记表

探索性分析不能按软件菜单批量生成。每一项拟执行的统计、诊断或可视化先登记：

| Analysis ID | 要回答的问题 | 允许数据/字段 | 方法 | 将影响的决策 | 输出证据 |
|---|---|---|---|---|---|
| EDA-Q1-01 | `<例如是否存在明显时间漂移>` | `<合同内字段>` | `<统计/检验/图>` | `<切分、变换、模型或验证选择>` | `<待运行>` |

运行后补充观察结果、局限和实际采取的下游动作。若结果不会影响题意判断、数据处理、
模型、验证、图表或结论，删除该分析，不用“多做一些图”代替建模证据。相关性和分组
差异只作为描述或候选机制；没有识别设计时不得写成因果关系。

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

### Step 5B: 建立逐题数据合同与依赖边界

读取 `references/question_contract_protocol.md`。为每个 Qi 复制
`templates/shared/question_contract.json` 到
`state/questions/<Qi>/question_contract.json`，先填写以下部分：

- `source.requirement_ids`、`source_anchors`、`team_interpretation` 与 `deliverables`；
- `dependencies.upstream_results` 或 `independence_rationale`；
- `dependencies.forbidden_inputs`；
- `data_contract.datasets` 或 `no_data_reason`。

每个数据集不能只写“附件 1”，必须写明文件、SHA-256、工作表/表、字段名称与含义、单位、行范围、筛选条件、预处理、排除项和用途。即使两个 Qi 使用同一附件，也分别声明它们实际允许读取的字段和样本范围。

此时模型与图表部分保持待填写，不能伪造候选或批准状态。Stage 3 会完成这些字段并运行 plan audit。

### Step 6: 数学任务雏形 (30 min)

每个 Qi 写出与问题类型匹配的符号化任务（不必完整，但要能约束后续选型）：

```
Q1: max  Σ_i p_i * x_i  - C(x)
    s.t. Σ_i x_i ≤ B (预算)
         x_i ≥ 0, x_i ∈ Z

Q2: 在 Q1 基础上加约束 K_i ≤ K_max
    
Qi: <与该子问题匹配的符号化目标>
    若使用上游结果或 warm start，注明接口与依据；否则保持独立
```

只有优化问题才写目标函数与可行域；只有动态问题才写状态转移；只有受约束任务才写
约束集合。预测、估计、分类、评价或机制分析应分别写清响应、损失/评价口径、比较对象
和验证方式，不得为了“看起来像数学模型”强行添加不存在的结构。

每个目标、硬约束和最终输出必须标注对应 Requirement ID。若一个数学对象找不到题面要求或已记录假设作为来源，先删除或回到题意审查，而不是让模型自行补全题目。

### Step 6B: 参赛者逐题确认

在进入模型选择前，用可读表格一次展示每个 Qi 的：

1. 原文锚点与 Codex 的理解；
2. 预期输出、单位与交付物；
3. 数据文件、工作表、字段、范围、筛选和禁止输入；
4. 上游结果依赖或独立理由；
5. 尚未解决的歧义。

让参赛者批准或逐项修改。不得把“用户没有反对”记为批准。批准写入
`decision_log.stages.2.interpretation_approval`；任何会改变 Qi 目标、数据边界或依赖关系的修改都要更新 contract 并重新确认。

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
  "subproblem_dependency": {"<Qi>": ["<only evidence-backed upstream IDs>"]},
  "question_contracts": {"<Qi>": "state/questions/<Qi>/question_contract.json"},
  "interpretation_approval": {"status": "approved", "approved_by": "...", "approved_at": "...", "notes": "..."}
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
7. 每个 Qi 已创建独立 question contract，数据字段/范围不会从其他 Qi 默认继承
8. 参赛者已明确批准逐题理解、交付物、数据边界和依赖；沉默不算批准
9. L1 rubric 全维 ≥7；任何未解决的高影响理解冲突优先 `block`

→ 跳转 `stage_03_model_selection.md`
