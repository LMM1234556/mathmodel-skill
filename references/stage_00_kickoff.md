---
stage: 0
name: kickoff
duration_h: 1
inputs:
  - "user_inputs.{competition, competition_year, problem_id, team_size, deadline, pdf_path}"
outputs:
  - "stage.0.{team_roles, tools_ready, problem_scan, time_budget_h, collab_protocol, checklist_completed}"
  - "root.{competition, task_type}"
  - "compliance.ruleset.{competition_year,basis_year,basis_status,replacement_required,snapshot_path,verification_status,critical_unknowns,conflicts,last_audit}"
loads_reference:
  - "references/rule_verification_protocol.md"
  - "competitions/huawei/current_rules.md"
  - "competitions/huawei/provisional_rules.json (only when Huawei prior-year fallback is selected)"
  - "competitions/huawei/topic_specs.json"
  - "competitions/huawei/README.md"
loads_template:
  - "templates/shared/decision_log.json"
  - "templates/shared/rules_snapshot.json"
  - "templates/shared/requirements.txt"
feedback: ["L1"]
next: "stage_01_problem_selection | wait_for_prompt"
---

# Stage 0 — 团队启动与资料预扫

**时长**: 1h | **反馈层**: L1 | **触发**: skill 首次启动 / 用户说"开始建模"

---

## 目标

在题目正式公布前(或公布后立即),把队伍状态调到"上手即可执行",避免后续阶段因协作/工具/角色问题反复返工。

---

## 输入

- 用户提供: 队员数 (默认 3) / 截止时间 / 模式偏好
- (若题目已发布) 题目 PDF 文件路径

## 产出

- `state/decision_log.json` 初始化,问题元信息填好
- 角色分工表 (写入 `decision_log.stages.0.team_roles`)
- 工具就绪 checklist
- 初步问题域识别 (优化 / 预测 / 评价 / 分类 / 仿真 / 综合) → 影响 stage 3

---

## 操作流程

### Step 1A: 适用范围与年份确认 (2 min) — 第一个交互门

先合并当前用户消息与已有 state，只确定两个字段：

1. **适用范围** — 明确是 `huawei` 华为杯中国研究生数学建模竞赛；
2. **目标年份** — 参赛届次对应的公历年份。

用户已经明确提供时直接复述确认，不重复询问。若用户说的是其他比赛，说明当前版本不支持并停止；不得套用华为杯规则。年份缺失时只问年份，不把题号、模型、规则版本等问题混进这一轮。

确定后由 agent 调用初始化器，不让参赛者手工执行：

```bash
python <skill>/scripts/init_project.py \
  --workspace <cwd> \
  --competition huawei \
  --year <year>
```

初始化器必须写入：

- `decision_log.competition`；
- `decision_log.problem_meta.year`；
- `decision_log.compliance.ruleset.competition_year`。

年份写入前，不得加载规则、模板、经验统计或题号列表。若任一状态文件已存在，初始化器必须拒绝覆盖；agent 改为读取、核对并恢复已有项目，并确认 `competition == huawei`。

### Step 1B: 当届规则核验 (3 min) — 第二个交互门

读取 `references/rule_verification_protocol.md`，打开初始化器生成的 `<cwd>/state/rules_snapshot.json`，再读取 `competitions/huawei/current_rules.md`。打开其中研创网官方来源，核验目标年份的参赛资格、赛程、题目下载、官方模板/封面、字体/段落、分页/页数、匿名、附录/支撑材料、提交文件、提交流程、AI、引用与原创性要求；仓库经验值不能覆盖官方通知。

