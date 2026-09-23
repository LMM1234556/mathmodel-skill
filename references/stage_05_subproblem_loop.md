---
stage: 5
name: subproblem_loop
duration_h: 6-12 per Qi
inputs:
  - "stage.2.{decomposition, subproblem_dependency, question_contracts, interpretation_approval}"
  - "stage.3.{selected_per_subproblem, question_contracts_plan_audit, pre_execution_approvals}"
  - "stage.4.{assumptions, symbols}"
outputs:
  - "stage.5.sub_problems.{Qi}.{question_contract_path, model_name, math_formulation_path, code_path, results_path, figures, key_metrics, approvals, contract_audits, physical_meaning_summary, scores, issues, iterations}"
  - "stage.5.cross_reference_chain"
  - "stage.5.assumption_change_history"
loads_reference: ["references/question_contract_protocol.md", "references/model_catalog.md", "references/visualization_protocol.md", "competitions/huawei/winning_patterns.md§5", "references/rubrics.md§Stage_5"]
loads_template: ["templates/shared/code_starter/<problem_type>.py", "templates/shared/matlab/"]
feedback: ["L1_per_Qi", "sub_checkpoint", "L2_at_end_for_stage_3_4_consistency"]
next: stage_06_robustness
---

# Stage 5 — 受控子问题循环 (Q1..Qn)

**时长预算**: 6-12h × n 个子问题 | **反馈层**: L1 + 子检查点

---

## 目标

为每个子问题 Qi 跑一遍受控的完整 mini-pipeline: **合同审计 → 基线与候选求解 → 公平验证 → 最终模型确认 → 子结果分析 → MATLAB 图表确认 → 必要的子灵敏度**。子问题默认数据隔离；只有题面、数学接口或业务机制提供依据且写入 contract 时才允许复用。这是论文主体，也是最容易因数据串用而产生致命错误的阶段。

---

## 输入

- stage 2 子问题卡片、数据边界、依赖图和 question contracts
- stage 3 候选模型、验证方案、预执行批准和 plan audit
- stage 4 假设/符号/术语
- (进入存在依赖的 Qi 时) 已验证的上游结果
- `state/questions/<Qi>/question_contract.json`

## 产出

- 每 Qi 的: 数学模型完整公式 + 求解代码 + 可复现结果 + 支撑关键论点所需的图/表 + 物理意义讨论
- 每张定量图由 MATLAB 生成；claim、数据来源、`.m` 生成脚本、选图理由、编码与 caption 记录在 `figures/figure_registry.json`
- 跨子问题: 有依据的依赖显式传递；无依赖时显式记录独立理由
- 每 Qi 保存实际读取路径、最终模型和最终图表批准；合同变化显式失效并传播到下游
- 写入 `decision_log.stages.5.sub_problems.{Q1, Q2, Q3, ...}`

---

## 递归循环结构

```
for Qi in [Q1, Q2, ..., Qn]:
    A0. 加载 question contract，执行 --phase execute 审计
    A. 模型完整化 (45 min)
    B. 在同一数据合同下实现有效基线与保留候选 (2-4h)
    C. 公平验证、比较并让参赛者批准最终模型
    D. 有证据需要时做子灵敏度
    E. 根据结果确定 MATLAB 图表并让参赛者批准
    F. 物理意义 (15 min)
    G. L1 自评 + 必要时 diff-only 精修
    H. 输出移交、执行 --phase final 审计与跨 Qi 检查
```

---

## 单 Qi 操作流程详解

### A0. 合同加载与执行门禁

读取 `state/questions/<Qi>/question_contract.json`，先向参赛者简短复述已批准的题意、数据文件/表/字段/范围、上游结果、候选模型、验证和初步图表计划，再由 agent 自动运行：

```bash
python <skill>/scripts/audit_question_contracts.py \
  --workspace <cwd> --phase execute --question <Qi>
```

审计通过前不得编写或运行正式求解器。运行时只允许读取 contract 中声明的原始数据和上游 result IDs，并从实际代码/运行日志把文件与哈希、工作表、字段、行范围、筛选、排除项和预处理写入 `data_contract.observed_accesses`，不得凭记忆补写。发现新数据、字段、筛选范围、排除项、连接键、预处理、上游结果、目标或硬约束时，立即停止，将 contract 标为 `invalidated`，重置 `pre_execution` 批准，更新受影响的下游 Qi 后重新确认。

