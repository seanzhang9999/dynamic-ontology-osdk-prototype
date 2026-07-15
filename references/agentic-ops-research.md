# Agentic-OPS Research

调研日期：2026-07-15  
仓库：[kingtutt52/Agentic-OPS](https://github.com/kingtutt52/Agentic-OPS)  
本地浅克隆：`references/external/Agentic-OPS/`  
克隆 commit：`5cd73d5e5b32b8baa9c4db2b1a0dce8a382ee3a0`  
GitHub 创建时间：2026-07-12

## 结论

Agentic-OPS 值得纳入本项目研究。它不是动态本体 OSDK 生成器，但已经实现了一个贴近本项目 runtime/action 层的开源 Agent 编排骨架：

- YAML-first workflow DAG。
- Ontology-aware context injection。
- Data / LLM / Action 三类 agent。
- SQL / REST connectors。
- human-in-the-loop checkpoint。
- hash-chain audit trail。
- 医疗 discharge 与财务 invoice anomaly 两个示例 workflow。

对本项目最有价值的不是它的本体建模深度，而是它把 “Agent 工作流、审批、审计、数据连接器、Ontology context” 做成了可运行的编排层。

## 仓库画像

GitHub API 描述：

> Open-source enterprise AI agent orchestration platform. Define multi-agent workflows in YAML with Ontology-aware context, audit trails, and human-in-the-loop checkpoints.

项目信息：

- 语言：Python。
- 包名：`agentic-ops`。
- 版本：`0.1.0`。
- 许可证：MIT。
- Python：`>=3.11`。
- 主要依赖：`anthropic`、`pydantic`、`sqlalchemy`、`httpx`、`pyyaml`、`click`。
- 自带测试：workflow loader、executor。

测试状态：

- 本地未运行成功，因为系统 Python 缺少 `pytest`。
- 未安装依赖，避免污染参考仓库。

## 目录结构

关键目录：

- `agentic_ops/workflow/`：workflow schema、loader、executor。
- `agentic_ops/ontology/`：ObjectType、Property、LinkType、OntologyContext、OntologyRegistry。
- `agentic_ops/agents/`：DataAgent、LLMAgent、ActionAgent。
- `agentic_ops/connectors/`：SQL 与 REST connector。
- `agentic_ops/checkpoint/`：human-in-the-loop approval。
- `agentic_ops/audit/`：append-only JSONL audit + hash chain。
- `examples/workflows/`：patient discharge、invoice anomaly detection。

## 可复用设计点

### 1. Workflow 作为本体应用层一等对象

Agentic-OPS 的 workflow YAML 包含：

- `name`
- `version`
- `description`
- `ontology_types`
- `triggers`
- `steps`
- `requires_approval`
- `on_failure`
- `timeout_seconds`

这对 DOIR 的启发是：除了 `object_types`、`link_types`、`action_types`，还应该加入 `workflow_types` 或 `automation_types`。否则我们的 OSDK 只能暴露对象和动作，缺少可复用业务流程。

### 2. DAG executor

`WorkflowExecutor` 会：

- 拓扑排序 workflow steps。
- 按 wave 并行执行无依赖步骤。
- 将上游 step output 注入下游。
- 每步执行前注入 `OntologyContext`。
- 支持 approval gate、retry、timeout、failure strategy。
- 每步完成后写 audit event。

这可以作为本项目 runtime 的参考实现：DOIR 生成的 action/workflow 不应该只是 API endpoint，也可以生成可审计的 DAG runner。

### 3. Ontology-aware context injection

Agentic-OPS 的 `OntologyContext` 将对象类型 schema 和实例数据序列化成 LLM system prompt。它支持：

- ObjectType runtime registry。
- Property type。
- Link type。
- sensitivity metadata。
- PHI / PII / SECRET redaction。

这比普通 “把 JSON 塞进 prompt” 更稳，但还没有做到完整动态本体映射。我们可以借鉴它的 context serialization 和 sensitivity model，然后把 schema 来源从手写 registry 换成 DOIR registry。

### 4. Human-in-the-loop

workflow step 可声明：

```yaml
requires_approval: true
timeout_seconds: 7200
```

Executor 在执行 action 前请求审批。这个模型适合本项目的 `action_types.safety`：

- `dry_run_required`
- `approval_required`
- `approval_role`
- `timeout_seconds`
- `audit_log`

### 5. Hash-chain audit trail

`AuditTrail` 使用 JSONL append-only 文件，并在每个 event 中写入 previous hash。它记录：

- workflow started/completed
- step completed
- approval requested/resolved
- input hash
- output hash
- actor
- tokens_used
- error

这对本项目非常重要。Agent 可用的数据应用如果要进企业场景，必须能解释“谁用什么输入触发了哪个动作，输出是什么，是否被审批”。

## 与本项目 DOIR 的差距

Agentic-OPS 当前更像 Agent orchestration framework，不是 OSDK / dynamic ontology platform：

- 没有从结构化/非结构化数据自动生成本体。
- 没有 source mapping、confidence、review status。
- 没有 SDK generator。
- 没有 MCP tool generator。
- ObjectType 是 runtime registry，不是版本化本体仓库。
- SQL query 当前用字符串模板插值，适合 demo，但生产需要参数化查询和 policy enforcement。
- ActionAgent 执行边界较宽，后续应由 DOIR action schema 和权限系统收紧。

## 对原型计划的修改建议

### 增加 `workflow_types`

DOIR 应新增：

```yaml
workflow_types:
  customerRiskReview:
    ontology_types: [Customer, Ticket, Contract, SlaTerm]
    triggers: [manual, webhook]
    steps:
      - id: fetch_customer
        uses: query.Customer.byName
      - id: find_risk_evidence
        uses: semantic.contract_sla_index
        inputs: [fetch_customer]
      - id: draft_assessment
        uses: llm.advisor
        inputs: [fetch_customer, find_risk_evidence]
      - id: escalate
        uses: action.escalateTicket
        inputs: [draft_assessment]
        requires_approval: true
```

### 把 `action_types` 分成 dry-run 与 execute

Agentic-OPS 的审批是在 step 级别做的。本项目可以更进一步：

- Agent 默认只能调用 `dry_run_*`。
- `execute_*` 需要权限和审批。
- 两者共享同一 action schema。

### 把 audit 作为 runtime 基础能力

DOIR 的 `runtime` 应声明 audit backend：

```yaml
runtime:
  audit:
    mode: hash_chain_jsonl
    include_input_hash: true
    include_output_hash: true
    include_provenance: true
```

### Agent apps 不直接编排底层 agent

Agentic-OPS 允许 workflow 中写 SQL / REST config。我们的目标更高一点：Agent 不应该看 SQL，而应看 DOIR 生成的 OSDK query/action。可以复用它的 executor，但 step 的 `uses` 应指向 OSDK 能力。

## 研究优先级

建议把 Agentic-OPS 放在本项目参考优先级第二层：

1. Palantir OSDK / Ontology / Ontology MCP：定义目标形态。
2. Agentic-OPS：参考 workflow runtime、HITL、audit、context injection。
3. SunnyLab OOSDK：参考 ontology.yaml 驱动业务策略和多 Agent 应用。

## 可落地借鉴

第一版原型可直接吸收这些概念：

- workflow YAML schema。
- topological wave executor。
- `requires_approval` gate。
- hash-chain audit JSONL。
- property sensitivity + LLM redaction。
- built-in example workflows。

但不要直接把它作为本项目核心，因为它还缺本体自动映射和 SDK 生成，这正是我们要证明的部分。
