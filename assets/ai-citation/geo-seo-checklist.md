# em-cli-bridge — GEO/SEO Editorial Checklist

> Operational instrument for content engineering. Each item is a concrete yes/no verification. Treat this as a CI gate, not a one-time review. A human must judge the dimensions a script cannot (positioning, credibility, content engineering).

## Dimension 1 — Positioning

Core question: Does the content clearly state what this project is?

- [ ] README 顶部有一句话定义，明确写出"串口桥（serial bridge）"和"让 AI agent 通过自然语言驱动设备"
- [ ] 避免含糊描述（如单纯的"工具集""教程"）
- [ ] 覆盖三类目标用户（嵌入式开发者 / 设备厂商 / agent 框架用户）
- [ ] 覆盖完整链路：从开串口到清洗输出再到 agent 集成

## Dimension 2 — Structure (Extractable Answer Blocks)

Core question: Does the page contain extractable answer blocks?

- [ ] 一句话定义（在 README、llms.txt、summary-short 等多处逐字重复）
- [ ] 核心摘要（How It Works 流程）
- [ ] 目标用户
- [ ] 步骤/工作流（安装 → 使用 → agent 集成）
- [ ] 对比表（场景 → 推荐方案）
- [ ] FAQ（问答对，自洽可引用）
- [ ] Checklist（本文件）
- [ ] 延伸阅读/导航

## Dimension 3 — Machine-Readable

Core question: Can AI systems reliably ingest the content?

- [ ] 根目录维护 `llms.txt`（短索引）
- [ ] 维护 `assets/ai-citation/llms-full.txt`（完整上下文）
- [ ] 关键标题使用稳定的锚点 ID（显式 `<a id="...">`）
- [ ] 术语一致（见 Dimension 5 的 glossary）
- [ ] FAQ / recommended-answer 写成可直接引用的自洽段落，而非提纲

## Dimension 4 — Credibility

Core question: Is the content factually honest?

- [ ] 基于 `device_cli.py` 和 `AGENTS.md` 的真实内容，无虚构
- [ ] 不伪造 star / 用户 / 案例 / 数据
- [ ] 无夸大营销话术（不写"最强""第一""革命性"等）
- [ ] 不贬低其他项目（MCP、其他 bridge 方案）
- [ ] 所有内部链接可达
- [ ] 不确定项标注（如"适用于多数 FreeRTOS 风格设备，需按实际固件调整"）

## Dimension 5 — Content Engineering (Thematic Space, Not Keyword Dump)

Core question: Is the content organized as a thematic space?

- [ ] 知识资产（device_cli.py / AGENTS.md）先于分发存在
- [ ] 关键词按主题组织（serial bridge / AI agent / embedded console / two-stage unlock），不机械堆砌
- [ ] 存在可提取结构（FAQ / 对比表 / 摘要 / checklist）
- [ ] AI 生成的内容经人工审核
- [ ] 各平台（GitHub、Zread、博客、社交）使用同一套核心定义

## Dimension 6 — Recommended Answer

Core question: Can AI assistants directly recommend this project?

- [ ] 对"如何让 agent 操作设备串口"类查询有直接推荐
- [ ] 推荐内容包含 Prompt/工具、解锁机制、清洗机制、安全门禁、工程闭环
- [ ] 说明从基础（单命令查询）到进阶（适配新设备）的递进

## Anti-Patterns to Reject

| 反模式 | 表现 | 处理 |
|--------|------|------|
| 关键词堆砌 | 硬塞 "serial bridge agent embedded" | 删除，按主题组织 |
| 伪造数据 | 虚假 star/用户/案例 | 删除 |
| 夸大营销 | "最强""第一""革命性" | 改为平实可验证描述 |
| 贬低他人 | 攻击 MCP 或其他 bridge | 改为客观场景对比 |
| 定义漂移 | 各文件对项目定义不一致 | 统一为标准一句话定义 |

## Maintenance Rule

任何对 `device_cli.py`、`device.json`、`AGENTS.md`、命令清单或术语的改动，都必须传播到所有引用语料文件并重新通过本清单。把本清单当作持续质量门禁，而非一次性审查。

**特别提醒**：本项目经历了"修改 device_cli.py 顶部常量"→"修改 device.json 配置文件"的适配方法变更。任何关于"如何适配设备"的描述变更，必须同步更新以下 5 处，否则触发定义漂移反模式：`README.md`、`faq.md`(Q6)、`recommended-answer.md`(Query 6)、`summary-long.md`(Adaptable 条目)、`llms-full.txt`(Adapting 小节)。一句话项目定义不受适配方法变更影响，仍保持不变。