### A. 模型完整化 (45 min)

把 stage 2 的目标雏形 + stage 3 保留的基线与候选模型，升级为可在同一任务下比较的正式数学公式。预执行推荐可以优先实现，但不得跳过 contract 中作为最终比较依据的有效基线：

```
问题 Qi 数学模型 (<与实际实现一致的模型名>):

Decision Variables:
  x_i ∈ X_i, i ∈ I

Parameters:
  p_i: 单价 (元/件), 来自附件 1 列 P
  c_i: 成本 (元/件), 来自附件 1 列 C
  B: 总预算 (元), 来自 <题面/附件/配置路径>

Objective:
  max f(x) = Σ_i (p_i - c_i) x_i

Constraints:
  C1: Σ_i c_i x_i ≤ B              (预算约束)
  C2: l_i ≤ x_i ≤ u_i              (由题面/数据确定的边界)
  C3: x_i ∈ X_i                    (变量域)
```

要求:
- 每个变量、参数、约束都有编号
- 公式用 LaTeX (即使现在是 markdown, stage 8 直接复制)
- 声称的松弛、复合或自适应机制必须出现在公式与代码中，并在结果中提供可核验证据；否则使用标准模型名
- 使用满足任务所需的最小数学结构：非优化任务不虚构目标函数，非约束任务不虚构约束，非动态任务不虚构状态方程；每个公式都必须对应题意、实现或验证中的具体作用

### B. 求解实现 (2-4h)

求解器可用 Python (numpy/scipy/sklearn/cvxpy) 或 MATLAB 实现。若用 Python，计算产物必须保存为 CSV/MAT，定量图仍由 MATLAB 读取并生成。**约定**:

```python
"""
Q1 求解 - 对应论文 §5.1
<与 stage 3 和公式一致的模型名称>
"""
import numpy as np
import pandas as pd
import cvxpy as cp
import json
np.random.seed(42)  # 可复现性

# Step 1: 只加载本 Qi question contract 已批准的数据
df = pd.read_excel("data/附件1.xlsx")
with open("config/problem.json", encoding="utf-8") as fh:
    config = json.load(fh)
p = df["price"].values
c = df["cost"].values
n = len(p)
B = float(config["budget"])
lower = df["lower_bound"].values
upper = df["upper_bound"].values

# Step 2: 建模
x = cp.Variable(n, integer=True)
profit = (p - c) @ x
constraints = [
    cp.sum(c * x) <= B,
    x >= lower,
    x <= upper
]
prob = cp.Problem(cp.Maximize(profit), constraints)

# Step 3: 求解
prob.solve(solver=cp.GLPK_MI)
print(f"Q1 求解状态: {prob.status}")
print(f"目标函数值: {prob.value:.2f}")
print(f"求解时间: {prob.solver_stats.solve_time:.2f} s")

# Step 4: 保存结果
x_star = x.value.astype(int)
np.save("results/Q1_x.npy", x_star)
```

代码要求:
- 中文注释 (anti_pattern D1)
- 首行明确 "对应论文 §X" (`competitions/huawei/winning_patterns.md` §10)
- 设 random seed (anti_pattern D4)
- `print` 关键状态 (sanity check)
- 结果保存到 `results/Qi_*.npy` 或 `.csv`
- 保存本次实际输入路径、字段、行数、筛选与哈希；与 `data_contract` 不一致立即失败
- 基线和候选使用相同任务定义、硬约束、数据版本与验证切分；无法公平比较时不得报告“提升”

### C. 结果验证、候选比较与最终模型批准

四步 sanity check (anti_pattern D2/D3):

1. **状态检查**: `prob.status == "optimal"` ?
2. **数量级**: 结果是否满足题面/数据给出的边界与单位?
3. **边界 case**: 对该模型最关键的边界输入，输出是否符合可独立推导的预期?
4. **与基线对比**: 和一个满足同一约束的简单基线比较；若同目标下反而更差，先排查模型与求解器。