- 每类规则在快照中只能标为 `confirmed`、`unknown` 或 `not_applicable`；`confirmed` 必须绑定事实与官方来源 ID，`not_applicable` 也必须有官方来源和理由。
- 格式四类必须独立展示，不得合并成“格式已确认”。摘要页数与全文页数必须分开；若当届完整文件没有规定某项，只能记录“已检查的官方文件未规定”，不得猜值。
- 当届规则完整：写入 `basis_year=competition_year`、`basis_status=current_official`、`replacement_required=false`。
- 当届规则不完整：先向参赛者展示“类别—状态—关键事实—来源—影响”表及阻断阶段，再让其选择“等待当届规则”或“采用可用的往届临时基线”。不得自动启用往届规则。
- 2026 项目加载 `competitions/huawei/official_rules_2026.json` 作为维护者基线，但仍须打开官方来源并把实际访问证据写入项目快照；只有其他目标年份当届文件不完整且参赛者明确批准时，才加载 `provisional_rules.json`。

将规则快照摘要同步到 `decision_log.compliance.ruleset`，然后运行：

```bash
python <skill>/scripts/audit_ruleset.py \
  --snapshot state/rules_snapshot.json \
  --decision-log state/decision_log.json \
  --phase kickoff
```

任何 error 阻断 Stage 0；warning 必须向参赛者展示并写入 `critical_unknowns`，不能改写成“已完全核实”。

### Step 1C: 其余元信息 (剩余时间) — 规则状态确定后

再合并当前消息与 state，只询问尚缺字段：

1. **题号** — 依已选赛事的当届题面动态生成；题面未发布时只提供“未公布”；
2. **队员数与各人擅长** — 自由文本；
3. **截止时间** — ISO 字符串或“距现在 X 小时”；
4. **题目 PDF 路径** — “未公布”亦可。

禁止让用户手动编辑 `decision_log.json`。Agent 写入 `problem_meta`、PDF 来源事件和后续状态。Stage 0 不预加载 `winning_patterns.md`：只有后续阶段需要某条经验模式、且能追溯其适用证据时才按需读取。

**自动读取华为杯基线**（来自 `competitions/huawei/README.md` 与 `topic_specs.json`）:
- 2026 邀请函公布的比赛时长为 100h；其他年份必须重新核验
- 写作语言为中文，除非当届题面另有要求
- 正式提交使用当届官方标准文档；仓库 xelatex 只生成内部评阅稿
- 题号对应的 task-type 路由候选（仅在题号真实可用后确认）

题面未公布或尚未读取时，`problem_scan.subproblem_count` 与 `stages.5.qi_count` 保持 `null`；不得用历史题目或 `topic_specs.json` 猜默认子问数。

`task_type` 字段在 Stage 1 读取当届试题后再填；题型不能可靠识别时使用 `default`，不得从往届题号猜测。

### Step 2: 角色分工 (10 min)

确保以下三类职责都有明确主责与互备。队员少于三人时允许一人兼任，队员更多时可拆分；不要虚构成员或为满足表格强行一人一岗:

| 角色 | 主责内容 | 互备 |
|------|---------|------|
| **建模主** | stage 2/3/4/5 主导,数学公式 | 编程主 |
| **编程主** | stage 5 求解、stage 6 灵敏度 | 建模主 |
| **写作主** | stage 8 主导,stage 1/9 协助 | 全员 |

**反模式 J1** (`competitions/huawei/anti_patterns.md`): "人人都负责一切，实际无人主责" — 拒绝。
每位真实队员写一句"我对这道题/这个角色的最大顾虑是什么"。

### Step 3: 工具就绪 checklist (15 min)

逐项确认 (bash 验证):

```bash
python --version           # ≥ 3.10

# 运行华为杯 skill 自检
python <skill>/scripts/doctor.py --competition huawei --workspace .

# 完整建模依赖检查 (一次性安装见 templates/shared/requirements.txt)
python -c "import numpy, scipy, sklearn, cvxpy, pandas, statsmodels, SALib, pdfplumber, imblearn"

# MATLAB 是工作流中定量图的必备渲染器
matlab -batch "disp(version); assert(exist('exportgraphics','file')==2)"

# 关键 solver 检查 (优化类必备)
python -c "import cvxpy; assert 'GLPK_MI' in cvxpy.installed_solvers(), '需 pip install cvxopt'"

# LaTeX 必备
xelatex --version          # 仅用于华为杯内部评阅稿

which git
```

如缺依赖, 一键安装:
```bash
pip install -r <skill>/templates/shared/requirements.txt
```

