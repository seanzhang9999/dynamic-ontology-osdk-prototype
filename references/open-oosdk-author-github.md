# Open OOSDK Article / Author / GitHub Research

调研日期：2026-07-15

## 文章

目标文章：

[Why I’m Building an Open Ontology SDK and What Palantir Got Right About AI Orchestration](https://levelup.gitconnected.com/why-im-building-an-open-ontology-sdk-and-what-palantir-got-right-about-ai-orchestration-b68830a6b41f)

页面显示作者为 Sunny Park，Medium handle 为 `@sunnylabtv`。文章核心观点是：Palantir 的关键价值不是“让 AI 到处运行”，而是把 AI 放在业务本体、对象、权限和动作边界内进行编排。作者提出 Open Ontology SDK / OOSDK 的方向，强调用 `ontology.yaml` 描述业务对象、规则、上下文注入、事件传播和多 Agent 协作。

## 文章中的技术主张

文章提出的 OOSDK 方向可以归纳为：

- 用 `ontology.yaml` 定义业务策略、对象、规则与 Agent 协作。
- `OntologyEngine` 在运行时读取本体，做策略判断和上下文注入。
- 三层内存：hot / warm / cold，用来区分即时上下文、可检索上下文和长期记录。
- Agent 不直接拥有全局业务上下文，而是通过本体获得受约束的上下文。
- 业务流程变化优先改本体配置，而不是改 Agent 代码。
- Agent 适合处理不确定判断，确定性业务路径应由规则和动作完成。

对本项目的启发：开放版 OSDK 需要把 “schema + policy + tool boundary + memory policy + provenance” 合在一个中间层里，而不仅是生成 CRUD client。

## GitHub 归因状态

已核验：

- `https://api.github.com/users/sunnylabtv` 返回 404。
- GitHub 用户搜索 `sunnylabtv` 命中 `sunnylabtv-crypto`。
- `sunnylabtv-crypto` 的公开仓库里有 `ai_mcp_multi_agent_oosdk-public`。
- 该仓库 README 末尾署名为 SunnyLab，并链接 Medium `@sunnylabtv` 与 YouTube `@sunnylabtv`。

谨慎结论：

`sunnylabtv-crypto/ai_mcp_multi_agent_oosdk-public` 与文章/作者系列高度相关，但由于文章页面本身没有直接给出 GitHub 链接，本项目将其标记为“候选关联 GitHub 资料”，不把 GitHub 用户身份当作完全确认事实。

## 候选 OOSDK 仓库

仓库：

[sunnylabtv-crypto/ai_mcp_multi_agent_oosdk-public](https://github.com/sunnylabtv-crypto/ai_mcp_multi_agent_oosdk-public)

本地浅克隆：

`references/external/ai_mcp_multi_agent_oosdk-public/`

仓库关键信息：

- 主题：Ontology-Oriented Multi-Agent Platform。
- 核心配置：`ontology/ontology.yaml`。
- 技术栈：Python、MCP / FastMCP、Streamlit、ChromaDB、Salesforce、Odoo、Docker、Google Cloud。
- 架构：Ontology Engine 决定 WHAT，Domain Agents 执行 HOW。
- 业务示例：Lead -> Quote -> Order / Inventory -> Ship -> Invoice -> Collect。
- Agent 边界：多数路径用确定性策略，只把 partial shipment、dunning、replenishment 等不确定判断交给 LLM advisor。
- 工程结构：`mcp_server/ontology_engine`、`mcp_server/agents`、`ontology/ontology.yaml`、`dashboard_modules`、`scripts`、`tests`。

## 可复用设计点

1. `ontology.yaml` 作为业务策略即代码：对象类型、数据源、规则和 agent delegation 都在 YAML 中。
2. “WHAT / HOW” 分层：Ontology 定义策略和路由，Agent 执行动作。
3. Caged LLM advisor：LLM 只输出建议，重要动作仍需规则 fallback 或人工审批。
4. 多源适配器：Salesforce / Odoo / local JSON 可以在 source 层切换。
5. 三层内存：hot / warm / cold 适合作为本项目非结构化上下文与长期证据管理的参考。

## 与本项目目标的差距

候选仓库更像是一个面向 order-to-cash 的多 Agent 应用展示，不是通用 OSDK 生成器。因此本项目需要补齐：

- 从任意结构化/非结构化数据自动发现本体候选。
- 本体中间表示 DOIR 的版本管理和校验。
- 从 DOIR 自动生成 TypeScript / Python SDK。
- 从 DOIR 自动生成 MCP tools / OpenAPI。
- 面向 Agent 的权限、审计、字段来源和置信度暴露。

## 相关仓库线索

`sunnylabtv-crypto` 还包含若干 MCP / agent 相关公开仓库，包括：

- `ai_mcp_fastmcp`
- `ai_mcp_fastmcp_remote-public`
- `ai_mcp_langgraph-public`
- `ai_mcp_multi_agent-public`
- `ai_mcp_multi_agent_oosdk-public`
- `ai_web_orchestrator_adk-public`

当前项目优先克隆并整理 `ai_mcp_multi_agent_oosdk-public`，因为它名称和 README 均直接对应 OOSDK。
