# 动态本体 OSDK 原型研究报告

报告日期：2026-07-15  
项目目录：`dynamic-ontology-osdk-prototype`  
面向读者：最终计划制定者、技术负责人、原型负责人  

## 1. 执行摘要

本次研究围绕一个核心问题展开：是否可以构建一个开放的动态本体中间层，将用户的结构化数据与非结构化数据映射为业务语义层，再从该语义层生成 OSDK / MCP / OpenAPI 等接口，使 Agent 能快速开发可审计、可约束、可用的数据应用。

结论是：方向成立，且已有三个强参考源可以支撑计划制定。

1. Palantir Ontology / OSDK / Ontology MCP 提供了目标形态：企业数据不应直接暴露为表、文件或任意 API，而应先变成对象、关系、动作、函数和权限受控的业务语义层，再生成 SDK 与 Agent 工具。
2. SunnyLab OOSDK 候选仓库展示了 `ontology.yaml` 驱动多 Agent 业务流程的应用形态，尤其强调“本体定义 WHAT，Agent 执行 HOW”。
3. Agentic-OPS 展示了一个开源 Agent workflow runtime：YAML DAG、Ontology context injection、HITL、hash-chain audit trail，适合成为本项目 runtime/action 层参考。

本报告建议最终计划采用“两层架构 + 三类生成物”：

- 两层架构：动态本体中间表示 DOIR + 可审计运行时 Runtime。
- 三类生成物：TypeScript/Python OSDK、MCP tools、Workflow runner。

第一版原型不应追求通用大平台，而应选择一个窄域业务场景，例如 “CRM accounts + support tickets + contracts/docs”，证明从数据接入、本体映射、SDK 生成、Agent 应用、审批和审计的闭环。

## 2. 研究目标与范围

原始目标：

1. 搜索调研 Palantir 提出的 OSDK / 动态本体 SDK 相关技术资料，并下载整理为参考资料。
2. 调研文章《Why I’m Building an Open Ontology SDK and What Palantir Got Right About AI Orchestration》的作者信息、GitHub 信息与相关 OOSDK 资料。
3. 设计一个原型开发计划：把结构化/非结构化数据映射到动态本体中间层，再将中间层映射为动态本体 OSDK，并编写简单应用证明 OSDK 可暴露给 Agent。
4. 补充研究 `kingtutt52/Agentic-OPS`，评估其是否应影响最终计划。

本报告将已有分析作为附录整合，并给出最终建议。

## 3. 关键资料与可核验 URL

### 3.1 Palantir 官方资料

- Ontology Overview: https://www.palantir.com/docs/foundry/ontology/overview/
- Ontology SDK Overview: https://www.palantir.com/docs/foundry/ontology-sdk/overview/
- Generate an OSDK for other languages: https://www.palantir.com/docs/foundry/ontology-sdk/generate-osdk-for-other-languages/
- Websocket Subscriptions: https://www.palantir.com/docs/foundry/ontology-sdk/websocket-subscriptions/
- Unsupported types: https://www.palantir.com/docs/foundry/ontology-sdk/unsupported-types/
- Ontology MCP Overview: https://www.palantir.com/docs/foundry/ontology-mcp/overview/
- Ontology MCP Sample Architecture: https://www.palantir.com/docs/foundry/ontology-mcp/sample-architecture/
- Ontology Augmented Generation: https://www.palantir.com/docs/foundry/ontology/ontology-augmented-generation/

本地快照：

- `references/raw/palantir-ontology-overview.html`
- `references/raw/palantir-osdk-overview.html`
- `references/raw/palantir-ontology-mcp-overview.html`

### 3.2 Palantir OSDK 包与代码

- TypeScript OSDK 仓库: https://github.com/palantir/osdk-ts
- `@osdk/client`: https://www.npmjs.com/package/@osdk/client
- `@osdk/api`: https://www.npmjs.com/package/@osdk/api
- `@osdk/generator`: https://www.npmjs.com/package/@osdk/generator

