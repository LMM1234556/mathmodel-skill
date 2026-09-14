---
stage: 3
name: model_selection
duration_h: 2-3
inputs:
  - "stage.2.{decomposition, objective_per_subproblem, data_schema, question_contracts, interpretation_approval}"
outputs:
  - "stage.3.{candidate_models, selected_per_subproblem, rejection_log, toy_demos_passed, red_team, model_family_consistency, question_contracts_plan_audit, pre_execution_approvals}"
loads_reference:
  - "references/model_catalog.md"
  - "references/question_contract_protocol.md"
  - "references/rubrics.md§Stage_3"
  - "competitions/<comp>/winning_patterns.md§4"
loads_template: ["templates/shared/code_starter/<problem_type>.py"]
feedback: ["L1", "counterfactual_exploration_in_championship"]
next: stage_04_foundation
---

# Stage 3 — 模型选型 (证据驱动的合理候选集)

**时长**: 2-3h | **反馈层**: L1 + 反事实探索 (championship 深挖真实可行的替代路径)

---

## 目标

为每个子问题建立一个可比较的候选集、有效基线和预执行推荐，并在正式求解前让参赛者确认数据、模型、验证与初步图表计划。Stage 3 的选择是待实证检验的推荐，不是最终“最优模型”；最终模型在 Stage 5 使用同一任务、数据和验证方案比较后再次确认。候选数量由问题结构和证据决定；若检索后没有合理替代，记录检索范围与原因，不用不适配模型凑数。

---

## 输入

- stage 2 输出: 子问题卡片 + 目标函数雏形 + 数据 schema + 每个 Qi 的 question contract
- stage 2 的逐题理解、数据边界和依赖已经参赛者批准
- `references/model_catalog.md` 必读

## 产出

- 每个 Qi 的有效基线、合理候选、预执行推荐 + 准确名称 + 选型理由
- 每个 Qi 的合理替代候选 + 否决理由；没有合理替代时记录检索证据
- 每个 Qi 的验证计划、失败条件、证据问题与初步图表候选
- 每个 Qi 的预执行人工批准和 question-contract plan audit
- 覆盖关键失败模式的最小可执行 demo (Python)
- (championship) red-team 攻击与回应

---

## 操作流程

### Step 1: 问题类型映射 (10 min)

对每个 Qi,查 `references/model_catalog.md` §0 速查表:

```
Q1: "求最优生产计划" → 优化类 (LP/IP)
Q2: "考虑库存约束" → 优化类 (MIP) + 启发式
Q3: "随机需求下的稳健决策" → 鲁棒优化 / 随机规划 / 蒙特卡罗
```

### Step 2: 候选生成 (45 min)

为每个 Qi 从题面目标、约束类型、数据规模、缺失机制与可用求解器出发生成候选。优先保留结构性不同且能解决**同一任务**的方案；跨模型族只有在目标与约束仍可公平比较时才有意义。完成目录与文献检索后若只有一个合理方案，明确记录“未找到合理替代”及检索范围:

```
Qi 候选 <ID>: <模型与模型族>
  - 适配证据: <对应目标/约束/数据性质>
  - 实现路径: <库/求解器/自实现>
  - 可验证优势: <用什么基线或诊断验证>
  - 风险: <复杂度、假设或数据风险>
  - 结论: retain / reject；<证据>
```

**反模式 C3 检查**: 若候选只是同一方法换名字，合并重复项；若跨族方案不能解决同一任务，不得为了“多样性”加入。多样性是发现反事实的手段，不是数量门槛。

### Step 3: 选型决策矩阵 (30 min)

为每个 Qi 做加权评分:

| 维度 | 权重 | `<候选 1>` | `...` | `<候选 N>` |
|------|-----|-----------|-------|-----------|
| 1. 适配度 (与问题契合) | 0.30 | `<score>` | `...` | `<score>` |
| 2. 求解可行性 (库支持/复杂度) | 0.25 | `<score>` | `...` | `<score>` |
| 3. 时间预算 (实施所需 h) | 0.20 | `<score>` | `...` | `<score>` |
| 4. 可验证增益空间 | 0.15 | `<score>` | `...` | `<score>` |
| 5. 文献或理论支持 | 0.10 | `<score>` | `...` | `<score>` |
| **加权** | | `<weighted>` | `...` | `<weighted>` |

→ 推荐证据最充分且在时间预算内可验证的候选；分数不能替代否决证据，也不能把“推荐”写成已经证明的最优模型。

每个 Qi 至少保留一个满足同一目标和硬约束的有效基线。若没有通常意义上的简单基线，说明为什么，并设计最低复杂度的有效对照。模型比较必须预先固定共同数据合同、指标/目标、约束和验证切分，避免只给复杂模型更有利的条件。

### Step 4: 可核验命名 (15 min)

名称只写已经进入公式、代码或实验的限定条件与机制:

模式: `<已实现且可核验的限定/机制> + <核心模型>`

若只实现标准模型，就使用标准名称。不得为了显得创新添加“改进”“自适应”“多层”等修饰词；声称复合、松弛或动态机制时，必须能指向对应公式、代码与消融/基线证据。

预执行推荐名称与证据位置写入 `decision_log.stages.3.selected_per_subproblem.<Qi>`；Stage 5 的最终选择可以不同，但必须保留变更理由和新的团队批准。

### Step 4B: 完成逐题执行卡并获取批准

把候选与决策矩阵写入各 Qi 的 `question_contract.json`：

