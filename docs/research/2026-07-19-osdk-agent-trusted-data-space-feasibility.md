# 利用 OSDK 实现面向智能体自动化数据交易的可信数据空间创新可行性报告

**日期：2026-07-19**

## 1. 结论先行

当前 Demo 与“可信数据空间”“数据元件”“数据产品”没有方向冲突，反而可以作为可信数据空间中“数据服务化、智能体自动调用、履约可验证”的执行层增强。

更准确地说：

- 可信数据空间标准解决的是跨主体数据流通利用的基础设施框架：身份、连接器、目录、数字合约、使用控制、存证审计。
- 数据元件解决的是把原始数据加工成边界清晰、可复用、可流通的中间形态，介于原始数据资源和最终数据产品之间。
- 当前 OSDK Demo 解决的是：当数据产品从“表/文件/API”进一步变成“可执行业务动作”时，Agent 如何发现、申请、调用、跨 Provider 编排并验证执行凭证。

因此，本方案不是替代可信数据空间，也不是替代数据中台，而是可以嵌入可信数据空间和数据中台之上，成为 **面向 Agent 的可信数据产品执行与自动交易层**。

可行性判断：

1. **理论路线可行**：Apheris Gateway、Eclipse Dataspace Components、Ocean Compute-to-Data、AWS Clean Rooms、国内可信数据空间与隐私计算平台都已分别验证“数据不出域、合约控制、本地计算、多方协作、可审计”这些基础路线。
2. **当前 Demo 已验证关键闭环**：动态本体/产品投影编译、typed OSDK 生成、远程 OSDK 经 Gateway 调 Provider Runtime、多 Provider fan-out、逐 Provider Receipt、授权撤销和部分失败处理。
3. **后续主要是工程复杂度与合规安全强化**：真实数据源 adapter、持久化 Registry/Policy/Audit、强身份、密钥管理、沙箱/TEE/MPC、DSP/ODRL 兼容、交易计量计费、生产运维等。
4. **仍不能说“无风险”**：隐私泄露、推断攻击、运行时绕过、跨主体责任、审计采信、监管认可都不是 OSDK 自身能解决的，需要生产级可信数据空间工程体系承接。但这些不是“理论方向不可实现”，而是明确可分解的工程、安全和合规任务。

建议继续推进，产品定位应从“我们也做可信数据空间”调整为：

> 在可信数据空间中，为数据提供方和数据使用方提供一套面向 Agent 的数据产品自动交易与可信执行框架：把数据元件/数据产品编译成 Agent 可调用的 Product OSDK，所有调用经数字合约和 Gateway 控制，在 Provider Runtime 内完成计算，并返回可验证 Receipt。

## 2. 资料来源与取证说明

本报告参考以下资料：

- 百度百科“数据元件”：https://baike.baidu.com/item/%E6%95%B0%E6%8D%AE%E5%85%83%E4%BB%B6/58069761  
  说明：该页面在命令行抓取时返回百度安全验证，未能直接抽取正文。因此本报告将其作为“数据元件”概念入口，同时以国家数据基础设施、可信数据空间技术架构及公开产业资料作为主要可复核依据。
- 附件《可信数据空间 技术架构》，全国数据标准化技术委员会技术文件 `TC609-6-2025-01`，2025-04-30 发布。附件文件名：`ff808081-960ee580-0196-8636bb64-04ce.pdf`。官方同名 PDF URL 可按文件名访问国家数据局站点：  
  https://www.nda.gov.cn/sjj/ywpd/szkjyjcss/0430/ff808081-960ee580-0196-8636bb64-04ce.pdf
- 国家数据局《可信数据空间发展行动计划（2024-2028年）》：  
  https://www.nda.gov.cn/sjj/zwgk/zcfb/1122/20241122164142182915964_pc.html
- 国家数据局“中小微企业融资增信可信数据空间”公开案例：  
  https://www.nda.gov.cn/sjj/ywpd/sjzy/0121/20260121135536476611581_pc.html
- Palantir Ontology SDK / OSDK：  
  https://www.palantir.com/docs/foundry/ontology-sdk/overview
- Eclipse Dataspace Components：  
  https://projects.eclipse.org/projects/technology.edc
- Eclipse Dataspace Protocol：  
  https://projects.eclipse.org/projects/technology.dataspace-protocol-base/governance
- International Data Spaces Connector：  
  https://international-data-spaces-association.github.io/DataspaceConnector/Introduction
