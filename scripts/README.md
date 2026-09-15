# Scripts 工具说明

v7.0 的活动运行时只面向华为杯。用户项目中的动态文件写入项目工作目录，不写回 Skill 仓库。

## 运行时工具

### `init_project.py`

在确认华为杯目标年份后原子初始化状态。`competition` 仍显式传入，便于审计，但唯一合法值是 `huawei`。

```bash
python scripts/init_project.py \
  --workspace /path/to/project \
  --competition huawei \
  --year 2026
```

脚本不会覆盖已有 `decision_log.json` 或 `rules_snapshot.json`。

### `doctor.py`

检查 Skill 结构、华为杯竞赛包、状态模板和本地工具链。

```bash
python scripts/doctor.py --competition huawei --workspace /path/to/project
python scripts/doctor.py --competition huawei --skip-tools --json
python scripts/doctor.py --competition huawei --require-renderer --require-modeling
```

### `audit_ruleset.py`

检查华为杯目标年份、官方来源、九类关键规则、未知项和临时回退批准。`final` 要求当届官方规则完整。

```bash
python scripts/audit_ruleset.py \
  --phase kickoff \
  --snapshot state/rules_snapshot.json \
  --decision-log state/decision_log.json
```

### `audit_question_contracts.py`

检查逐题题意、数据边界、依赖、候选模型、验证计划和人工批准。

```bash
python scripts/audit_question_contracts.py --workspace /path/to/project --phase plan
python scripts/audit_question_contracts.py --workspace /path/to/project --phase execute --question Q1
python scripts/audit_question_contracts.py --workspace /path/to/project --phase final --json
```

### `score_artifact.py`

校验 Critic JSON、计算 verdict，并写入 `state/decision_log.json`。活动项目必须从状态读取到 `competition=huawei`。

```bash
python scripts/score_artifact.py \
  --competition huawei \
  --stage 5 \
  --critique state/critique_v0.json \
  --decision-log state/decision_log.json
```

### `render_paper.py`

将标准 Markdown 工作区装配为华为杯内部评阅稿。输出不能替代当届官方标准文档。

```bash
python scripts/render_paper.py \
  --competition huawei \
  --workspace paper_workspace \
  --output-dir paper_output
```

### 其他辅助工具

- `extract_diff.py`：阶段内定向修改；
- `migrate_state.py`：迁移旧 schema；
- `render_ai_usage.py`：保留的历史披露工具，不定义华为杯官方输出格式；
- `download_cumcm_papers.py`、`ingest_papers.py`：非活动历史维护工具，不属于华为杯运行时。

## 路径协议

| 类型 | 位置 |
|---|---|
| Skill 静态资源 | `<skill>/{references,templates,scripts,competitions/huawei}` |
| 项目状态 | `<project>/state/` |
| 逐题合同 | `<project>/state/questions/<Qi>/question_contract.json` |
| 项目产物 | `<project>/{results,figures,paper_workspace,paper_output}` |

不要在 Skill 仓库根目录运行参赛项目初始化。