2026-07-15 重新核验的 npm 元数据：

| 包 | 版本 | 许可证 | 仓库 |
| --- | --- | --- | --- |
| `@osdk/client` | `2.45.0` | Apache-2.0 | https://github.com/palantir/osdk-ts |
| `@osdk/api` | `2.45.0` | Apache-2.0 | https://github.com/palantir/osdk-ts |
| `@osdk/generator` | `2.45.0` | Apache-2.0 | https://github.com/palantir/osdk-ts |

### 3.3 Open OOSDK 文章与 SunnyLab 资料

- 文章 URL: https://levelup.gitconnected.com/why-im-building-an-open-ontology-sdk-and-what-palantir-got-right-about-ai-orchestration-b68830a6b41f
- Medium 作者入口: https://medium.com/@sunnylabtv
- YouTube 入口: https://www.youtube.com/@sunnylabtv
- 候选 GitHub 用户: https://github.com/sunnylabtv-crypto
- 候选 OOSDK 仓库: https://github.com/sunnylabtv-crypto/ai_mcp_multi_agent_oosdk-public

注意：[GitHub API user sunnylabtv](https://api.github.com/users/sunnylabtv) 返回 404。GitHub 用户搜索命中 `sunnylabtv-crypto`，其仓库 README 链接 Medium `@sunnylabtv` 与 YouTube `@sunnylabtv`，因此可视为高度相关候选资料，但不应在计划文档中断言该 GitHub 用户身份已由文章页面直接确认。

候选仓库本地浅克隆：

- `references/external/ai_mcp_multi_agent_oosdk-public/`
- 当前 commit: `6400c1e5d60cbca35ca9def02cc84cf1c1b3406f`
- commit 时间：2026-07-08 20:32:39 +0900
- commit 标题：`docs: 서버 실행·테스트·데모 안내 추가 및 메타데이터 현행화`

### 3.4 Agentic-OPS

- 仓库 URL: https://github.com/kingtutt52/Agentic-OPS
- README 中提到的 related project `foundry-dev-sdk`: https://github.com/kingtutt52/foundry-dev-sdk

GitHub API 重新核验信息：

- 创建时间：2026-07-12T19:53:07Z
- pushed_at：2026-07-12T19:53:25Z
- 语言：Python
- 许可证：MIT
- 描述：Open-source enterprise AI agent orchestration platform. Define multi-agent workflows in YAML with Ontology-aware context, audit trails, and human-in-the-loop checkpoints.

本地浅克隆：

- `references/external/Agentic-OPS/`
- 当前 commit: `5cd73d5e5b32b8baa9c4db2b1a0dce8a382ee3a0`
- commit 时间：2026-07-12 13:53:22 -0600
- commit 标题：`Initial release v0.1.0 — enterprise AI agent orchestration platform`

## 4. Palantir OSDK 研究结论

Palantir 的关键思路不是给数据库包一层 SDK，而是把企业数据、业务对象、动作、函数和权限封装为 Ontology，然后基于 Ontology 生成 SDK。开发者通过 OSDK 访问 `Customer`、`Order`、`Invoice` 等业务对象，而不是直接访问表、文件、SQL 或底层 API。

从官方资料看，Ontology 至少包含这些能力：

- Object Types：业务对象类型。
- Properties：对象属性。
- Link Types：对象间关系。
- Actions：权限控制、验证和审计的写操作。
- Functions：可复用逻辑能力。
- Interfaces：跨对象类型的通用约束。
- Query / Aggregation / Subscription：查询、聚合与变更订阅。

对本项目的直接启发：

1. DOIR 不能只是 schema registry。它必须覆盖对象、关系、动作、查询、语义索引、权限、来源和审计。
2. OSDK 生成器应输出面向业务对象的 typed SDK，而不是通用 REST client。
3. Agent 不应直接看到自由 SQL 或任意向量检索。Agent 应看到被本体约束的 MCP tools 和 action dry-run / execute。
4. 写操作必须是 Action，不应让 Agent 直接写底层系统。
5. 本体变化必须版本化，否则生成 SDK 后应用会被动态 schema 静默破坏。

## 5. Open OOSDK / SunnyLab 研究结论

目标文章提出的核心主张可以概括为：Palantir 的价值在于用本体组织 AI 编排，而不是让 LLM 随意调用工具。作者提出开放 OOSDK 方向，强调用 `ontology.yaml` 描述业务对象、策略、上下文注入、事件传播和多 Agent 协作。

候选仓库 `sunnylabtv-crypto/ai_mcp_multi_agent_oosdk-public` 对计划有实际参考价值。它包含：

- `ontology/ontology.yaml`
- `mcp_server/ontology_engine`
- `mcp_server/agents`
- Salesforce / Odoo / local JSON 适配器
- Streamlit dashboard
- order-to-cash demo scripts
- hot / warm / cold memory 相关实现

其设计可复用点：

- `ontology.yaml` 作为业务策略即代码。
- 本体定义 WHAT，Agent 执行 HOW。
- 确定性业务路径优先用规则，LLM 只做 advisor。
- 重要动作走 human approval 或 deterministic fallback。
- 多源适配器可以通过 source 层切换。

差距也很明确：它更像一个 order-to-cash 多 Agent 应用展示，不是通用 OSDK 生成器。因此最终计划不能只复刻该仓库，而应吸收它的 policy-as-ontology 思路，再补齐自动映射、版本化 DOIR、SDK/MCP 生成和权限审计。

## 6. Agentic-OPS 研究结论

Agentic-OPS 与 OOSDK 的关系很有意思：它不解决“如何从数据生成本体”，但较好解决了“本体上下文如何进入 Agent workflow，以及执行如何审批和审计”。

它的关键实现模块：

- `agentic_ops/workflow/schema.py`：Pydantic workflow schema，包含 DAG steps、agent type、inputs、approval、retry、timeout。
- `agentic_ops/workflow/executor.py`：拓扑排序、并行 wave、step output 传递、HITL、audit。
- `agentic_ops/ontology/object_type.py`：ObjectType、Property、LinkType、SensitivityLevel。
- `agentic_ops/ontology/context.py`：OntologyRegistry 与 OntologyContext，负责把类型化对象注入 LLM prompt。
- `agentic_ops/audit/trail.py`：append-only JSONL audit trail + previous hash chain。
- `examples/workflows/patient_discharge.yaml`：医疗 discharge readiness workflow。
- `examples/workflows/spend_analysis.yaml`：财务 invoice anomaly workflow。

对本项目最直接的影响：

1. DOIR 应增加 `workflow_types`，把可复用业务流程作为一等对象。
2. Runtime 应支持 DAG runner、HITL、timeout、retry、failure policy。
3. Audit 应成为默认能力，第一版可采用 hash-chain JSONL。
4. Agent-facing workflow step 不应写自由 SQL，应引用 DOIR 中声明过的 query、semantic index、advisor、action。
5. Sensitivity / PHI / PII / SECRET redaction 值得纳入 DOIR property metadata。

Agentic-OPS 也有风险：

- 当前 SQL query 使用字符串模板插值，生产场景必须改为参数化查询和 policy enforcement。
- ObjectType 是 runtime registry，不是版本化本体仓库。
- ActionAgent 边界偏宽，需要由 DOIR action schema 收紧。
- 该仓库很新，GitHub 创建于 2026-07-12，成熟度仍需验证。

## 7. 目标系统建议架构

建议最终计划采用如下架构：

```text
Data Sources
  CSV / JSON / SQL / Docs / PDF / Email
        |
        v
Ingestion & Profiling
  schema profiling, document chunking, entity extraction
        |
        v
Ontology Mapping
  object proposals, field mappings, links, confidence, provenance
        |
        v
DOIR Registry
  object_types, link_types, action_types, query_types,
  semantic_indexes, workflow_types, permissions, versions
        |
        v
Runtime
  object store, graph index, vector index,
  action executor, workflow runner, audit trail
        |
        v
Generated Interfaces
  TypeScript/Python OSDK, MCP tools, OpenAPI, workflow runner
        |
        v
Agent Apps
  investigation assistant, workflow automation, data-quality agent
```

## 8. DOIR 范围建议

DOIR 是动态本体中间表示，建议第一版支持：

- `sources`：结构化和非结构化数据源。
- `object_types`：对象类型、属性、主键、字段来源、敏感级别。
- `link_types`：对象关系、基数、映射规则、置信度。
- `semantic_indexes`：非结构化文本 chunk 与对象的绑定。
- `query_types`：受约束的本体查询。
- `action_types`：dry-run / execute、审批、权限、幂等、审计。
- `workflow_types`：可复用业务流程 DAG。
- `permissions`：角色、字段级、动作级权限。
- `runtime.audit`：hash-chain JSONL 或后续可替换审计后端。
- `generation`：TypeScript SDK、Python SDK、MCP server、OpenAPI 输出配置。

示例文件：

- 本地 DOIR 规范：`specs/dynamic-ontology-ir.md`
- 本地 DOIR 示例：`examples/sample-doir.yaml`

## 9. 原型场景建议

第一版建议使用一个窄域但足够完整的场景：

```text
CRM accounts + support tickets + contracts/docs
```

输入：

- `accounts.csv`
- `tickets.csv`
- `contracts/`
- `notes/`

动态本体对象：

- `Customer`
- `Ticket`
- `Contract`
- `SlaTerm`
- `AccountOwner`

关键关系：

- `Customer -> Ticket`
- `Customer -> Contract`
- `Contract -> SlaTerm`

关键动作：

- `createFollowUpTask`
- `escalateTicket`

关键查询：

- `customersAtRisk`
- `findEvidenceForCustomerRisk`

关键 workflow：

- `customerRiskReview`：查客户、查开放高优工单、查合同证据、LLM advisor 生成风险判断、审批后升级。

该场景能同时验证结构化数据、非结构化文本、本体映射、语义证据、Agent 工具调用、审批和审计。

## 10. 开发计划建议

### 阶段 1：DOIR v0 与样例数据

目标：

- 定义 DOIR YAML schema。
- 准备 CRM/ticket/contract 样例数据。
- 写出可解析 sample DOIR。

验收：

- `sample-doir.yaml` 可校验。
- 能表达 Customer/Ticket/Contract/SlaTerm、关系、query、action、workflow。

### 阶段 2：数据接入与映射建议

目标：

- CSV profiler。
- 文档 chunker。
- 实体与字段映射 proposal。
- confidence、evidence、review_status。

验收：

- 新数据源可生成 `mapping-proposal.yaml`。
- 人工确认后进入 DOIR registry。

### 阶段 3：Runtime 查询层

目标：

- 本体对象查询。
- link traversal。
- semantic evidence search。
- action dry-run。

验收：

- 能回答 “某客户有哪些开放 P1 ticket，并给出合同/SLA 证据”。

### 阶段 4：OSDK / MCP / Workflow 生成

目标：

- 生成 TypeScript OSDK。
- 生成 MCP tools。
- 生成 workflow runner adapter。

验收：

- SDK 编译通过。
- MCP client 可调用本体查询。
- `customerRiskReview` workflow 可运行到 dry-run action。

### 阶段 5：Agent 应用

目标：

- Customer Risk Analyst。
- Ticket Escalation Builder。
- Ontology Change Assistant。

验收：

- Agent 不直接访问底层表。
- Agent 只调用 OSDK / MCP / workflow。
- 输出包含对象 id、证据 chunk、字段来源、动作审计。

### 阶段 6：安全与评估

目标：

- 权限模型。
- 版本迁移。
- audit chain verify。
- 映射准确率、证据覆盖率、任务成功率评估。

验收：

- breaking / non-breaking ontology change 可识别。
- workflow 审计链可校验。
- 误调用和无证据结论可统计。

## 11. 技术选型建议

第一版建议：

- Python：ingestion、mapping、runtime、MCP server。
- TypeScript：生成 SDK 与 demo app。
- DuckDB 或 SQLite：本地结构化对象存储。
- Chroma / LanceDB / pgvector：语义索引。
- FastAPI：runtime API。
- MCP / FastMCP：Agent 工具暴露。
- JSON Schema：DOIR 校验。
- Hash-chain JSONL：审计日志。

设计原则：

- 先本地闭环，不先上复杂分布式平台。
- 先 narrow domain，不先追求所有行业通用。
- 先强约束工具，不直接暴露 SQL/RAG 给 Agent。
- 先 dry-run，再 execute。
- 先证据与审计，再自动化规模化。

## 12. 风险与缓解

| 风险 | 影响 | 缓解 |
| --- | --- | --- |
| 自动本体发现误判 | SDK 和应用建立在错误对象/关系上 | proposal -> human review -> versioned DOIR |
| 非结构化抽取幻觉 | Agent 输出无证据判断 | evidence chunk、confidence、source pointer 必填 |
| 动态本体破坏已生成应用 | 生产应用不稳定 | semantic version、migration、breaking change 检测 |
| Agent 工具过多 | 工具选择错误 | 按 workflow/task 裁剪 MCP tools |
| 写操作风险 | 误写业务系统 | dry-run、approval、idempotency、audit |
| 权限只在 SDK 层 | 可绕过 | runtime 强制权限 |
| 参考仓库成熟度不足 | 误判可复用性 | 只吸收架构模式，不直接依赖其代码作为核心 |

## 13. 最终建议

建议最终计划把项目定位为：

> 开放动态本体 OSDK 原型：从用户数据生成版本化业务本体中间层，并从该中间层生成受权限和审计约束的 SDK、MCP tools 与 workflow runtime，使 Agent 能快速构建精确、可追溯的数据应用。

不要把它定位成单纯的 RAG 平台、单纯的 workflow 引擎、单纯的 ORM 或单纯的 agent framework。它的差异化应是：

- 数据到业务本体的动态映射。
- 本体到 SDK/MCP/workflow 的生成。
- Agent 只能在本体边界内操作。
- 所有结论有证据，所有写操作有审批和审计。

优先级建议：

1. 先实现 DOIR 和本地 runtime。
2. 再实现 TypeScript SDK 与 MCP tool generator。
3. 再实现 workflow runner 和 HITL/audit。
4. 最后做多数据源、多租户和复杂权限。

## 附录 A：Palantir OSDK 分析报告

来源：

- https://www.palantir.com/docs/foundry/ontology/overview/
- https://www.palantir.com/docs/foundry/ontology-sdk/overview/
- https://www.palantir.com/docs/foundry/ontology-mcp/overview/
- https://github.com/palantir/osdk-ts

本地分析文件：

- `references/palantir-osdk-research.md`

摘要：

Palantir OSDK 的核心是基于 Ontology 生成面向业务对象的 SDK。Ontology 将底层数据和业务逻辑组织为对象、属性、关系、动作、函数和接口。Ontology MCP 进一步说明本体可以作为 Agent 工具边界，通过 MCP 暴露给 LLM 客户端。本项目应复刻这种“本体作为 Agent 操作边界”的思想，而不是只做数据访问 SDK。

## 附录 B：Open OOSDK / SunnyLab 分析报告

来源：

- https://levelup.gitconnected.com/why-im-building-an-open-ontology-sdk-and-what-palantir-got-right-about-ai-orchestration-b68830a6b41f
- https://medium.com/@sunnylabtv
- https://www.youtube.com/@sunnylabtv
- https://github.com/sunnylabtv-crypto
- https://github.com/sunnylabtv-crypto/ai_mcp_multi_agent_oosdk-public

本地分析文件：

- `references/open-oosdk-author-github.md`

摘要：

Open OOSDK 文章和候选仓库提供了一个有价值的方向：业务策略可以写入 `ontology.yaml`，让本体驱动多 Agent 协作。候选仓库展示了 order-to-cash 的多 Agent 应用，但不是通用 OSDK 生成器。本项目应吸收其 policy-as-ontology、WHAT/HOW 分层、LLM advisor 边界，而不是只复制其业务 demo。

## 附录 C：Agentic-OPS 分析报告

来源：

- https://github.com/kingtutt52/Agentic-OPS
- https://github.com/kingtutt52/foundry-dev-sdk

本地分析文件：

- `references/agentic-ops-research.md`

摘要：

Agentic-OPS 对本项目最有价值的是 runtime/action 层：YAML workflow DAG、Ontology context injection、HITL、hash-chain audit。它不是动态本体 OSDK 生成器，但非常适合作为 workflow runtime 的设计参考。本项目应引入 `workflow_types`、hash-chain audit、step-level approval，同时避免让 workflow 直接暴露自由 SQL。

## 附录 D：来源索引与下载状态

本地文件：

- `references/source-index.md`

已下载：

- Palantir Ontology Overview HTML 快照。
- Palantir OSDK Overview HTML 快照。
- Palantir Ontology MCP Overview HTML 快照。
- SunnyLab OOSDK 候选仓库浅克隆。
- Agentic-OPS 仓库浅克隆。

未下载：

- LevelUp / Medium 文章原始 HTML。原因：`curl` 两次超时；页面 URL 可浏览，因此保留 URL 作为核验入口。

## 附录 E：DOIR 规范与样例

本地文件：

- `specs/dynamic-ontology-ir.md`
- `examples/sample-doir.yaml`

当前 DOIR 包含：

- `sources`
- `object_types`
- `link_types`
- `semantic_indexes`
- `query_types`
- `workflow_types`
- `action_types`
- `permissions`
- `generation`
- `runtime.audit`

`examples/sample-doir.yaml` 已通过 YAML 解析校验。

## 附录 F：原型开发计划

本地文件：

- `prototype-plan/prototype-development-plan.md`

计划重点：

- Week 1：DOIR v0。
- Week 2：ingestion + mapping proposal。
- Week 3：runtime query layer。
- Week 4：SDK + MCP + workflow runner。
- Week 5：Agent demo apps。
- Week 6：evaluation + hardening。

## 附录 G：核验命令摘要

本次报告生成前重新核验：

```bash
npm view @osdk/client name version license repository.url homepage bugs.url --json
npm view @osdk/api name version license repository.url homepage bugs.url --json
npm view @osdk/generator name version license repository.url homepage bugs.url --json
curl --max-time 20 -s https://api.github.com/repos/kingtutt52/Agentic-OPS
curl --max-time 20 -s https://api.github.com/repos/sunnylabtv-crypto/ai_mcp_multi_agent_oosdk-public
git -C references/external/Agentic-OPS log -1 --format=%H%n%ci%n%s
git -C references/external/ai_mcp_multi_agent_oosdk-public log -1 --format=%H%n%ci%n%s
ruby -e 'require "yaml"; YAML.load_file("examples/sample-doir.yaml")'
```

核验结果：

- `@osdk/client`、`@osdk/api`、`@osdk/generator` 版本均为 `2.45.0`。
- Agentic-OPS commit 为 `5cd73d5e5b32b8baa9c4db2b1a0dce8a382ee3a0`。
- SunnyLab OOSDK 候选仓库 commit 为 `6400c1e5d60cbca35ca9def02cc84cf1c1b3406f`。
- `examples/sample-doir.yaml` 解析成功。