- `model_plan.candidates`：有效基线、主流方案、进阶方案中真正可比较的候选；
- `recommended_candidate_id` 与 `selection_criteria`；
- `validation_plan`：共同指标、切分/情景、基线 ID 和失败条件；
- `figure_plan`：需要回答的证据问题、候选图形和初步推荐；如果本 Qi 不需要图，填写 `no_figure_reason`，不得为凑图强制可视化。

先由 agent 自动运行：

```bash
python <skill>/scripts/audit_question_contracts.py --workspace <cwd> --phase plan
```

任何 error 都是 high issue 并 `block`。审计通过后，向参赛者展示完整执行卡：题意、交付物、数据文件/字段/范围、禁止输入、上下游依赖、候选模型、推荐理由、验证方式、失败条件和初步图表。参赛者批准后填写 `approvals.pre_execution` 的状态、确认人、时间和由审计脚本生成的 `contract_digest`。沉默、继续聊天或只批准模型名称都不算完整批准。

如果参赛者要求修改，更新 contract、重新运行 plan audit，再次展示变化后的执行卡。在 plan audit 和预执行批准均通过前，不得运行正式求解器或写正式结论。

### Step 5: Toy Demo 验证 (45 min)

在本 Qi 的预执行批准后写最小可执行 demo。规模应足以覆盖关键约束、已批准的数据接口和已知失败模式：优先从真实数据构造代表性切片；若真实数据尚不可用，使用明确标注的合成 sanity case。不要用固定行数、固定抽样比例或固定秒数代替可行性证据。Toy demo 不是正式结果，不得进入论文证据注册表：

```python
# Qi feasibility demo - 用项目中的实际构造器保持接口一致
case = build_representative_case(problem_data, cover=critical_constraints)
model = build_model(case)
result = solve(model, time_budget=remaining_stage_budget)

assert result.status in accepted_statuses
assert constraints_hold(result, case)
record_runtime_and_scale(result, case)
```

要求:
- 求解器状态可解释，输出满足关键约束
- 数据规模与覆盖范围有记录，能暴露主要失败模式
- 运行时间不超过该候选在实际 deadline 下的可用预算
- 结果数量级通过题面边界或独立基线校验

不通过 → 候选无效，回 Step 2 修改 contract。候选、数据切片、验证方案或推荐发生变化时，原 `pre_execution` 批准失效，重置为 `pending` 并重新展示执行卡；不得沿用旧批准。

### Step 6: 跨子问题模型族协调 (10 min)

检查全部 Qi 的主模型是否能通过明确接口衔接:
- 库或数据结构不同是否有可靠转换层?
- 不同模型族组合时，输入输出、触发条件与误差传播是否明确?
- 为统一工具而牺牲问题适配度时，回到 Step 3 重评。

写入 `decision_log.stages.3` 的 "model_family_consistency" 字段。

### Step 7 (championship 模式): Red-team 攻击 (30 min)

> 假装最严苛评委，列出能够改变选型结论的实质攻击，并给出可核验回应。合并同义攻击；没有新的实质攻击时停止，不凑数量。

模板:
```
攻击: <能够改变选型结论的失败模式>
证据需求: <benchmark、收敛诊断、接口检查或公式/代码定位>
回应: <已有证据；没有证据时写待验证，不预填结论>
状态: resolved | open
```

写入 `decision_log.stages.3.red_team`。

### Step 8: 输出移交 (10 min)

写入 `decision_log.stages.3`:
```json
{
  "candidate_models": [...],
  "selected_per_subproblem": {
    "<Qi>": {"name": "...", "library": "...", "rationale": "...", "evidence_paths": [...]}
  },
  "rejection_log": [...],
  "toy_demos_passed": true,
  "red_team": [...],
  "model_family_consistency": "...",
  "question_contracts_plan_audit": {"status": "passed", "checked_at": "...", "findings": []},
  "pre_execution_approvals": {"<Qi>": {"status": "approved", "approved_by": "...", "approved_at": "..."}}
}
```

---

## L1 Rubric

| 维度 | 满分行为 |
|------|---------|
| 1. 候选质量与反事实覆盖 | 所有合理替代均被评估；无合理替代时检索范围与原因可审计 |
| 2. 选型理由 | 每候选有适配 + 不选原因 |
| 3. 命名准确性 | 每个修饰词均能定位到公式、代码与验证；允许标准名称 |
| 4. 求解可行性 | toy demo 通过 |
| 5. 文献/理论支撑 | 关键选型主张有相关且已核验的来源；不以篇数代替相关性 |

championship 额外: red_team 覆盖所有能改变结论的实质攻击，每个回应有证据或明确的待验证状态。

## 常见坑

- C1 为显得创新强行改名 → Step 4 要求名称与实际实现逐项对应
- C2 模型不匹配 → Step 1 速查表对照
- C3 候选重复或伪跨族 → 合并同义项，只保留真正可比较的替代
- C4 选型理由薄弱 → Step 3 5 维矩阵
- C5 不验证可行性 → Step 5 toy demo

## 退出条件

1. 每 Qi 有有效基线、可比较候选和预执行推荐；名称与计划实现一致
2. 每 Qi 的合理替代已评估；若无替代，检索范围与理由已记录
3. 每 Qi 已固定共同验证条件和初步图表计划，或有不作图的正当理由
4. 每 Qi 的完整执行卡已获参赛者明确批准，question-contract plan audit 通过
5. toy demo 通过；若它改变合同，已经重新批准
6. (championship) 所有实质 red-team 攻击均有证据回应或明确的未解决风险
7. L1 全维 ≥7

→ 跳转 `stage_04_foundation.md`
