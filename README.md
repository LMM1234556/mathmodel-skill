# mathmodel-skill

> 华为杯中国研究生数学建模竞赛专用的 Codex Skill：把题意理解、逐题数据、模型决策、MATLAB 图表、论文证据和提交规则放进一条可恢复、可审计的工作流。

[![Version](https://img.shields.io/badge/version-v7.0.0-6f42c1)](./.codex-plugin/plugin.json)
[![Scope](https://img.shields.io/badge/scope-Huawei%20Cup-f97316)](./competitions/huawei/)
[![License](https://img.shields.io/badge/license-MIT-2ea44f)](./LICENSE)

## 当前范围

v7.0 只支持“华为杯”中国研究生数学建模竞赛。

- 不接受 CUMCM、MCM/ICM 或电工杯项目；
- 不把其他比赛的页数、模板、AI 披露格式套入华为杯；
- 仓库中保留的其他赛事目录属于未来扩展的非活动历史资源；
- 华为杯 `empirical.json` 当前为 `n=0`，不提供论文分位或获奖概率；
- `templates/latex/huawei/main.tex` 只生成内部评阅稿，正式提交必须使用当届官方标准文档。

## 为什么做这个 Skill

数学建模中最危险的问题通常不是“模型不够复杂”，而是：

1. 把题目的限定词、对象或交付物理解错；
2. 多个子问题使用不同数据，却被错误地套用同一套数据；
3. 模型由 AI 直接决定，参赛者没有比较候选与失败条件；
4. 图表好看但类型不适合，或无法回溯到结果文件；
5. 论文写完后才发现规则、匿名、AI 披露或提交文件不合格。

本 Skill 以逐题合同和人工审批门控制这些风险，不承诺获奖，也不代替参赛者判断。

## 十阶段流程

| Stage | 目标 | 关键门禁 |
|---:|---|---|
| 0 | 确认华为杯年份、规则、团队和环境 | 当届规则快照审计 |
| 1 | 基于当届官方试题选择题目 | 不用往届题号猜题 |
| 2 | 原文追踪、独立复读、逐题数据边界 | 逐题题意确认 |
| 3 | 建立可比较的模型候选和验证计划 | 预执行批准 |
| 4 | 固化假设、符号和术语 | 与题意和合同一致 |
| 5 | Q1…Qn 受控求解 | 数据、最终模型、最终图表三重批准 |
| 6 | 验证、灵敏度与稳健性 | 风险与方法匹配 |
| 7 | 模型评价和推广边界 | 所有评价有证据 |
| 8 | 证据驱动论文写作 | Claim—result—figure 可追溯 |
| 9 | 规则、证据、图表和 PDF 终审 | 当届官方文件完整才能提交 |

## 三条核心约束

### 1. 每道子问题有独立合同

项目中每个 `Qi` 保存：

```text
state/questions/Q1/question_contract.json
state/questions/Q2/question_contract.json
...
```

合同分别记录原文理解、交付物、数据文件、表/字段/行范围、上游结果、禁止输入、候选模型、验证方案和图表方案。未经批准不得执行正式求解。

### 2. 模型必须比较后再决定

候选应能在相同任务、数据、约束和验证指标下比较。保留有效基线，不为凑数量加入不适用模型；只有一个候选时必须解释检索过程和排除依据。最终采用哪个模型由参赛者确认。

### 3. 定量图统一由 MATLAB 生成

Python、求解器或其他工具可以计算，但绘图数据必须保存为 CSV/MAT，再由 MATLAB 生成图表。每张正式图绑定：

- Claim 与决策问题；
- 源数据和 result ID；
- MATLAB `.m` 生成脚本；
- 图表类型及被拒方案；
- 单位、编码、不确定性和 caption。

鲜艳颜色用于突出信息，不使用彩虹色、3D 柱状图或无意义装饰。

## 规则边界

当前规则基线见 [`competitions/huawei/current_rules.md`](competitions/huawei/current_rules.md)。

2026 邀请函已经核验，但论文标准、AI 规则和题面必须在开赛时重新从研创网或竞赛系统获取。若只采用 2025 临时基线：

```json
{
  "competition_year": 2026,
  "basis_year": 2025,
  "basis_status": "prior_year_provisional",
  "replacement_required": true,
  "submission_authorized": false
}
```

这种状态可以训练和预排版，不能把项目标记为正式提交就绪。

## 安装

仓库为私有仓库。运行 `git clone` 时需使用有访问权限的 GitHub 账号；Windows 通常会由 Git Credential Manager 打开浏览器完成登录。

Windows 用户级安装：

```powershell
New-Item -ItemType Directory -Force "$HOME\.codex\skills" | Out-Null
git clone https://github.com/LMM1234556/mathmodel-skill.git `
  "$HOME\.codex\skills\mathmodel-skill"

python "$HOME\.codex\skills\mathmodel-skill\scripts\doctor.py" `
  --competition huawei
```

项目级安装：

```powershell
New-Item -ItemType Directory -Force ".agents\skills" | Out-Null
git clone https://github.com/LMM1234556/mathmodel-skill.git `
  ".agents\skills\mathmodel-skill"
```

进入一个独立的建模项目目录后启动 Codex，并输入：

```text
使用 $mathmodel-skill，开始 2026 华为杯建模。
```

不要在 Skill 仓库根目录直接创建参赛项目；状态和结果应写入独立工作目录。

## 首次启动顺序

1. 确认项目确实是华为杯并询问目标年份；
2. 运行 `init_project.py --competition huawei --year <year>`；
3. 打开当届官方链接，建立规则快照并执行 kickoff 审计；
4. 再询问题面、题号、团队能力和截止时间；
5. 题面未发布时保持 `qi_count=null`，停在 Stage 0 等待。

参赛者不需要手工编辑 JSON，也不需要自己运行审计命令。

## 主要运行时工具

| 工具 | 作用 |
|---|---|
| `scripts/init_project.py` | 原子初始化华为杯工作区 |
| `scripts/doctor.py` | 检查 Skill、华为杯包、MATLAB 和渲染环境 |
| `scripts/audit_ruleset.py` | 审计当届规则来源和未知项 |
| `scripts/audit_question_contracts.py` | 审计逐题数据、模型和批准状态 |
| `scripts/score_artifact.py` | 处理阶段评分与逐题聚合 |
| `scripts/render_paper.py` | 生成内部评阅 PDF，不替代官方模板 |

## 依赖

核心工作流不要求一次性安装全部建模包。需要运行模型起步代码时：

```powershell
python -m pip install -r templates/shared/requirements.txt
```

正式评阅还需要 MATLAB、Pandoc 和带中文支持的 TeX 发行版。`ReportLab` 已列入可选完整依赖，但华为杯当前没有被仓库擅自定义的官方 AI 披露 PDF 格式。

## 验证

```powershell
python -m compileall -q scripts templates/shared
python -m unittest discover -s tests -p "test_*.py" -v
python scripts/doctor.py --competition huawei --skip-tools
python scripts/doctor.py --competition huawei --require-renderer --require-modeling
matlab -batch "run('tests/matlab/test_mm_figure_pipeline.m')"
git diff --check
```

单元测试和 schema 审计不能证明数学结论正确。正式使用前还应完成一次多子问题行为测试，故意尝试读取错误文件、错误字段和不存在的上游 result ID。

## 项目结构

```text
mathmodel-skill/
├── SKILL.md
├── agents/openai.yaml
├── competitions/huawei/       # 当前唯一活动竞赛包
├── references/                # 十阶段与质量协议
├── scripts/                   # 初始化、审计、评分、渲染
├── templates/shared/          # 状态、逐题合同、MATLAB 工具
├── templates/latex/huawei/    # 仅内部评阅
└── tests/
```

## 来源与归属

本仓库是在原开源 `mathmodel-skill` 基础上的二次开发，保留原许可证与第三方声明，详见 [`LICENSE`](LICENSE) 和 [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)。简历或作品集中应表述为“基于开源项目二次开发”，并明确自己完成的规则审计、逐题合同、MATLAB 图表和工程化改进。

## 后续扩展原则

华为杯版本完成真实多问题验证后，再扩展其他比赛。每增加一个赛事，必须独立提供：

- 当届官方规则快照与来源；
- 专用题号/题型路由；
- 专用论文标准和 AI 披露要求；
- 独立渲染与终审测试；
- 不把华为杯规则反向当作通用默认值。
