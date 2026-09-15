# 华为杯论文格式与提交材料审计表

> 本表属于内部审计证据，不是官方模板。每个结论必须来自目标年份官方通知、
> 格式规范、标准文档、提交手册或所选题面。`unknown` 表示尚未核实；
> `not_stated` 仅能在已检查全部相关当届文件后使用。两者都不能凭经验填值。

## 审计元数据

| 字段 | 值 |
|---|---|
| 竞赛年份 | |
| 规则依据年份 | |
| 依据状态 | current_official / prior_year_provisional |
| 当届开赛公告 URL / SHA-256 | |
| 当届格式规范 URL / SHA-256 | |
| 当届标准文档 URL / SHA-256 | |
| 当届提交手册 URL / SHA-256 | |
| 所选题面路径 / SHA-256 | |
| 最终 PDF 路径 / SHA-256 | |
| 检查人和时间 | |

## 规则与成品逐项比对

状态只能填 `confirmed`、`not_stated`、`not_applicable` 或 `unknown`。
结果只能填 `pass`、`fail` 或 `blocked`。任何 `unknown`、`fail`、`blocked`
都禁止将项目标记为正式提交就绪。

| 检查项 | 状态 | 当届官方要求 | 最终成品观察值 | 来源/页码/题面锚点 | 结果 |
|---|---|---|---|---|---|
| 官方标准文档及版本 | unknown | | | | blocked |
| 封面是否保留、logo 是否可改 | unknown | | | | blocked |
| 纸张尺寸与页边距 | unknown | | | | blocked |
| 论文题目字体、字号、对齐 | unknown | | | | blocked |
| 一级标题字体、字号、对齐 | unknown | | | | blocked |
| 二级及以下标题格式 | unknown | | | | blocked |
| 中文正文字体与字号 | unknown | | | | blocked |
| 英文、数字和公式字体 | unknown | | | | blocked |
| 首行缩进、段前段后 | unknown | | | | blocked |
| 行距 | unknown | | | | blocked |
| 图题、表题、公式编号格式 | unknown | | | | blocked |
| 页眉 | unknown | | | | blocked |
| 页码起始页、位置和连续性 | unknown | | | | blocked |
| 摘要页数上限 | unknown | | | | blocked |
| 论文总页数上限 | unknown | | | | blocked |
| 正文内附录是否允许及计页方式 | unknown | | | | blocked |
| 匿名范围和身份信息位置 | unknown | | | | blocked |
| PDF 格式、压缩和文件大小 | unknown | | | | blocked |
| PDF 文件名 | unknown | | | | blocked |
| 支撑材料触发条件 | unknown | | | | blocked |
| 支撑材料内容、格式、命名、大小 | unknown | | | | blocked |
| 论文中是否需要声明支撑材料 | unknown | | | | blocked |
| AI 使用标注和额外材料 | unknown | | | | blocked |
| 所选题面的专项交付物 | unknown | | | | blocked |

## 机械检查记录

| 项目 | 观察值 | 证据 | 结果 |
|---|---|---|---|
| PDF 实际总页数 | | `pdfinfo` 或等价工具输出 | |
| 摘要实际页数 | | 人工页视图 | |
| PDF 实际文件大小 | | 文件属性 | |
| 字体嵌入/缺字 | | `pdffonts`、PDF 日志和目视检查 | |
| 页眉页码连续性 | | 逐页抽查；首尾及章节转换页必查 | |
| 封面、摘要、正文顺序 | | PDF 页面缩略图 | |
| 附录与支撑材料清单一致 | | 文件清单和题面交付物映射 | |
| 最终 PDF 与已锁定 MD5 一致 | | 官方工具输出和时间戳 | |

## 未解决项与冲突

- 未解决项：
- 官方文件之间的冲突及采用依据：
- 与仓库临时基线的冲突：
- 参赛者确认：姓名/角色、时间、结论。