- Apheris Gateway：  
  https://www.apheris.com/docs/gateway/latest/general/introduction.html  
  https://www.apheris.com/docs/gateway/latest/general/architecture.html
- AWS Clean Rooms：  
  https://docs.aws.amazon.com/clean-rooms/latest/userguide/what-is.html
- Snowflake Data Clean Rooms：  
  https://docs.snowflake.com/en/user-guide/cleanrooms/about
- Databricks Clean Rooms：  
  https://docs.databricks.com/aws/en/clean-rooms/
- Ocean Protocol Compute-to-Data：  
  https://docs.oceanprotocol.com/developers/compute-to-data
- Dawex 数据交换和数据空间平台：  
  https://www.dawex.com/en/data-exchange-technology/interoperability/
- SecretFlow 隐语：  
  https://www.secretflow.org.cn/
- 华为云数据空间、数据交换相关产品入口：  
  https://www.huaweicloud.com/product/
- 中国电子云数据要素、数据空间相关产品入口：  
  https://www.cecloud.com/

当前 Demo 代码依据：

- `core/trusted_data_demo/gateway_app.py`
- `core/trusted_data_demo/gateway.py`
- `core/trusted_data_demo/provider_app.py`
- `core/trusted_data_demo/control_plane.py`
- `core/trusted_data_demo/runtime.py`
- `core/trusted_data_demo/osdk_generator.py`
- `generated/python/enterprise_energy_credit/enterprise_energy_credit/client.py`
- `generated/python/enterprise_energy_credit/enterprise_energy_credit/runtime.py`
- `docs/project-status-and-osdk.md`
- `docs/research/2026-07-17-data-service-landscape-and-novelty.md`

## 3. 标准语境：可信数据空间到底要求什么

附件《可信数据空间 技术架构》给出的核心定义可以概括为：

可信数据空间是基于共识规则联接多方主体、实现数据资源共享共用的数据流通利用基础设施，是数据要素价值共创的应用生态。

它的关键词不是“把数据搬到一个平台”，而是：

- **共识规则**：参与主体对数据内容、使用方式、使用次数、使用范围、使用环境等达成约定。
- **数字合约**：以数字化形式描述各方对数据流通和使用的承诺。
- **使用控制**：在传输、存储、使用和销毁环节，用技术手段保证数据使用符合合约。
- **服务平台 + 接入连接器**：服务平台负责身份、目录、合约、空间管理、使用控制、审计；接入连接器是各参与方加入空间和执行使用控制的载体。
- **数据产品为基本单元**：可信数据空间中的流通对象是数据产品，形式可以是数据库表、文件或数据 API。
- **数据服务方可加入**：算力服务、人工智能服务、数据治理服务、隐私保护计算服务、数据交易服务等都可以通过连接器接入。

标准文件中对可信数据空间服务平台提出 7 类核心能力：

1. 身份管理
2. 接入连接器管理
3. 目录管理
4. 数字合约管理
5. 可信数据空间管理
6. 数据使用控制
7. 国际空间互通网关

同时，安全要求包括数字合约完整性、合约真实性、数据安全分级、数据传输安全、数据存储安全、数据计算安全、日志存证和合规审计。

这说明可信数据空间不是单一技术产品，而是一个包含平台、连接器、合约、策略、运行环境、审计和生态角色的系统工程。

## 4. 数据元件与当前方案的关系

“数据元件”在产业语境中通常指向这样一种中间形态：

- 来源于原始数据资源。
- 经过清洗、治理、加工、标注、标准化、脱敏或融合。
- 形成边界清晰、语义明确、可复用、可组合、可流通的中间单元。
- 可进一步封装为具体数据产品或数据服务。

它解决的是“原始数据资源不能直接高效流通，最终数据产品又太场景化”的中间层问题。

当前 OSDK Demo 里的 DOIR、动态本体、产品投影和 Provider mapping，可以被理解为数据元件机制的一个“可执行语义版本”：

