# Palantir OSDK / Dynamic Ontology Research

调研日期：2026-07-15

## 一句话结论

Palantir 的 OSDK 不是传统数据库 SDK，而是围绕 Ontology 生成的类型化业务对象 SDK：开发者通过对象、链接、动作、函数、查询和订阅来访问企业语义层，而不是直接访问底层表、API 或文件。

## Ontology 的关键抽象

根据 Palantir 官方 Ontology 文档，Ontology 把底层数据、业务逻辑和操作能力组织为应用可用的语义层。关键构件包括：

- `Object Types`：业务实体，例如 Customer、Order、Asset、Invoice。
- `Properties`：对象字段，可来自数据集、函数或计算逻辑。
- `Link Types`：对象之间的关系，例如 Customer -> Order。
- `Actions`：可被权限控制、验证和审计的业务写操作。
- `Functions`：可被应用、自动化、Agent 调用的逻辑能力。
- `Interfaces`：跨对象类型的通用能力约束。

这对本项目的启发是：动态本体中间层不应该只是 schema registry，而应同时表达对象、关系、动作、查询、权限、来源与可解释性。

## OSDK 的公开能力

Palantir Ontology SDK Overview 描述的核心能力包括：

- 从 Ontology 自动生成客户端 SDK。
- 用 SDK 对对象执行搜索、聚合、读取、创建、修改、删除等操作。
- 运行 Ontology Action 与 Function。
- 支持 TypeScript、Python、Java，并可通过 OpenAPI / Ontology Metadata API 生成其他语言 SDK。
- TypeScript OSDK 生态对应 `@osdk/client`、`@osdk/api`、`@osdk/generator` 等包。

截至 2026-07-15，npm registry 核验：

- `@osdk/client`：`2.45.0`
- `@osdk/api`：`2.45.0`
- `@osdk/generator`：`2.45.0`
- 许可证：Apache-2.0
- 仓库：[palantir/osdk-ts](https://github.com/palantir/osdk-ts)

## 动态本体与 OSDK 的关系

Palantir 的路径可以抽象为：

```text
Data + Business Logic
        ->
Ontology semantic layer
        ->
Generated OSDK
        ->
Applications / automations / agents
```

本项目要做的是开放版路径：

```text
Structured + unstructured user data
        ->
Dynamic Ontology Intermediate Representation (DOIR)
        ->
Generated OSDK + MCP tools + OpenAPI
        ->
Agent-built precise data apps
```

关键差异在于：我们不能假设数据已经进入 Foundry，也不能假设本体由人工长期建模完成。因此需要加入自动发现、映射建议、人工确认、版本演化、数据血缘和置信度。

## Ontology MCP 的启发

Palantir Ontology MCP 文档说明，Ontology 可以通过 MCP Server 暴露给支持 MCP 的客户端，使 LLM/Agent 能调用对象查询、语义搜索、Action 和 Function。

这给本项目一个明确验证路线：生成 OSDK 的同时生成 MCP tool descriptors。Agent 不直接猜 SQL 或调用底层系统，而是只看到经过本体约束的工具：

- `search_customers`
- `get_customer_orders`
- `create_follow_up_task`
- `summarize_evidence_for_case`
- `resolve_duplicate_entities`

每个工具都带类型、权限、输入约束、输出 schema 和 provenance。

## 对原型设计的直接要求

1. 中间层必须支持对象类型、属性、链接、动作、查询和语义索引。
2. 每个字段和关系都必须带来源、映射规则、置信度和验证状态。
3. OSDK 生成器至少要输出 TypeScript SDK、Python SDK 或 MCP tools 中的两类，便于证明跨使用场景。
4. Agent-facing 接口要比通用 SQL/RAG 更窄、更强约束，减少幻觉和误操作。
5. 动态本体更新必须版本化，不能让已生成应用被静默破坏。

## 需要继续深挖的问题

- `palantir/osdk-ts` 中 generator 的实际输入元数据格式与可复用边界。
- Python / Java OSDK 是否有公开源仓库或仅公开文档。
- Ontology MCP 对语义检索、工具选择、Action 审批的默认约束是否可复刻。
- OSDK 的 permission / security model 在开放版中如何映射到租户、角色和字段级权限。