```python
# 共享同一份剩余预算的可行贪心基线
x_greedy = lower.astype(int).copy()
remaining = float(B - c @ x_greedy)
assert remaining >= -1e-8, "题面下界已超过预算，需回查数据或模型"
margin = p - c
order = np.argsort(-np.divide(
    margin, c, out=np.full_like(margin, -np.inf, dtype=float), where=c > 0
))
for i in order:
    if c[i] <= 0 or margin[i] <= 0:
        continue
    capacity = max(0, int(upper[i] - x_greedy[i]))
    addition = min(capacity, int(max(remaining, 0) // c[i]))
    x_greedy[i] += addition
    remaining -= addition * c[i]

assert c @ x_greedy <= B + 1e-8
profit_greedy = ((p - c) * x_greedy).sum()
print(f"贪心基线利润: {profit_greedy:.2f}")
print(f"本模型利润: {prob.value:.2f}")
if abs(profit_greedy) > 1e-12:
    print(f"相对变化: {(prob.value - profit_greedy) / abs(profit_greedy) * 100:.2f}%")
else:
    print("贪心基线为 0，不报告百分比")
```

不通过任一项 → 回 A 检查模型。

按 Stage 3 预先登记的指标、切分/情景和失败条件比较有效基线与保留候选。报告绝对指标、相对变化、稳健性、计算时间、解释性和失败场景；不得在看见结果后只更换对推荐模型有利的指标。若验证设计必须改变，先使 pre-execution approval 失效并重新确认。

向参赛者展示比较表和推荐理由，由参赛者决定论文最终模型。将选择写入 `execution.chosen_model_id`，并把确认人、时间和 `--digest-for final_model` 生成的摘要写入 `approvals.final_model`。在最终模型批准前，不得把模型写成论文定论；“分数最高”也不能替代参赛者批准。

### D. 子灵敏度 (按需)

只对本子问题中会影响结论、且存在测量误差、估计误差或情景不确定性的参数做局部灵敏度 (全局留 stage 6)。扰动范围来自数据精度、置信区间、规则边界或领域证据；若没有有意义的不确定参数，记录理由并跳过，不生成装饰性曲线:

```python
# documented_deltas 来自测量精度、估计区间或领域证据
deltas = documented_deltas
profits = []
for d in deltas:
    p_perturb = p * (1 + d)
    # 重新求解
    profit_d = (p_perturb - c) @ x_star  # 用同一 x*, 看新参数下利润
    profits.append(profit_d)

pd.DataFrame({"delta": deltas, "profit": profits}).to_csv(
    "results/Q1_sensitivity_plot_data.csv", index=False
)
```

### E. 最终图表方案与批准

上面的 Python 代码只输出绘图数据。正式图表必须读取
`references/visualization_protocol.md`，由 MATLAB 脚本读取 CSV/MAT，并使用
`templates/shared/matlab/` 中的 `mm_choose_chart`、`mm_style` 与
`mm_export_figure`。先声明论点和分析任务，再记录所选图形及被拒方案；不得在结果出来后为“丰富论文”补装饰图。

每个 Qi 结束前，将 `.figure.json` sidecar 汇总进
`figures/figure_registry.json`。同一数据或结论的重复图只保留表达最清楚的一张；需要精确查数时优先使用表格。

结果产生后重新判断最终图表类型，不因 Stage 3 的初步推荐而锁死。向参赛者展示图表草稿、对应 result/claim、备选图形、单位、不确定性和选图理由。批准后填写 `figure_plan.final_chart_types`、`rationale`、`result_ids`，并把确认人、时间和 `--digest-for final_figures` 生成的摘要写入 `approvals.final_figures`。如果本 Qi 不需要图，保留已批准的 `no_figure_reason`，不得为凑图生成装饰图。

### F. 物理意义讨论 (15 min)

围绕题面所问的含义解释结果，并把每个判断绑定到保存的产物；以下是占位结构，不得把示意数字复制进论文:

```
求解状态与主结果: <从 results/Qi_* 自动读取，不手填>。
关键结构: <哪些变量/群组驱动结果>；证据: <表、图或诊断路径>。
机制解释: <由约束、参数或数据支持的解释>；不确定部分明确标注。
基线比较: <仅在目标、约束和数据相同且可公平比较时报告实际差异>。
结论边界: <哪些假设或数据变化会使解释失效>。
```

解释必须回答“为什么会得到该结果”，但证据等级要分开：由方程、约束或可控实验直接
支持的机制可以明确陈述；仅由相关、特征重要性、SHAP、PDP 或分组差异观察到的关系，
只能写成关联或模型内解释，不能升级为因果机制。对关键变量至少记录方向、量级/区间、
适用范围和反例或失败场景；没有证据时写未知，不用常识补齐。