| 数据元件概念 | 当前 Demo 对应物 | 说明 |
| --- | --- | --- |
| 原始数据资源 | Provider 侧用电、账单、管线、监测 fixture | 当前为合成数据；生产中应替换为真实表、GIS、API |
| 加工治理规则 | DOIR L0/L1/L2 mapping、分类分级、质量规则 | 决定字段语义、敏感级别和可用方式 |
| 数据元件 | 动态本体对象、属性、Link、Query、Action | 不是单纯表字段，而是具备业务语义的可组合单元 |
| 数据产品 | ProductProjection / Product Manifest | 面向用途封装的可申请、可授权、可执行产品 |
| 数据产品接口 | Generated Product OSDK / MCP Tool / OpenAPI | Agent 和应用调用的稳定入口 |
| 数据使用证明 | ExecutionReceipt | 证明谁、基于什么合约、调用了什么版本、得到什么 hash |

因此，本方案可以利用“数据元件”概念，但不应把数据元件仅理解为“物化宽表”或“加工后数据包”。更有价值的表达是：

> 动态本体中的对象、属性、关系和动作，是面向 Agent 可执行的数据元件；Product OSDK 是把这些数据元件封装为可交易、可授权、可调用的数据产品接口。

## 5. 当前方案与可信数据空间标准的映射

```mermaid
flowchart LR
  TDS["可信数据空间服务平台"] --> ID["身份管理"]
  TDS --> CAT["目录管理"]
  TDS --> CONTRACT["数字合约管理"]
  TDS --> UC["数据使用控制"]
  TDS --> AUDIT["存证审计"]

  CONN_PROVIDER["数据提供方接入连接器"] --> PR["Provider Runtime"]
  CONN_USER["数据使用方接入连接器"] --> OSDK["Agent / Product OSDK Workload"]

  CAT --> PRODUCT["数据产品目录"]
  CONTRACT --> ENT["Entitlement / 数字合约执行许可"]
  UC --> GW["Trusted Gateway"]
  GW --> PR
  PR --> RECEIPT["Execution Receipt"]
  RECEIPT --> AUDIT
  PRODUCT --> OSDK
  OSDK --> GW
```

映射关系如下：

| 可信数据空间标准组件 | 当前 Demo 已实现/可承接部分 | 当前缺口 |
| --- | --- | --- |
| 服务平台 | `GatewayControlPlane`、产品目录、Entitlement 创建 | 缺少统一身份、连接器注册、空间管理、合约协商、计量计费 |
| 接入连接器 | `Provider Runtime` 可视为提供方连接器中的使用控制/计算执行模块 | 缺少标准连接器协议、Connector 注册、运行监测、能力适配 |
| 数字合约 | Entitlement 表达产品、用途、Provider、期限、配额、输出粒度 | 缺少正式电子签名、合同协商、ODRL/DSP 策略映射 |
| 使用控制 | Gateway preflight、Runtime consume、撤销后拒绝、输出过滤 | 缺少细粒度策略语言、持续控制、异常终止、查询预算 |
| 数据产品 | Product Manifest、Product Schema、Generated OSDK | 缺少国家/行业目录登记、产品唯一标识、价格、权益分配 |
| 数据计算环境 | Provider Runtime 本地执行产品动作 | 缺少沙箱、TEE/MPC、资源隔离、远程证明、真实数据源权限隔离 |
| 履约证明 | ExecutionReceipt、input/output hash、Ed25519 签名 | 缺少持久化、公钥体系、时间戳、第三方存证、监管采信 |
| 数据服务方 | Agent、OSDK Compiler、Gateway 可作为数据服务能力 | 缺少服务方接入、服务目录、SLA、运营流程 |

判断：当前 Demo 与可信数据空间标准是兼容关系。它实现的是标准中“数据产品安全计算、使用控制、履约证明、数据服务方能力”的一段关键执行链，而不是完整可信数据空间服务平台。

## 6. 是否存在冲突

不存在根本冲突，但有 4 个边界需要在产品叙事和后续工程中处理清楚。

### 6.1 OSDK 不是连接器标准的替代

可信数据空间标准强调接入连接器及其接口。OSDK 是应用/Agent 调用数据产品的开发接口，不应被表述为替代连接器。

更合理的定位是：

- Provider Runtime 是连接器内部或连接器旁路的受控执行环境。
- Gateway 是服务平台或空间内可信路由/使用控制模块。
- Product OSDK 是数据使用方连接器或 Agent workload 调用数据产品的 client SDK。

### 6.2 Entitlement 不是完整数字合约

当前 Entitlement 已包含产品、用途、Provider、期限、配额、输出粒度，但它不是正式数字合约。

生产中需要：

- 合同协商流程。
- 合同双方电子签名。
- 合同防篡改存储。
- ODRL 或等价策略语言。
- 合同解除、撤销、备案。
- 合同和执行凭证的关联。

