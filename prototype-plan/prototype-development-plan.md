# Prototype Development Plan

## 原型目标

验证一个开放动态本体 OSDK 是否能做到：

1. 接收用户的结构化数据和非结构化数据。
2. 自动发现并映射到动态本体中间层 DOIR。
3. 从 DOIR 生成 OSDK：类型化查询、关系遍历、动作调用、语义检索和 MCP tools。
4. 让 Agent 基于 OSDK 快速构建精确可用的数据应用，而不是直接猜 SQL、猜字段或做松散 RAG。

## 范围选择

第一版建议限定在一个小但真实的业务域：

```text
CRM accounts + support tickets + contracts/docs
```

数据输入：

- `accounts.csv`：客户、行业、等级、ARR、owner。
- `tickets.csv`：工单、状态、优先级、客户 id、创建时间。
- `contracts/`：合同、SLA、服务条款、PDF 或 Markdown。
- `notes/`：会议纪要、客户邮件、实施记录。

目标本体：

- `Customer`
- `Ticket`
- `Contract`
- `SlaTerm`
- `AccountOwner`
- link: `Customer -> Ticket`
- link: `Customer -> Contract`
- link: `Contract -> SlaTerm`
- action: `createFollowUpTask`
- action: `escalateTicket`
- query: `customersAtRisk`
- semantic search: `findEvidenceForCustomerRisk`
- workflow: `customerRiskReview`

## 总体架构

```text
Connectors
  CSV / JSON / SQL / Markdown / PDF / Email
        |
        v
Data Profiling + Extraction
  schema profiling, entity extraction, chunking, embeddings
        |
        v
Ontology Mapping
  object candidates, field mapping, links, actions, confidence, provenance
        |
        v
DOIR Registry
  versioned ontology, policies, mappings, migrations, approvals
        |
        v
Runtime Layer
  object store + graph index + vector index + action executor
        |
        v
OSDK Generator
  TypeScript SDK + Python SDK + OpenAPI + MCP tools
        |
        v
Agent Applications
  dashboards, investigation assistant, workflow automation, data quality agent
```

## 核心模块

### 1. Data connectors

第一版支持：

- CSV / JSON：结构化表格。
- Markdown / TXT：非结构化文本。
- PDF：可选，先走文本抽取。
- SQLite / Postgres：第二阶段加入。

输出统一为 `SourceDataset` 与 `SourceDocument`：

- source id
- records / chunks
- detected schema
- lineage pointer
- update timestamp

### 2. Ontology mapper

职责：

- 从结构化字段推断对象类型与属性。
- 从外键、同名 id、值分布推断 link types。
- 从非结构化文本抽取实体、日期、义务、风险、SLA 等候选对象。
- 将候选映射到 DOIR，并给出 `confidence`、`evidence`、`review_status`。

第一版不要完全自动写入本体。采用：

```text
proposal -> validation -> human accept/reject -> versioned DOIR
```

### 3. DOIR Registry

DOIR 是动态本体的中间表示。它需要表达：

- object types
- property types
- link types
- action types
- query types
- semantic indexes
- source mappings
- permissions
- provenance
- version and migration rules

第一版用 YAML + JSON Schema 校验，后续可迁移到数据库。

### 4. Runtime layer

最小实现：

- DuckDB / SQLite：结构化对象存储。
- NetworkX 或轻量 graph table：对象关系。
- Chroma / LanceDB / pgvector：文本 chunk 与语义索引。
- Action executor：只实现 mock action 和少量真实 action。

查询能力：

- object search
- property filters
- link traversal
- aggregate
- semantic evidence search
- action dry-run / execute

### 5. Workflow runtime

参考 Agentic-OPS 的 workflow executor，把 DOIR 中的 `workflow_types` 编译成可运行 DAG：

- 支持拓扑排序与并行 wave。
- step 只能引用 DOIR 中的 query、semantic index、advisor、action。
- 支持 `requires_approval`、timeout、retry、failure policy。
- 每个 step 写 hash-chain audit event。
- LLM advisor 默认只给建议，不能直接执行写操作。

### 6. OSDK generator

第一版输出两类接口：

1. TypeScript SDK
2. MCP tool definitions

TypeScript SDK 示例：

```ts
const risky = await osdk.Customer.where({ tier: "VIP" })
  .link("tickets")
  .where({ priority: "P1", status: "open" })
  .fetch();

const evidence = await osdk.Customer.semanticSearch(customerId, {
  query: "contractual SLA breach risk",
  sources: ["contracts", "notes"],
});

await osdk.actions.escalateTicket({
  ticketId,
  reason: "VIP customer has unresolved P1 ticket over SLA",
});
```