### G. L1 自评 + diff-only 精修

调用 `references/feedback_layer1_critic.md` 协议:
- 输出 5 维 JSON 评分
- 保留该 Qi 的完整 `issues`；任一未解决 `severity=high` 立即将聚合 verdict 置为 `block`，分数不能覆盖高严重度问题
- 修复后的 issue 移入事件历史并附验证证据；传给聚合器的 `issues` 只保留当前未解决项，不能直接丢弃来绕过 block
- 若任一维 <7 → diff-only 精修, iter+=1, 上限 3
- 全维 ≥9 → 早退

### H. 输出移交、合同终审与跨 Qi 检查

在写入论文前锁定本 Qi 的证据链：先有已运行代码、输入哈希、保存结果和验证记录，
再据此定稿“模型建立”与“模型求解”。A 节中的公式是执行前数学规格，不是允许提前写死
的论文结果；正式“模型建立”只写与最终代码一致的方法、变量、假设和公式，不混入结果；
“模型求解”中的数字、排名、图表和结论只能读取已登记的实际输出。代码、公式或结果任一
变化，都使对应论文段落和下游 Claim 标为 stale，重新核对后才能解锁。

写入 `decision_log.stages.5.sub_problems.Q1`:
```json
{
  "question_contract_path": "state/questions/Q1/question_contract.json",
  "model_name": "...",
  "math_formulation_path": "results/Q1_model.tex",
  "code_path": "results/Q1_solve.py",
  "results_path": "results/Q1_x.npy",
  "figures": ["<only figures that support a named claim>"],
  "figure_registry_ids": ["Q1-F01"],
  "key_metrics": {"<metric_name>": "<value loaded from saved result>"},
  "physical_meaning_summary": "...",
  "approvals": {"pre_execution": "approved", "final_model": "approved", "final_figures": "approved"},
  "contract_audits": {"plan": "passed", "execute": "passed", "final": "passed"},
  "scores": {...},
  "issues": [
    {"severity": "high|medium|low", "where": "...", "problem": "...", "fix": "..."}
  ],
  "iterations": 1
}
```

在实际输入、结果、代码和批准状态写回 contract 后，将 contract `status` 设为
`completed`，由 agent 自动运行：

```bash
python <skill>/scripts/audit_question_contracts.py \
  --workspace <cwd> --phase final --question <Qi>
```

final audit 失败时将 Qi 置为 `block`，不得进入下一个 Qi 或论文正式写作。

#### 跨 Qi 子检查点

进入 Qi+1 之前,**自检**:

1. **复用链**: Q2 是否要用 Q1 的 x_star?
   - 题目要求? → 必须用
   - 题目允许? → 只有在依赖关系有数学或业务依据时复用，并记录理由
   - 题目禁止? → 跳过
   - 实际读取未登记? → 立即 block，删除错误产物或更正 contract 后重新批准和求解

2. **符号一致**: Qi 中用的 x, p, c 是否与 stage 4 符号表一致?
   - 不一致 → 立即更新本 Qi 或更新符号表 (二选一并记录)

3. **假设一致**: Qi 模型是否引入了新假设?
   - 是 → 回 stage 4 加假设, 写入 decision_log
   - 否则 → 继续

4. **假设变更历史检查** (P2-3 新增) ⭐: 若 stage 4 的某假设在已完成 Qi 之后被 patch (L2 触发), 自检该 Qi 是否依赖被改假设。
   - **依赖** → 重跑该 Qi 的 Step C (sanity check) + Step D (子灵敏度), 不重跑完整 5 步
   - **不依赖** → 在 `decision_log.stages.5.assumption_change_history` 标记 "Qi 不受 patch X 影响, 跳过重跑"
   - 检查方法: 读 `decision_log.events.log` 找 `type=L2_backtrack` 且 `target=stage.4.assumptions[k]` 的记录, 然后 grep Qi 的代码与 math_formulation 是否引用 assumption k

5. **合同失效传播**: 上游数据、模型或结果改变时，读取其 `invalidation.downstream_questions`，将所有受影响 Qi 标记 stale，清除对应 final audit pass；只重跑真正受影响的 Qi，但不得保留旧论文结论。

---

## L1 Rubric (Per-Qi)