### 6.3 Receipt 不是完整存证审计系统

当前 Receipt 可以证明单次调用的输入输出 hash 和 Provider 签名，但还不是可信数据空间要求的完整日志存证与合规审计。

生产中需要：

- Provider 长期身份和公钥管理。
- KMS/HSM 或等价密钥保护。
- 防篡改事件存储。
- 时间戳服务。
- 跨重启可验证。
- 审计查询和监管报送接口。

### 6.4 字段不暴露不等于隐私安全

当前 Demo 的分级编译可以让原始字段不出现在 OSDK 和输出结果里，但隐私泄露还可能来自推断攻击、重复查询、低样本聚合、模型反演等。

生产中应按场景引入：

- 最小群体阈值。
- 查询预算。
- 结果扰动或差分隐私。
- 输出审核。
- TEE、MPC、联邦学习、密态计算或数据沙箱。

## 7. 当前 Demo 已验证的技术闭环

当前最新代码已验证以下路径：

```mermaid
sequenceDiagram
  participant Agent as "Agent / 客户应用"
  participant OSDK as "Generated Product OSDK"
  participant GW as "Trusted Gateway"
  participant CP as "Gateway Control Plane"
  participant P1 as "Grid Provider Runtime"
  participant P2 as "Integrated Energy Runtime"
  participant Audit as "Receipt / Audit"

  Agent->>OSDK: "调用 compute_credit_features"
  OSDK->>GW: "POST /actions/execute，携带 providers + payload"
  GW->>CP: "校验产品合同、Provider 映射、Entitlement"
  GW->>P1: "内部调用 /internal/actions/execute"
  GW->>P2: "内部调用 /internal/actions/execute"
  P1->>Audit: "生成 input/output hash 与签名 Receipt"
  P2->>Audit: "生成 input/output hash 与签名 Receipt"
  P1-->>GW: "provider_result + receipt"
  P2-->>GW: "provider_result + receipt"
  GW-->>OSDK: "MultiProviderResult"
  OSDK-->>Agent: "typed result，银行侧自行聚合"
```

已验证能力：

1. **动态本体到产品合同**：DOIR、字段分级、产品投影编译为 Product Manifest、Schema、MCP/OpenAPI 和 Python OSDK。
2. **OSDK 远程调用**：生成的 SDK 不依赖内部 Runtime，而是经 `ProviderRuntimeClient` 调 Gateway。
3. **多 Provider fan-out**：一次 OSDK 调用携带多个 Provider binding，Gateway 并发调用多个 Runtime。
4. **Gateway 不持有数据**：Gateway 只做身份、合同、授权、路由和响应关联。
5. **Provider Runtime 本地计算**：每个 Runtime 只处理自身 provider scope。
6. **授权控制**：Entitlement 支持用途、期限、Provider、配额、撤销。
7. **输出边界**：产品结果不返回原始用电明细、缴费流水、管线精确坐标等敏感数据。
8. **执行凭证**：Provider 返回带 input/output hash、产品版本、Runtime 版本和 Ed25519 签名的 Receipt。
9. **部分失败**：某 Provider 不可用时，Gateway 返回 `partial`，成功 Provider 的结果和凭证保留。

## 8. 当前 Demo 的技术验证完整度

| 能力域 | 当前完整度 | 说明 |
| --- | --- | --- |
| 概念验证 | 高 | 已从页面叙事推进到可运行代码闭环 |
| OSDK 生成 | 中高 | typed Python SDK、ProviderBinding、多 Provider result 已实现 |
| Gateway fan-out | 中高 | HTTP 拆分、并发、部分失败、Provider routing 已实现 |
| Provider Runtime | 中 | 有本地计算与输出控制，但数据源仍是 fixture |
| Policy / Entitlement | 中 | 语义正确但内存态，缺少合同生命周期和强策略语言 |
| Receipt | 中 | 签名和 hash 成立，但密钥、存储、时间戳、监管接口仍是演示级 |
| 动态本体 Registry | 中低 | 有 Lite Registry 和编译输入，但不是生产 registry |
| 真实数据接入 | 低 | 未接真实 SQL/GIS/API 数据源 |
| 可信运行环境 | 低 | 未实现沙箱、TEE、MPC、远程证明、资源隔离 |
| 数据交易运营 | 低 | 缺少目录登记、价格、结算、合同协商、履约争议处理 |
| Agent 自动化 | 中 | OSDK/MCP 调用链成立，但 Agent 规划、审批、人机协同和异步通知未完整产品化 |