**初始化结果检查**：确认 Step 1A 的 `init_project.py` 已生成
`state/{decision_log.json,rules_snapshot.json}` 与
`results/`、`figures/`、`paper_workspace/`。不得在这里再次复制模板或覆盖状态。

确认 `<skill>/templates/latex/huawei/main.tex` 只能用于内部评阅。2026 官方提交模板是 `.doc`；第三方或仓库 LaTeX 不因外观相似而获得官方地位。

### Step 4: 题目预扫 (题目公布后,15 min)

用户提供题目 PDF 后，agent 用当前 harness 可用的文件读取工具先核对题面与附件，再做快速识别；不要只读固定页数后就假定任务已完整：

输出格式:
```json
{
  "problem_id": "<year-letter from the official prompt>",
  "domain_keywords": ["<extracted keyword>"],
  "data_attachments": ["<actual attachment path and description>"],
  "subproblem_count": "<count parsed from the official prompt>",
  "primary_problem_type": "<inferred type with evidence>",
  "secondary_types": ["<only if applicable>"],
  "estimated_difficulty": "<easy|medium|hard with rationale>",
  "data_size_signal": "<actual scan result>"
}
```

写入 `decision_log.events.log`,作为 stage 1 输入。

### Step 5: 时间预算分配 (10 min)

从真实 deadline 倒推并写入 `decision_log.stages.0.time_budget_h`。题面未公布时只记录 **provisional** 总预算与以下保留项，不给 Stage 5 猜子问数量或“每问小时数”：

- 为最终装配、格式复核、支撑材料上传和不可预见故障保留明确缓冲。
- 题面公布后，根据实际子问、依赖链、数据清洗量、求解成本和当届交付要求，再分配 Stage 1–9。
- Stage 5 与 Stage 8 通常占主体，但具体比例必须来自当前题面和团队能力；验证与合规不能被压缩为零。
- 当届标准文档替换、MD5 锁定、PDF 上传、题面专项附件和 AI 披露材料都要进入真实预算。
- 剩余时间不足时，列出会牺牲的验证或表达范围，让用户确认取舍，不假装仍能完成完整流程。

### Step 6: 协作约定 (5 min)

写入 `decision_log.stages.0.notes`:
- 命名规范: 文件 / 变量 / Python 模块
- 版本控制: 由团队按产物边界约定提交/检查点节奏
- 沟通节奏: 由 deadline 与并行任务决定；每次同步必须包含阻断项和交接产物
- 求助升级: 为当前赛程约定明确触发条件，不使用脱离任务风险的固定时长

---

## L1 Rubric (5 维 × 1-10)

参考 `rubrics.md` Stage 0 节。每维必须 ≥7 才通过。

```json
{
  "stage_id": 0,
  "scores": {
    "1_role_clarity": {...},
    "2_tools_ready": {...},
    "3_time_planning": {...},
    "4_problem_scan": {...},
    "5_collab_protocol": {...}
  }
}
```

## 常见坑 (anti_patterns)

- **J1**: 三人都全栈不深 → 强制角色主责
- **J2**: 选题摇摆 (跳到 stage 1 才出现)
- **J3**: 写作留到最后 → time budget 把 stage 8 提前到 day 2

## 退出条件

1. `decision_log.stages.0.checklist_completed == true`
2. `audit_ruleset.py --phase kickoff` 无 error，所有 warning 与 unknown 已展示并写入状态
3. 团队角色明确,工具全员 ready
4. (若题目已发布) 题目预扫完成
5. L1 rubric 全维 ≥7

分支：

- **题面与候选题已可读** → 跳转 `stage_01_problem_selection.md`。
- **题面未公布/不可读** → 写入 `current_stage=0` 与等待原因，停止内容生成并等待用户提供题面；恢复时从 Step 4 继续，不重复已完成的角色和环境准备。

---

## 与 Stage 1 的衔接

仅在 Step 4 已完成时，把题目预扫 JSON 作为 Stage 1 的上下文输入，避免重新读题。没有题面时不得伪造预扫或进入选题。