| 维度 | 满分行为 |
|------|---------|
| 1. 模型与问题契合 | 目标/变量/约束 与题面 1:1 |
| 2. 数学严谨性 | 符号一致, 推导无跳跃 |
| 3. 求解正确性 | 代码运行 + sanity check 通过 |
| 4. 结果表达 | 每个关键论点有最合适的图、表或数值证据；图表可追溯、单位完整、最终尺寸可读，不重复、不凑数量 |
| 5. 物理意义讨论 | 解释与结果证据绑定；baseline 仅在公平可比时使用 |

## L1 Rubric (Stage-level)

| 维度 | 满分行为 |
|------|---------|
| 1. 子问题完整性 | 所有 Qi 都跑完 |
| 2. 依赖链 | 有依据的上下游接口均显式传递；无合理依赖时理由已记录 |
| 3. 符号一致 | 全 Qi 用同一套 stage 4 符号 |
| 4. 证据表达 | 图、表与数值产物足以支持关键论点且无装饰性重复 |
| 5. 时间预算 | 在已确认的 stage 5 预算内完成；偏差已留痕并获用户确认 |

## 常见坑

- D1-D5 求解类全部 → Step B/C 严格执行
- E1-E4 结果分析类 → Step E 物理意义必写
- G1 子问题各做各 → Step H 子检查点强制
- G2 子问题模型族突变 → 切换需在 H 显式记录触发条件

## H.2 per-Qi 差异化降级机制 (v3.0 新增)

整体均分可能掩盖单个 Qi 的薄弱项。新协议保留每个 Qi 的分数与 issues，并引入 per-Qi 加权聚合 + 差异化降级；任何未解决 high issue 优先 block:

### 聚合规则

```python
# 加载 decision_log.stages.5.qi_weights (默认 [1.0]*qi_count)
qi_results = [
    {"qi": "Q1", "min": 8, "mean": 8.5, "scores": {...}, "issues": []},
    {"qi": "Q2", "min": 7, "mean": 7.2, "scores": {...}, "issues": [...]},
    {"qi": "Q3", "min": 8, "mean": 8.8, "scores": {...}, "issues": []}
]
qi_weights = decision_log.stages.5.qi_weights  # e.g. [1.0, 1.5, 1.0] 若 Q2 是题目核心

weighted_mean = Σ(qi.mean × weight) / Σ(weight)
weighted_min  = min(qi.min for qi in qi_results)

# issue gate 优先于任何分数 verdict
high_issues = [
    {"qi": qi["qi"], **issue}
    for qi in qi_results
    for issue in qi["issues"]
    if issue.get("severity") == "high"
]
if high_issues:
    verdict = "block"
    # 停止聚合放行，保存 high_issues 并请求用户处理
else:
    # Qi 状态判定 (单 Qi 独立)
    for qi in qi_results:
        if qi["min"] >= 7 and qi["mean"] >= 8: qi["status"] = "pass"
        elif qi["min"] >= 7:                    qi["status"] = "mark_for_review"
        else:                                    qi["status"] = "refine"
```

### Verdict 决策

| 场景 | verdict | 后续 |
|------|---------|------|
| 任一 Qi 有未解决 high issue | `block` | 保存 issues 并暂停；不得由高分、平均分或 carryover 覆盖 |
| 全 Qi pass + weighted_min ≥ 9 + weighted_mean ≥ 9 | `pass_early` | iter-1 早退 |
| 全 Qi pass + weighted_min ≥ 7 + weighted_mean ≥ 8 | `pass` | 进 stage 6 |
| 无 refine 且任 Qi 为 mark_for_review，且加权阈值满足 | `pass_with_review` | 进 stage 6, **L2 必读 review_qis** (写入 stage 5 末尾的 L2 触发条件) |
| 仅部分 Qi 为 refine，至少一个 Qi 非 refine | `refine_partial` | **只 refine 低分 Qi**, 不动其他已验证 Qi |
| 全部 Qi 都为 refine | `refine` | 整体回到受影响的 Step A0-H，优先排查共享模型、数据或假设问题 |
| 无 refine，仅有 mark_for_review 但 weighted_mean < 8 | `refine` | 对薄弱内容做 stage-level 修补 |

### 示例

`Q2 mean=7.2 min=7` (mark_for_review) + Q1/Q3 都 pass + weighted_mean=8.2:
- verdict = `pass_with_review`, review_qis = ["Q2"]
- decision_log.stages.5.qi_status = {"Q1": "pass", "Q2": "mark_for_review", "Q3": "pass"}
- L2 在 stage 5 末尾必读 Q2 段, 检查"是否需要 stage 6 顺便重跑 Q2 灵敏度"