整体判断：

> 当前 Demo 已完整验证“Agent 通过 OSDK 自动调用可信数据产品”的主技术链路，但尚未完整验证“生产可信数据空间”的身份、合约、连接器、数据源、安全计算、存证审计和交易运营体系。

## 9. 与数据中台的区别和协同关系

传统数据中台通常以企业内部数据治理为中心：采集、湖仓、建模、指标、标签、API、报表。它更擅长解决“企业内部如何管好和复用数据”。

可信数据空间和本方案关注的是跨主体流通：不同组织之间如何在不完全互信的情况下完成数据产品申请、授权、使用控制、执行和审计。

二者不是替代关系：

```mermaid
flowchart TB
  DMP["数据中台 / 湖仓 / 主数据 / 指标体系"] --> ADAPTER["Provider Adapter"]
  ADAPTER --> ONTO["动态本体 / 数据元件"]
  ONTO --> PRODUCT["可信数据产品"]
  PRODUCT --> OSDK["Product OSDK / MCP Tool"]
  OSDK --> AGENT["Agent 自动化调用"]
  AGENT --> GW["可信数据空间 Gateway"]
  GW --> RUNTIME["Provider Runtime 本地计算"]
  RUNTIME --> RECEIPT["Receipt / 履约证明"]
```

关系判断：

- 数据中台可以是 Provider 侧的数据底座。
- 动态本体可以把中台中的表、指标、标签、文档、GIS、API 映射成数据元件。
- Product Compiler 可以把数据元件封装成可信数据产品。
- OSDK 可以让 Agent 和业务应用以稳定动作调用数据产品。
- Gateway/Runtime/Receipt 可以保证调用符合合约并留下履约证明。

因此，本方案不是“再做一个数据中台”，而是让数据中台中已经治理好的数据能力，进入跨组织、可授权、可审计、Agent 可自动调用的数据交易网络。

## 10. 类似公司与方案对标

| 方案 | 已有能力 | 与本方案关系 |
| --- | --- | --- |
| Apheris Gateway | 数据留在本地 Gateway，中心 Orchestrator 调度计算任务 | 拓扑最接近，证明本地 Runtime + 中心路由可行；本方案差异在动态本体产品合同和 typed OSDK |
| Eclipse Dataspace Components / Dataspace Protocol | Connector、目录、策略、合同协商、数据面/控制面分离 | 标准和基础设施对标；本方案应兼容而不是重做 |
| IDS Connector | 分散存储、语义元数据、ODRL 使用控制、应用容器 | 与可信数据空间标准理念一致；本方案补充 Agent/OSDK 执行体验 |
| AWS / Snowflake / Databricks Clean Rooms | 多方在受控环境分析，原始数据不直接暴露 | 证明“可用不可见”市场成熟；本方案更适合异构 Provider 和业务产品动作 |
| Ocean Compute-to-Data | 算法到数据侧执行，替代数据下载 | 证明计算靠近数据的交易模型；本方案更强调企业级合约、OSDK 和凭证 |
| Dawex | 数据交易、数据空间、Connector、ODRL、DSP 互操作 | 数据空间运营和交易平台成熟；本方案可作为服务型数据产品执行层 |
| Palantir OSDK | Ontology 到 typed SDK，应用调用对象和动作 | OSDK 生成思路最接近；本方案目标是开放、多 Provider、可信数据空间兼容 |
| SecretFlow 隐语 | 隐私计算、联邦学习、安全多方计算、数据流通基础能力 | 可作为 Runtime 内部隐私计算组件或数据服务方能力 |
| 华为云、中国电子云等 | 数据要素、数据空间、数据治理、云上安全与行业平台 | 可作为底层云、数据中台、连接器或数据空间平台对标/集成对象 |

结论：市场上已有大量相邻方案，所以不能把“数据不出域”“连接器”“可用不可见”当成独占创新。当前方案真正值得强调的是组合创新：

1. 动态本体和分类分级共同编译出产品 OSDK。
2. OSDK 成为 Agent 自动化数据交易和执行的编程界面。
3. Gateway 将产品动作 fan-out 到多个 Provider Runtime。
4. Provider Runtime 在本地执行并返回逐 Provider Receipt。
5. Agent 可以验证结果来源、授权、产品版本和输入输出 hash。

