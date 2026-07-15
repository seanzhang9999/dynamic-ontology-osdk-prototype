# Dynamic Ontology Intermediate Representation (DOIR) v0

DOIR 是本项目的核心中间层。它不是数据库 schema，也不是单纯的知识图谱 ontology，而是把数据来源、业务对象、关系、动作、语义索引、权限和证据合在一起的可生成 SDK 规范。

## 设计原则

1. `Ontology first`：应用和 Agent 只依赖本体对象，不依赖底层表名、文件名或 API。
2. `Source aware`：每个对象、字段、关系都能追溯到来源。
3. `Confidence aware`：自动映射必须记录置信度和人工审核状态。
4. `Action bounded`：写操作只能通过声明式 action 暴露。
5. `Versioned`：本体演化必须明确 breaking / non-breaking。
6. `Agent-safe`：所有可暴露给 Agent 的能力必须有 schema、权限、描述和审计策略。

## 顶层结构

```yaml
ontology:
  id: customer-support-demo
  version: 0.1.0
  display_name: Customer Support Demo

sources: []
object_types: {}
link_types: {}
action_types: {}
query_types: {}
workflow_types: {}
semantic_indexes: {}
permissions: {}
runtime: {}
generation: {}
```

## Source

描述数据来源和抽取方式。

```yaml
sources:
  accounts_csv:
    kind: csv
    path: data/accounts.csv
    primary_key: account_id
    refresh: manual
    owner: sales_ops
```

非结构化来源：

```yaml
sources:
  contracts_folder:
    kind: document_folder
    path: data/contracts
    chunking:
      strategy: heading_and_window
      max_tokens: 800
    extraction:
      entities:
        - Customer
        - SlaTerm
```

## Object Type

```yaml
object_types:
  Customer:
    display_name: Customer
    primary_key: customer_id
    source_mapping:
      source: accounts_csv
      key: account_id
      confidence: 0.98
      review_status: accepted
    properties:
      customer_id:
        type: string
        required: true
        source_field: account_id
      name:
        type: string
        source_field: account_name
      tier:
        type: enum
        values: [VIP, Standard, Trial]
        source_field: tier
```

## Link Type

```yaml
link_types:
  CustomerTickets:
    from: Customer
    to: Ticket
    cardinality: one_to_many
    mapping:
      left_field: Customer.customer_id
      right_field: Ticket.customer_id
      confidence: 0.95
      review_status: accepted
```

## Action Type

Action 是可审计、可权限控制的写操作或外部系统调用。

```yaml
action_types:
  escalateTicket:
    display_name: Escalate ticket
    input:
      ticket_id: { type: string, required: true }
      reason: { type: string, required: true }
    output:
      escalation_id: { type: string }
      status: { type: string }
    executor:
      kind: mock
      idempotency_key: ticket_id
    safety:
      dry_run_required: true
      approval_required: true
      audit_log: true
    permissions:
      roles: [support_manager, agent_runtime]
```

## Query Type

Query 是经过本体命名和约束的查询能力。

```yaml
query_types:
  customersAtRisk:
    returns: Customer[]
    parameters:
      min_open_p1_tickets: { type: number, default: 1 }
      include_contract_evidence: { type: boolean, default: true }
    plan:
      - filter: Ticket.priority == "P1" and Ticket.status != "closed"
      - traverse: Ticket -> Customer
      - semantic_evidence: contract_sla_index
```

## Workflow Type

Workflow Type 表达可复用业务流程。它借鉴 Agentic-OPS 的 YAML-first DAG，但 step 不应直接暴露自由 SQL；step 应引用 DOIR 中声明过的 query、action、semantic index 或 advisor。

```yaml
workflow_types:
  customerRiskReview:
    ontology_types: [Customer, Ticket, Contract, SlaTerm]
    triggers: [manual, webhook]
    steps:
      - id: find_customer
        uses: query.Customer.byName
      - id: find_open_tickets
        uses: query.Ticket.openByCustomer
        inputs: [find_customer]
      - id: find_contract_evidence
        uses: semantic.contract_sla_index
        inputs: [find_customer]
      - id: draft_risk_assessment
        uses: advisor.customerRisk
        inputs: [find_customer, find_open_tickets, find_contract_evidence]
      - id: escalate_ticket
        uses: action.escalateTicket
        inputs: [draft_risk_assessment]
        requires_approval: true
    failure_policy:
      default: stop
      optional_steps:
        - find_contract_evidence
```

## Semantic Index

```yaml
semantic_indexes:
  contract_sla_index:
    source: contracts_folder
    object_scope: Contract
    chunk_to_object:
      object_type: Contract
      key_extractor: contract_id
    metadata:
      - customer_id
      - document_id
      - page
      - section
```

## Generation

声明要生成的 SDK 与 Agent 工具。

```yaml
generation:
  typescript:
    package_name: "@demo/customer-support-osdk"
    output: generated/ts
  mcp:
    server_name: customer-support-osdk
    output: generated/mcp
    expose:
      - query_types
      - safe_actions
      - semantic_indexes
```

## 版本策略

建议规则：

- 新增 object type：minor。
- 新增 optional property：minor。
- 删除 property：major。
- 修改 property type：major。
- 新增 action：minor。
- 修改 action input required field：major。
- source mapping confidence 变化：patch 或 metadata-only。

## Agent 暴露约束

给 Agent 的工具描述必须包含：

- tool name
- natural language description
- input JSON Schema
- output JSON Schema
- permission tag
- dry-run / approval requirement
- provenance behavior
- examples

不要把自由 SQL、自由文件读取、无限制 vector search 直接暴露给 Agent。

## Audit

Runtime 应默认记录 workflow、query 和 action 审计事件。第一版可采用 hash-chain JSONL：

```yaml
runtime:
  audit:
    mode: hash_chain_jsonl
    include_input_hash: true
    include_output_hash: true
    include_provenance: true
```
