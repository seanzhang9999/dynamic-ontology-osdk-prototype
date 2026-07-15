# Source Index

调研日期：2026-07-15  
网络来源分为三类：官方资料、包/代码资料、相关文章与候选 OOSDK 资料。

## Palantir 官方资料

| 来源 | 用途 | 本地快照 |
| --- | --- | --- |
| [Palantir Ontology Overview](https://www.palantir.com/docs/foundry/ontology/overview/) | Ontology 概念、对象、链接、动作、函数、接口方式 | `references/raw/palantir-ontology-overview.html` |
| [Ontology SDK Overview](https://www.palantir.com/docs/foundry/ontology-sdk/overview/) | OSDK 能力边界、语言支持、生成客户端 | `references/raw/palantir-osdk-overview.html` |
| [Generate an OSDK for other languages](https://www.palantir.com/docs/foundry/ontology-sdk/generate-osdk-for-other-languages/) | 说明 OSDK 可基于 Ontology 元数据和 OpenAPI 生成其他语言 SDK | 未单独下载，已记录链接 |
| [Websocket Subscriptions](https://www.palantir.com/docs/foundry/ontology-sdk/websocket-subscriptions/) | 订阅对象变更、动作/函数完成等事件 | 未单独下载，已记录链接 |
| [Unsupported types](https://www.palantir.com/docs/foundry/ontology-sdk/unsupported-types/) | OSDK 不支持类型与建模边界 | 未单独下载，已记录链接 |
| [Ontology MCP Overview](https://www.palantir.com/docs/foundry/ontology-mcp/overview/) | 把 Ontology 暴露为 MCP 服务，面向 LLM/Agent | `references/raw/palantir-ontology-mcp-overview.html` |
| [Ontology MCP Sample Architecture](https://www.palantir.com/docs/foundry/ontology-mcp/sample-architecture/) | Client/Server、语义检索、Action 调用、对象查询架构 | 未单独下载，已记录链接 |
| [Ontology Augmented Generation](https://www.palantir.com/docs/foundry/ontology/ontology-augmented-generation/) | 用 Ontology 支撑生成式 AI 的上下文与工具调用 | 未单独下载，已记录链接 |

## Palantir OSDK 包与代码

| 来源 | 核验结果 |
| --- | --- |
| [palantir/osdk-ts](https://github.com/palantir/osdk-ts) | npm 元数据指向的 TypeScript OSDK 仓库 |
| [@osdk/client](https://www.npmjs.com/package/@osdk/client) | `npm view` 核验版本 `2.45.0`，Apache-2.0，repo `palantir/osdk-ts` |
| [@osdk/api](https://www.npmjs.com/package/@osdk/api) | `npm view` 核验版本 `2.45.0`，Apache-2.0，repo `palantir/osdk-ts` |
| [@osdk/generator](https://www.npmjs.com/package/@osdk/generator) | `npm view` 核验版本 `2.45.0`，Apache-2.0，repo `palantir/osdk-ts` |

## Open OOSDK / 作者相关资料

| 来源 | 状态 | 本地材料 |
| --- | --- | --- |
| [Why I’m Building an Open Ontology SDK...](https://levelup.gitconnected.com/why-im-building-an-open-ontology-sdk-and-what-palantir-got-right-about-ai-orchestration-b68830a6b41f) | 页面可浏览；`curl` 直接下载两次超时 | 无原始快照 |
| [Medium @sunnylabtv](https://medium.com/@sunnylabtv) | 文章页署名入口 | 链接记录 |
| [YouTube @sunnylabtv](https://www.youtube.com/@sunnylabtv) | 候选 OOSDK 仓库 README 链接的 SunnyLab 资料 | 链接记录 |
| [sunnylabtv-crypto/ai_mcp_multi_agent_oosdk-public](https://github.com/sunnylabtv-crypto/ai_mcp_multi_agent_oosdk-public) | 与文章主题高度相关的公开 OOSDK 候选仓库 | `references/external/ai_mcp_multi_agent_oosdk-public/` |
| [GitHub user sunnylabtv-crypto](https://github.com/sunnylabtv-crypto) | GitHub 用户搜索命中；不能仅凭此断言就是文章作者，但 README 链接到 Medium `@sunnylabtv` | 链接记录 |
| [kingtutt52/Agentic-OPS](https://github.com/kingtutt52/Agentic-OPS) | 企业 Agent 编排框架，YAML workflow、Ontology context、HITL、audit trail；适合参考 runtime/action 层 | `references/external/Agentic-OPS/` |

## GitHub 查询记录

- `https://api.github.com/users/sunnylabtv` 返回 404。
- GitHub 用户搜索 `sunnylabtv` 命中 `sunnylabtv-crypto`。
- `sunnylabtv-crypto` 公开仓库中包含 `ai_mcp_multi_agent_oosdk-public`，README 明确链接 Medium `@sunnylabtv` 与 YouTube `@sunnylabtv`。
- GitHub 仓库搜索 `Open Ontology SDK`、`OOSDK ontology`、`OOSDK: Open Ontology SDK` 未发现其他明确匹配仓库。
- GitHub code search REST 接口未认证时返回 401，因此未能做全站代码搜索。

## 下载状态

已成功下载：

- `palantir-ontology-overview.html`
- `palantir-osdk-overview.html`
- `palantir-ontology-mcp-overview.html`
- 候选 OOSDK 仓库浅克隆
- Agentic-OPS 仓库浅克隆，commit `5cd73d5e5b32b8baa9c4db2b1a0dce8a382ee3a0`

未成功下载：

- LevelUp / Medium 文章原始 HTML。原因：`curl` 两次超时。已保留公开 URL，并基于浏览器可访问内容整理摘要。
