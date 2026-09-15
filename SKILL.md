---
name: mathmodel-skill
description: “华为杯”中国研究生数学建模竞赛专用的端到端协作与质量控制工作流。Use when a user is preparing for or participating in the Huawei Cup China Postgraduate Mathematical Contest in Modeling and needs source-anchored problem interpretation, per-question human approval, default-deny data isolation, comparable model selection, MATLAB figures, paper writing, compliance, or final review. Do not trigger for CUMCM, MCM/ICM, Diangong Cup, generic model selection, ordinary data analysis, or non-competition paper review.
---

# mathmodel-skill — 华为杯数学建模工作流 (v7.0)

10 阶段把华为杯约 100 小时的竞赛协作变成可恢复、可检查的流程。用户回答关键问题，agent 维护状态与脚本。流程重点控制三类高风险错误：题意误读、跨题串用数据、模型与图表未经参赛者确认。Stage 8–9 必须重新核验当届官方规则；仓库没有获奖概率模型，华为杯经验统计为 `n=0`。

**v7.0 范围**：当前发行版只支持华为杯。其他赛事资料若仍存在于仓库，只是未来扩展的非活动历史资源，不得加载、不得作为当前规则来源，也不属于本版本的质量承诺。

---

## Codex 原生入口

Codex 优先按 skill 目录发现本文件:

- 用户级安装: `$HOME/.agents/skills/mathmodel-skill/`
- 项目级安装: `<repo>/.agents/skills/mathmodel-skill/`
- UI 元数据: `agents/openai.yaml`
- 插件分发元数据: `.codex-plugin/plugin.json` + `skills/mathmodel-skill/SKILL.md` shim
- 项目指导: `AGENTS.md` 仍可作为 repo / workspace 级 instructions, 但不是唯一入口

当 skill 已安装后, 用户可直接说"开始建模"或显式说"使用 `$mathmodel-skill` 开始建模"。

---

## Harness 兼容 (Claude Code / Codex)

本 skill v7.0 以 Codex Skills 为一等入口, 同时保持 harness-agnostic 设计:

| harness | 入口文件 | 用户交互工具 | 状态文件 |
|---------|---------|-------------|---------|
| Claude Code | `SKILL.md` (本文件) | `AskUserQuestion` 工具 | `<cwd>/state/decision_log.json` |
| Codex CLI / Codex app | skill 目录中的 `SKILL.md` + 可选 `AGENTS.md` | markdown 编号列表 | 同上 (**互通**) |

跨 harness 互通: day 1 用 Codex 跑 stage 0-2, day 2 切回 Claude Code 接着 stage 3+, 状态完全保留。详见 `references/harness_compat.md`。

---

## 问答式优先 (Friendly Mode)

**核心原则**: 用户只需回答**编号问题**, 不应被要求手敲 bash / python / json。

- 离散选项 (选竞赛 / 选题 / 选模型 / verdict 决策) → **必须**用问答式
- 自由文本 (PDF 路径 / 截止时间) → 单行回复
- 状态读写 (decision_log.json) → agent 自动完成
- 每个 stage 的关键决策点都有 "让我决定 (推荐 X)" 兜底选项

优先使用当前 harness 可用的原生选择 UI；没有时回退到 markdown 编号列表。两者语义等价，见 `references/harness_compat.md` §1。

---

## 路径解析协议 (任何阶段必读)

| 类型 | 位置 | 例 |
|------|------|-----|
| skill 内通用 | skill 根目录的相对路径 | `references/stage_05_subproblem_loop.md`, `templates/shared/decision_log.json` |
| **华为杯规则与写作资源** | `competitions/huawei/...` | `competitions/huawei/current_rules.md` |
| **内部评阅模板** | `templates/latex/huawei/main.tex` | 仅内部评阅，不是官方提交模板 |
| 用户产物 | 用户工作目录的相对路径 | `<cwd>/state/`, `<cwd>/results/`, `<cwd>/figures/`, `<cwd>/paper_workspace/` |
| state 持久化 | `<cwd>/state/decision_log.json` | 各 stage 必读必写 |
| 环境变量 | `MATHMODEL_STATE_DIR` | scripts 用此变量 |

约定: `<skill>/` = skill 安装目录，`<cwd>/` = 用户工作目录；`decision_log.competition` 必须固定为 `huawei`。

---

## Quick Start (用户首次说"开始建模")

