# Dynamic Ontology OSDK Prototype

创建日期：2026-07-15

本项目用于调研 Palantir Ontology SDK / OSDK、开放 OOSDK 相关资料，并设计一个可开发原型：把用户的结构化数据与非结构化数据映射到动态本体中间层，再从中间层生成面向应用和 Agent 的动态本体 SDK。

## 项目目标

1. 调研并整理 Palantir OSDK / Ontology / Ontology MCP 的公开技术资料。
2. 调研 Level Up / GitConnected 文章《Why I’m Building an Open Ontology SDK...》作者、公开 GitHub 线索与相关 OOSDK 资料。
3. 设计原型开发计划，证明动态本体 OSDK 可以暴露给 Agent，用于快速开发精确、可用的数据应用。

## 当前产物

- `FINAL_RESEARCH_REPORT.md`：面向最终计划制定者的完整综合研究报告。
- `references/source-index.md`：所有来源、下载状态、可复查链接。
- `references/palantir-osdk-research.md`：Palantir Ontology / OSDK / Ontology MCP 技术要点。
- `references/open-oosdk-author-github.md`：文章作者、候选 GitHub、OOSDK 仓库调研。
- `references/agentic-ops-research.md`：Agentic-OPS 的 Agent 编排、HITL、审计和 Ontology context 调研。
- `prototype-plan/prototype-development-plan.md`：原型架构、阶段计划、应用验证方案。
- `prototype-plan/trusted-data-product-flow-demo-plan.md`：基于可信数据产品流转 Demo 方案展开的双场景原型设计与四周开发计划。
- `specs/dynamic-ontology-ir.md`：动态本体中间表示（DOIR）初版规范。
- `examples/sample-doir.yaml`：一个简化的动态本体中间层示例。

## 已下载参考资料

- `references/raw/`：Palantir 官方页面 HTML 快照。
- `references/external/ai_mcp_multi_agent_oosdk-public/`：候选 OOSDK GitHub 仓库浅克隆。
- `references/external/Agentic-OPS/`：Agentic-OPS GitHub 仓库浅克隆。

LevelUp / Medium 文章页面可通过浏览器访问，但直接 `curl` 下载两次超时，因此未形成原始 HTML 快照；调研笔记保留了原文 URL 与访问说明。

## 建议下一步

若面向可信数据产品流转 Demo，优先从 `prototype-plan/trusted-data-product-flow-demo-plan.md` 开始，以“企业用电征信”为主线闭环，以“长春城市生命线开挖风险”为行业扩展示范。先完成 DOIR v0.2、Product Compiler、Product Service OSDK、Provider Runtime、Policy Service 和 Receipt Service 六个核心组件。
