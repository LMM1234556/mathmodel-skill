# 华为杯论文内容骨架

> 这是内部内容组织，不是 2026 官方格式。2025 官方格式规则可用于预排版
> 和匿名检查，但不得据此标记 2026 提交就绪；开赛后必须把内容装配到研创网
> 发布的当届《竞赛论文标准文档》中。

| 工作区文件 | 内容职责 |
|---|---|
| `01_abstract.md` | 从已验证 Claim ID 写成的摘要与关键词 |
| `02_problem_restate.md` | 研究对象、范围、题面 Requirement 与交付物 |
| `03_analysis.md` | 子问依赖、难点、数据接口与技术路线 |
| `04_assumptions.md` | 假设、依据、影响范围和验证动作 |
| `05_notation.md` | 符号、索引、单位与数据字段 |
| `06_models.md` | 逐问模型、求解、结果、图表、解释与边界 |
| `07_sensitivity.md` | 验证、稳健性、不确定性与失效区域 |
| `08_evaluation.md` | 优点、局限、改进代价、推广和最终建议 |
| `09_references.md` | 正文实际引用且已核验的来源 |
| `10_appendix.md` | 仅供内部评阅的条件式附录草稿；当届规则或题面允许/要求时才进入正式论文 |
| `supporting_materials_manifest.md` | 单独上传文件的名称、内容、哈希、大小、题面依据和论文引用位置；默认不进入论文 |

不得因为内部渲染器存在 `10_appendix.md` 就推定正式 PDF 允许附录，也不得把
单独上传的程序或计算结果自动并入正文。内部还需维护：`claim_evidence_matrix.md`、`reverse_outline.md`、
`figures/figure_registry.json`。这些文件默认不进入论文，但用于终审反向追踪。