## 11. Agent 自动化数据交易的产品创新点

可信数据空间标准中已有“数据产品申请、合约签订、控制策略下发、数据交付、履约证明”的流程。但流程通常面向门户、连接器和人工操作。Agent 时代的增量机会是把它自动化、可编排、可验证。

建议定义如下闭环：

```mermaid
flowchart LR
  DISCOVER["发现<br/>读取产品目录和 OSDK/MCP 描述"] --> APPLY["申请<br/>按用途和 Provider 申请 Entitlement"]
  APPLY --> APPROVE["审批<br/>人工或策略引擎批准数字合约"]
  APPROVE --> EXEC["执行<br/>OSDK 经 Gateway 调 Runtime"]
  EXEC --> VERIFY["验证<br/>Receipt 验签和 hash 校验"]
  VERIFY --> SETTLE["结算<br/>计量计费、履约证明、争议处理"]
  SETTLE --> LEARN["运营改进<br/>数据运营 Agent 生成质量和供给建议"]
```

这里 Agent 的价值不是“替人点按钮”，而是：

- 自动读产品目录，发现可用数据产品。
- 自动判断需要哪些 Provider 和数据产品组合。
- 自动生成合规申请，带用途、数据主体、期限、输出粒度。
- 自动调用 OSDK，不接触 SQL、连接串和原始文件。
- 自动处理部分失败、重试、降级和补充申请。
- 自动验签 Receipt，把结果和证据交给业务系统。
- 自动驱动数据提供方侧的数据运营 Agent 改进质量、映射、上架、履约。

这与我们前面讨论的“数据交易服务数字员工部门”一致：数据提供方通常没有足够专人执行全流程，Agent 可以承担数据产品生产、质量检查、合同响应、履约监测和异常处理的协同工作。

## 12. 对 awiki.ai 的结合方向

如果 awiki.ai 希望拓展智能体网络市场，本方案可以作为一个垂直产品方向：

### 12.1 Agent 网络中的可信数据产品 Skill

将每个可信数据产品发布为 Agent Skill：

- Skill 描述产品用途、输入输出、授权要求、价格、SLA、Receipt 校验方式。
- Skill 内部绑定 Product OSDK。
- Agent 不需要理解底层数据平台，只需理解可调用的数据产品动作。

### 12.2 客户侧 Agent + 服务侧 Agent 协同

客户侧 Agent：

- 表达业务目标。
- 发现数据产品。
- 发起授权申请。
- 调用 OSDK。
- 验证 Receipt。
- 将结果写回业务流程。

服务侧 Agent：

- 辅助 Provider 上架数据产品。
- 检查数据质量。
- 维护动态本体映射。
- 处理授权审批。
- 监控履约和异常。
- 生成数据产品运营报告。

### 12.3 异步通知与交易履约

数据交易很多不是同步 API 能完成的。应引入异步事件：

- 授权申请已提交。
- Provider 需要人工审批。
- 合约已签署。
- Runtime 作业已开始。
- 部分 Provider 超时。
- Receipt 已生成。
- 计费事件已确认。

这会把 awiki.ai 的 Agent 网络从“对话和工具调用”推进到“跨组织数据交易工作流”。

## 13. 后续是否只剩工程复杂度

结论要分层说。

### 13.1 理论方向不存在明显不可实现风险

不存在明显理论不可实现风险，原因是：

- 数据留域、本地计算、中心编排已有 Apheris、Ocean、Clean Room、EDC 等成熟先例。
- Ontology 到 typed SDK 已有 Palantir OSDK 先例。
- 数字合约、ODRL、Connector、数据空间协议已有 IDS/EDC/DSP 标准和实现。
- 隐私计算、TEE、MPC、联邦学习、数据沙箱已有成熟技术路线。
- Receipt 的 hash、签名、存证、验签属于标准密码工程问题。

当前方案把这些能力组合到“Agent 可自动调用的数据产品 OSDK”上，没有违反现有技术边界。

### 13.2 但不是普通 CRUD 工程量

后续不是“写几个接口就生产可用”，而是中高复杂度工程系统：