MCP tools 示例：

- `list_object_types`
- `search_customers`
- `get_customer_tickets`
- `find_customer_risk_evidence`
- `dry_run_escalate_ticket`
- `execute_escalate_ticket`

### 7. Agent apps

用三个小应用证明 OSDK 对 Agent 有用：

1. `Customer Risk Analyst`
   - 输入客户名称。
   - Agent 用 OSDK 查客户、工单、合同条款和会议纪要。
   - 输出风险判断、证据链接、建议动作。

2. `Ticket Escalation Builder`
   - Agent 根据本体动作生成一个小工作流。
   - 只能调用 `dry_run` 和 `execute`，不能直接写数据库。
   - 展示权限、审批和审计。

3. `Ontology Change Assistant`
   - 用户上传新 CSV 或文档。
   - Agent 生成 DOIR mapping proposal。
   - 人确认后重新生成 SDK。

## 里程碑

### Week 1: Research + DOIR v0

- 完成参考资料整理。
- 写出 DOIR YAML schema。
- 定义 sample domain。
- 写出 mapping proposal 格式。

验收：

- `examples/sample-doir.yaml` 能被 schema 校验。
- 至少能表达 Customer / Ticket / Contract / SlaTerm。

### Week 2: Ingestion + mapping proposal

- CSV profiler。
- Markdown / TXT chunker。
- 简单实体抽取。
- 字段到对象/属性的映射建议。

验收：

- 给定 sample data，输出 `mapping-proposal.yaml`。
- proposal 包含 confidence 和 evidence。

### Week 3: Runtime query layer

- 加载 DOIR。
- 建立 object store、link store、vector store。
- 实现对象查询、关系遍历和语义证据检索。

验收：

- API 可以查 Customer、Ticket、Contract。
- 能回答 “某客户有哪些开放 P1 ticket，并给出合同证据”。

### Week 4: SDK + MCP generation

- 生成 TypeScript SDK。
- 生成 MCP server tools。
- 每个工具带 JSON Schema、description、权限标签。
- 生成 workflow runner 的最小适配层。

验收：

- TypeScript SDK 编译通过。
- MCP client 能列出 tools 并调用查询。
- `customerRiskReview` workflow 可以执行到 dry-run action。

### Week 5: Agent demo apps

- Customer Risk Analyst。
- Ticket Escalation Builder。
- Ontology Change Assistant。
- Customer Risk Review workflow：查询、证据检索、LLM advisor、审批后升级。

验收：

- Agent 不直接访问底层表。
- Agent 调用 OSDK / MCP 完成任务。
- 输出包含对象 id、字段来源、证据 chunk 和动作审计记录。
- Workflow 运行产生可校验 audit chain。

### Week 6: Evaluation + hardening

- 加权限模型。
- 加版本迁移。
- 加数据质量和映射准确率评估。
- 写 demo script 和技术说明。

验收：

- 新增一个字段或数据源后，SDK 可重新生成，旧应用明确知道 breaking / non-breaking change。
- Agent 任务成功率、误调用率、证据引用率有记录。

## 验证指标

- `SDK compile success`：生成 SDK 是否可编译。
- `agent task success`：Agent 是否只靠 OSDK 完成任务。
- `mapping precision`：字段/对象/关系映射准确率。
- `evidence coverage`：非结构化结论是否带来源 chunk。
- `action safety`：写操作是否经过 dry-run、权限和审计。
- `time-to-app`：新数据源到可用小应用的时间。

## 主要风险

- 自动本体发现容易过拟合字段名，需要人工确认闭环。
- 非结构化抽取可能幻觉，必须保留证据和置信度。
- 动态本体会破坏已生成 SDK，需要版本和迁移策略。
- Agent 工具过多会造成选择困难，需要按 task/context 裁剪工具。
- 权限如果只在 SDK 层做会被绕过，必须放到 runtime。

## 原型技术选型

推荐第一版：

- Python：ingestion、mapping、runtime、MCP server。
- TypeScript：生成 SDK 和 demo app。
- DuckDB 或 SQLite：本地结构化对象存储。
- Chroma 或 LanceDB：本地向量索引。
- FastAPI：runtime API。
- MCP / FastMCP：Agent 工具暴露。
- JSON Schema：DOIR 校验。
- Hash-chain JSONL：第一版审计日志。

选择理由：开发速度快，可本地跑通，不依赖大型平台，同时能贴近 Palantir OSDK 的对象/动作/工具边界思想。