```
1. 一段话介绍 (≤50 字): "启动华为杯数学建模工作流，先核验年份与规则，再逐题确认。"

2. **Gate S0-A — 先确认适用范围与年份**。确认用户参加的是“华为杯”中国研究生数学建模竞赛，并取得目标年份。若用户说的是其他比赛，说明本版本不支持并停止，不得套用华为杯规则。年份缺失时只询问年份。

3. 自动初始化 (agent 自动完成, 不要让用户编辑 json):
   - 确认后运行 `python <skill>/scripts/init_project.py --workspace <cwd> --competition huawei --year <year>`
   - 脚本同时创建 `decision_log.json`、空白 `rules_snapshot.json` 与工作目录；不得省略目标年份或改用其他 competition
   - 已存在任一状态文件 → 脚本拒绝覆盖；读取现有 schema、competition 与 current_stage 决定恢复或迁移，不重新初始化

4. **Gate S0-B — 再核验当届规则**。读取 `references/rule_verification_protocol.md` 与 `competitions/huawei/current_rules.md`，打开研创网官方链接核对目标年份并建立 `<cwd>/state/rules_snapshot.json`。逐类区分 `confirmed` / `unknown` / `not_applicable`，向参赛者展示缺项与冲突，再运行 `audit_ruleset.py --phase kickoff`。2025 临时基线不得自动启用，也不能授权正式提交。

5. 规则状态确定后，再合并询问题号、队员数与擅长、截止时间、题目 PDF 路径等尚缺启动信息。题号依当届题面动态生成；题面未发布时使用“未公布”，不得从往届预填。

6. 继续 Stage 0 (`references/stage_00_kickoff.md`)，不重复问已知字段；若题面未公布，完成环境与协作准备后保持 `qi_count=null` 并等待题面，不进入 Stage 1。
```