| 工程域 | 难点 |
| --- | --- |
| 真实数据 adapter | 异构 schema、质量口径、权限边界、查询优化、GIS/文档/API 混合 |
| 策略系统 | 数字合约、ODRL、ABAC、用途控制、撤销传播、查询预算 |
| 身份体系 | 组织身份、Agent/workload 身份、mTLS/OIDC、证书轮换 |
| 运行隔离 | 容器沙箱、网络策略、资源限制、TEE/MPC 可选集成 |
| 凭证审计 | KMS/HSM、时间戳、不可变日志、监管接口、长期验签 |
| 分布式执行 | 幂等、重试、超时、部分失败、异步任务、配额 reservation/commit |
| 产品治理 | 本体版本、breaking change、Provider conformance、SDK 发布 |
| 数据交易运营 | 目录、定价、结算、分润、争议、人工审批、SLA |

因此更准确的判断是：

> 后续主要是可分解的工程、安全、合规和运营复杂度，不是理论技术路线不可实现风险。

### 13.3 需要避免的错误判断

不能说：

- “OSDK 本身很简单，所以项目没有门槛。”
- “字段不暴露就等于隐私安全。”
- “有 Receipt 就等于监管采信。”
- “能跑 Demo 就等于可信数据空间生产可用。”

应该说：

- OSDK 只是 Agent 友好的产品接口。
- 门槛在 OSDK 背后的动态本体编译、策略、Runtime、连接器、凭证和交易运营。
- Demo 已验证核心路线，生产化需要系统工程。

## 14. 推荐下一阶段实施路线

### Phase 1：可信数据空间兼容模型

目标：把现有概念映射到可信数据空间术语。

交付：

- 数据产品目录元数据：产品标识、Provider、用途、输入输出、价格、SLA。
- Entitlement 到数字合约的映射。
- Receipt 到履约证明的映射。
- Connector / Gateway / Runtime 部署角色说明。

价值：让方案可被可信数据空间客户和标准团队理解。

### Phase 2：真实数据元件与动态本体 Registry

目标：让数据元件不再只是 fixture。

交付：

- SQLite/DuckDB/GIS/REST adapter。
- Provider mapping conformance test。
- DOIR Registry 持久化、版本 diff、回滚。
- 数据元件质量报告。

价值：证明可接真实异构 Provider，而不是只跑合成数据。

### Phase 3：生产级 Gateway 和 Policy

目标：把 Demo 网关变成可信边界。

交付：

- OIDC/mTLS workload identity。
- ODRL/ABAC 策略引擎。
- Entitlement 持久化。
- 配额 reservation/commit。
- 异步 job、重试、部分失败语义。

价值：支撑真实跨主体调用。

### Phase 4：Receipt 与存证审计

目标：让执行证明可被第三方验证。

交付：

- Provider 公钥注册。
- KMS/HSM 密钥管理。
- 不可变审计日志。
- 时间戳服务。
- Receipt verifier SDK。

价值：支撑交易履约、争议处理和监管审计。

### Phase 5：Agent 自动交易工作流

目标：让 awiki.ai 的 Agent 网络进入数据交易场景。

交付：

- 产品发现 Agent。
- 授权申请 Agent。
- Provider 数据运营 Agent。
- 异步通知和人工审批。
- OSDK Skill 市场。

价值：形成与普通数据空间、数据交易平台和数据中台不同的 Agent 时代差异化入口。

## 15. 最终判断

当前方案与可信数据空间标准一致，可以利用数据元件、数据产品、连接器、数字合约、使用控制和履约证明这些概念，不存在根本冲突。

真正的创新点不在“可信数据空间”四个字，也不在 OSDK 代码生成本身，而在：

1. 用动态本体把异构数据资源组织成可执行数据元件。
2. 用产品投影和分类分级把数据元件编译成可信数据产品。
3. 用 Product OSDK/MCP 把数据产品暴露为 Agent 可调用动作。
4. 用 Gateway 和 Provider Runtime 保证原始数据不出域、按合约执行。
5. 用 Receipt 让每次调用可验证、可追溯、可结算。
6. 用 Agent 网络自动化发现、申请、执行、验证和运营。

当前 Demo 已经验证第 1 至第 5 点的最小技术闭环，第 6 点已有清晰产品方向但还需要继续实现。

因此，后续不存在明显“理论路线不可实现”的风险；主要风险是工程复杂度、生产安全、合规采信、生态接入和商业运营。只要下一阶段按可信数据空间标准补齐连接器、数字合约、真实数据 adapter、持久化审计、强身份和 Agent 工作流，本方案可以成为 awiki.ai 面向 Agent 时代数据交易市场的一个有差异化的可信数据服务产品方向。