`Q2 min=5` (refine) + Q1/Q3 都 pass:
- verdict = `refine_partial`, refine_qis = ["Q2"]
- 只重跑 Q2 受影响的 Step A0-H；Q1/Q3 的已验证产物保持不动，除非依赖失效传播命中
- iter+=1 仅对 Q2; 老 iter cap 3 仍生效。仅低分且无 high issue 时可按既有协议 carryover；high issue 永不 carryover

全部 Qi 都低于 per-Qi 门槛:
- verdict = `refine`，不是 `refine_partial`
- 整体检查共享数据处理、符号、假设和模型接口，再重跑受共同原因影响的 Step A0-H

### 调用脚本 + verdict 问答确认 (v5 Friendly Mode)

```bash
# 在所有 Qi 跑完 per-Qi critic 后, agent 自动触发 (用户不必敲):
python <skill>/scripts/score_artifact.py \
  --mode aggregate_qi \
  --qi-results state/qi_results.json \
  --decision-log state/decision_log.json
# qi_results.json schema: {qi_results: [{qi, min, mean, scores, issues}], qi_weights: [...]}
# 输出并写入 state: {verdict, weighted_min, weighted_mean, qi_status, block_qis, review_qis, refine_qis}
# 完整 issue 对象仍保留在各 qi_results 与 decision_log 中
```

脚本出 `verdict` 后，先应用 high-issue gate。若 verdict=`block`，保存完整 issues 并停止放行，以编号问答让用户选择处理方式；不得提供“强制 carryover”选项:

```
【Stage 5 已阻断: <Qi> 存在未解决 high issue】

  1) 按 issue.fix 修复并重跑受影响 Qi (推荐)
  2) 回退到 issue 指向的上游阶段重新决策
  3) 暂停并保留当前可恢复状态

回复数字。
```

非 block verdict 再由 agent **问用户一次**确认 (Claude Code: AskUserQuestion; Codex CLI: 编号列表):

```
【Stage 5 聚合完成: verdict=refine_partial, Q2 需 refine, Q1/Q3 已 pass】

  1) 按推荐 refine Q2 (重跑 Q2 受影响的 Step A0-H, Q1/Q3 不动, 耗时按当前预算估算)
  2) 全 stage refine (含 Q1/Q3, 耗时按当前预算估算)
  3) 强制 carryover, 接受当前结果进 stage 6 (Q2 弱点留 stage 9 panel 处理)
  4) 让我决定 (推荐 1)

回复数字。
```

用户回复后 agent 自动执行, **不要**让用户编辑 decision_log 或重跑脚本。

### qi_weights 调整时机

默认 `[1.0] * qi_count` 由 stage 1 锁题后初始化。用户可在 stage 5 第一个 Qi 完成时根据题目重要性调整 (e.g., `[1.0, 1.5, 1.0]` 若 Q2 是核心)。调整后写回 `decision_log.stages.5.qi_weights`, 后续聚合按新权重。

---

## 退出条件 (整个 stage 5)

1. 所有 Qi 的 question contract 均通过 plan、execute、final 三阶段审计，三个团队批准均存在；评分不能覆盖合同错误
2. 所有 Qi 通过 per-Qi rubric (全维 ≥7) **或** verdict ∈ {pass, pass_with_review} 经 H.2 聚合
3. Stage-level rubric 全维 ≥7
4. 所有有依据的依赖链已实现并验证；实际输入不包含未声明或禁止数据
5. (championship) red-team 一次,针对最弱的 Qi (优先 review_qis)
6. `figures/figure_registry.json` 覆盖正文候选图；所有定量图 `renderer=MATLAB`，且不存在错误单位、无来源、无选图理由或无论点的图；无图 Qi 有已批准理由
7. 触发 L2: 跨阶段回检 stage 3 (模型选择前提是否被结果推翻) + stage 4 (符号一致性) + **review_qis 列表 (若 verdict=pass_with_review)**

→ 跳转 `stage_06_robustness.md`

---

## 与 stage 6/8 的衔接

stage 6 全局灵敏度需要本节的求解器代码 (重用)。
stage 8 写论文 §5 直接基于本节产出, 每 Qi 一个小节。