**已有 state 触发** (用户中途回到 skill):
```
1. 读 `<cwd>/state/decision_log.json` 的 schema、competition 与 current_stage
2. 若 schema=3.1、3.2、3.3 或 3.4，先自动运行 `python <skill>/scripts/migrate_state.py <cwd>/state/decision_log.json`；保留备份后再继续。其他未知 schema 不自动改写
3. 加载对应 stage_NN.md，按需结合 `competitions/huawei/*`
4. 不重复读 winning_patterns
```

---

## 华为杯 × 三模式

华为杯当前按 100 小时中文竞赛准备。2026 邀请函已经核验；若当届论文标准或 AI 规则仍不可用，2025 文件只能作为显式 `prior_year_provisional` 演练基线，内部 LaTeX 不能作为提交件。反馈深度由 mode 决定。

| Mode | 上下文策略 | 反馈层 | 用途 |
|---|---|---|---|
| fast | 只保留当前阻断项与最小证据 | L1 单次 | 选题试跑 / sanity check |
| standard | 按阶段加载并保留决策摘要 | L1+L2 | 默认主流程 |
| championship | 在终审阶段扩展证据与独立视角 | L1+L2+L3+L4 + red-team | 提交前最后冲刺 |

模式自动推荐 (按距 deadline 剩余):
- > 60h: standard (最后 6h 升 championship)
- 24-60h: standard
- 6-24h: fast 关键阶段 + championship 终审
- < 6h: 直接进 stage 9 (championship)

---

## 10 阶段索引

| # | 阶段 | reference | 时长 | 反馈 | 竞赛差异点 |
|---|------|-----------|------|------|-----------|
| 0 | 团队启动 + 资料预扫 | `stage_00_kickoff.md` | 1h | L1 | 确认年份、规则状态与官方题面 |
| 1 | 选题 (多题对比 → 1) | `stage_01_problem_selection.md` | 2-4h | L1 | 题号体系 (A-E/A-F/A-B) + task_type 写入 |
| 2 | 原文追踪、独立复读与逐题数据边界 | `stage_02_analysis.md` | 2-3h | L1 + 题意确认 | 题面锚点、依赖图与 question contract |
| 3 | 逐题模型候选、验证与预执行审批 | `stage_03_model_selection.md` | 2-4h | L1 + 人工门禁 | 基线/主流/进阶候选按同一任务比较 |
| 4 | Foundation (假设+符号+术语) | `stage_04_foundation.md` | 1h | L1 | 通用 |
| 5 | **受控子问题循环** Q1..Qn + per-Qi 加权聚合 | `stage_05_subproblem_loop.md` | 按题目分配 | 三个审批门 + L1 | 默认拒绝跨题数据；模型复评；MATLAB 图表确认 |
| 6 | 全局灵敏度 / 稳健性 | `stage_06_robustness.md` | 2-3h | L1 + L2 | 按题面风险选择工程、数据或数学参数 |
| 7 | 模型评价 + 推广 | `stage_07_evaluation.md` | 1-2h | L1 | 通用 |
| 8 | 证据驱动论文写作 + 合规装配 | `stage_08_writing.md` | 12-30h | L1 + L2 | Claim IDs、反向提纲、AI 台账与官方标准文档 |
| 9 | 提交合规 + 反向追踪 + Panel | `stage_09_review.md` | 2-6h | L1 + L3 panel | requirement/claim/figure 审计 + panel |

---

## 加载协议 (节省 token 的关键)

**只在进入阶段 N 时加载** `references/stage_NN_*.md`。**切勿**一次性全读。

各阶段额外加载（只使用华为杯资源）:
- 每阶段开头: `<cwd>/state/decision_log.json` 必读
- 每阶段结尾: `<cwd>/state/decision_log.json` 必写 (核心决策 + 5 维评分)
- stage 1-9: `references/rubrics.md` 对应章节 (L1 评分用)
- **stage 1**: `competitions/huawei/topic_specs.json`；赛前 topics 为空，必须从当届试题 ZIP 建立题号与 task_type
- **stage 2**: `references/problem_understanding_protocol.md` + `references/question_contract_protocol.md` + `templates/shared/{problem_spec.md,question_contract.json}`
- **stage 3, 5**: `references/question_contract_protocol.md` + `references/model_catalog.md`；Stage 3 运行 `audit_question_contracts.py --phase plan`，Stage 5 求解前运行 `--phase execute --question <Qi>`，完成后运行 `--phase final --question <Qi>`
- **stage 5 / 8 / 9**: `references/visualization_protocol.md`; 所有定量图必须由 MATLAB 生成，复制 `templates/shared/matlab/` 使用 `mm_choose_chart`、`mm_style` 与 `mm_export_figure`
- **stage 5**: per-Qi 评分跑完后调 `scripts/score_artifact.py --mode aggregate_qi` 聚合
- **stage 0 / 8 / 9**: 读取 `references/rule_verification_protocol.md`，核对 `competitions/huawei/current_rules.md` 中的官方链接，维护 `state/rules_snapshot.json`；依次运行 `audit_ruleset.py --phase kickoff|writing|final`
- **stage 8**: `competitions/huawei/{winning_patterns,phrase_bank,abstract_template,paper_skeleton}.md`
- **stage 8 / 9**: `references/paper_quality_protocol.md`，维护 Claim IDs、证据矩阵与反向提纲
- **stage 8 经验锚点**: `competitions/huawei/empirical.json` 为 `n=0`，不得输出论文分位、获奖概率或伪经验阈值
- **stage 9**: 先做规则合规门，再用 `anti_patterns.md` 与 `rubric_overlay.json` 的 panel personas
- 触发反馈时: 对应 `references/feedback_layer*.md`
- harness 适配差异 (Codex 用户必读): `references/harness_compat.md`

---

## 收敛准则 (统一定义, 三处一致)

评分 verdict 不能覆盖人工审批与数据隔离门禁。任一 Qi 出现以下情况时先 `block`：

- 题意或高影响歧义未经团队确认；
- `question_contract` 未通过 plan/execute/final 对应阶段审计；
- 正式代码读取未声明的数据、字段、范围或上游结果；
- `approvals.pre_execution` 未批准却开始正式求解；
- `approvals.final_model` 未批准却写入确定性模型结论；
- `approvals.final_figures` 未批准却把图表标记为正式稿。

详细协议见 `references/question_contract_protocol.md`。审批只覆盖当前合同；数据、依赖、目标、硬约束或验证方案变化会使批准失效，并向下游传播 stale 状态。

**verdict 优先级 (从高到低)**:

| verdict | 触发 | 行为 |
|---------|------|------|
| `block` | issues 含 ≥1 high-severity | 暂停 skill, 用户介入 |
| `pass_early` | raw_min ≥ 9 AND weighted_mean ≥ 9 | iter-1 早退 |
| `pass` | raw_min ≥ 7 AND weighted_mean ≥ 8 | 进下一阶段 |
| `pass_with_review` *(stage 5)* | 任 Qi mark_for_review 但加权阈值满足 | 进 stage 6, L2 必读 review_qis |
| `refine` | 其他 | section-patch 精修, iter+=1 (cap 3) |
| `refine_partial` *(stage 5)* | 任 Qi.min < 7, 其他 Qi 已 pass | 仅 refine 该 Qi, 不动其他 |
| `carryover` | iter == 3 仍 refine | 进下一阶段, 标记由 L2 处理 |

`weighted_mean` = Σ(s_i × w_i) / Σ(w_i)，权重来自 `config/dim_weights.json[huawei][<task_type>]`（clamp [0.7, 1.5]）；题型未可靠识别时使用 `default`。

此定义在 `feedback_layer1_critic.md` / `rubrics.md` / `scripts/score_artifact.py` 三处必须**完全一致**。

---

## 状态持久化

每阶段:
- 开头: 读取 `<cwd>/state/decision_log.json`, 核对 current_stage 与上下文
- 结尾: 更新 stage 节点 (核心决策 + 摒弃方案 + 评分), `current_stage += 1`

`decision_log.json` v3.5 schema 关键字段 (与 `templates/shared/decision_log.json` 对齐):
- root: `competition`, `task_type`, `mode`, `current_stage`, `budget`, `events`, `compliance`
- compliance ruleset: `competition_year`, `basis_year`, `basis_status`, `replacement_required`, `snapshot_path`, `verification_status`, `critical_unknowns`, `conflicts`, `last_audit`；详细证据保存在 `state/rules_snapshot.json`
- stage_2 扩展: `problem_source`, `requirement_traceability`, `interpretation_review`, `ambiguities`, `question_contracts`
- stage_3 扩展: `question_contracts_plan_audit`, `pre_execution_approvals`
- stage_5 扩展: `qi_count`, `qi_weights`, `qi_status`, `question_contracts_dir`, `question_contract_audits`
- stage_8/9 扩展: claim-evidence、reverse-outline、figure-registry 与 reverse-trace gate
- scores 扩展: 含 `weighted_mean`, `review_qis`, `refine_qis` (stage 5 加权聚合用)

L2 跨阶段回检 (stage 5/6/8 末尾) 读这个文件主动找冲突, 触发**定向回滚**: 不重做整阶段, 只针对冲突点。

---

## 上下文预算纪律

- L1 Critic 强制 JSON 输出, ~500 token/次
- 精修策略: section-level patch (`scripts/extract_diff.py`), 优先只传相关 section
- references/ 与 competitions/ 文件**懒加载**, 本 SKILL.md 主体 ≤ 6k tokens
- 阶段完成后, artifact 摘要 + 关键数据 + 路径写入 decision_log, 不在上下文保留全文
- 只有当前 harness / API 提供可靠 usage 时才记录 token 消耗；不可观测时保留为 `null`，不得估算成已用额度
- 上下文压力或剩余时间不足时，向用户建议从 championship → standard → fast 降级，并把确认后的 mode change 写入 events；不要声称已自动计量或静默切换

---

## 用户指令快捷

- "进入 stage N" / "重做 stage N" → 跳转
- “切到其他比赛” → 说明 v7.0 仅支持华为杯并停止；不得改写已有项目的 competition
- "升级到 championship" → 启用 L3 + L4 + red-team
- "切到 fast" → 关闭迭代
- "回退到 stage M" → 读 decision_log, 回退 current_stage 并清理 ≥M 节点
- "做 L2 回检" → 立即触发 cross-stage backtrack
- "看进度" → 输出 decision_log 摘要 + 当前评分

---

## 数据来源声明

- `competitions/huawei/`: 2026 邀请函与官方通知列表已于 2026-09-14 核对；2025 官方格式与 AI 规则可作显式临时基线，但当届文件发布后必须替换，内部模板不得作为提交件，empirical 为 `n=0`
- 通用模型清单 `references/model_catalog.md` 跨竞赛复用

---

## 与外部资源的关系

核心工作流可离线运行，但当届规则与问题要求必须从官方来源重新核对。官方优先来源为中国研究生创新实践系列大赛管理平台及当届竞赛系统。公众号或学校转载只能用于发现线索，关键规则必须回到官方页面或官方附件核实。
