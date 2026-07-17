# 数据服务与数据交易方案对标：新颖性和门槛评估

**调研快照：2026-07-17**

## 1. 结论先行

这个原型有清晰的产品方向，但不应把“数据不出域”“Gateway 调用本地 Runtime”或“多 Provider 联邦执行”单独宣传为技术首创。Apheris、Ocean Protocol、数据空间 Connector、Clean Room 等方案已经分别覆盖这些能力，其中 Apheris 与当前拓扑最接近。

当前真正值得建立差异的位置，是以下组合：

1. 动态本体与数据分级共同编译出**业务数据产品合同**，而不是只注册 dataset、table 或任意容器任务。
2. 编译器同时生成 typed Product OSDK，让银行应用调用稳定的业务动作，不接触 Provider URL、表名和物理 schema。
3. 同一个 OSDK 动作可由 Gateway fan-out 到多个独立 Provider Runtime，返回逐 Provider 的 typed result、失败状态、运行版本和签名 Receipt。
4. Gateway 只做身份、合同、授权、路由和响应关联；跨 Provider 的信用评分、权重和最低来源规则由银行持有。
5. 本体字段分级或产品投影变化可以驱动接口缩减与版本变化，使“可用不可见”落实到可测试的软件合同。

这是一个**中等概念新颖性、早期工程门槛仍偏低、行业落地门槛很高**的方向。当前原型的建议评分为：概念组合新颖性 `6/10`，现有代码技术壁垒 `4/10`，形成行业标准、认证适配和 Provider 网络后的潜在商业壁垒 `7/10`。

## 2. 最接近的方案

### 2.1 Apheris Gateway：最直接的架构对标

[Apheris Gateway](https://www.apheris.com/docs/gateway/latest/general/introduction.html) 支持在数据保管方环境中验证、配置并执行 Compute Spec，原始数据留在本地。其[架构文档](https://www.apheris.com/docs/gateway/latest/general/architecture.html)采用中心 Orchestrator 和多个本地 Compute Gateway：Orchestrator 路由任务、保存数据集元数据，并可聚合各 Gateway 的中间结果；本地 Gateway 执行计算和策略控制。

与本原型的重合：

- 中心编排端到多个本地 Runtime 的联邦调用。
- 数据保管方控制允许谁在什么数据上运行什么计算。
- 计算结果返回，原始数据不需要离开本地环境。
- 多方任务、局部失败、审计和程序化调用都是核心问题。

本原型可保留的差异：

- Apheris 的主要抽象是 dataset、asset policy、compute spec 和模型/容器任务；本原型面向由本体编译出的、受版本控制的业务产品动作。
- 本原型计划让 OSDK 的输入输出随本体和分级规则生成，而不是让数据科学家提交通用 Compute Spec。
- Apheris 可在 Orchestrator 聚合联邦计算中间结果；当前银行场景明确让银行应用掌握业务评分聚合，Gateway 只返回来源可追溯的逐 Provider 结果。

判断：Apheris 证明了总体拓扑和价值主张已有成熟竞品，因此“远程 OSDK 调本地 Provider”不是壁垒；动态语义产品合同和银行业务集成才可能形成区分。

### 2.2 数据空间 Connector：治理和互操作对标

[International Data Spaces Connector](https://international-data-spaces-association.github.io/DataspaceConnector/Introduction) 强调分散存储、Connector 执行使用条件、语义元数据和应用容器；其[Usage Control](https://international-data-spaces-association.github.io/DataspaceConnector/Documentation/v6/UsageControl)采用 ODRL 风格策略表达并在运行时执行。

[Eclipse Dataspace Components](https://projects.eclipse.org/projects/technology.edc)提供 Connector、联邦目录、身份和注册等数据空间组件。[EDC Handbook](https://github.com/eclipse-edc/docs/blob/main/developer/handbook.md)将控制面负责合同、策略、身份和传输协商，数据面负责实际数据流转。[Dataspace Protocol](https://projects.eclipse.org/projects/technology.dataspace-protocol-base/governance)进一步标准化目录、ODRL 使用策略、合同协商和数据传输。

与本原型的重合：身份、目录、合同、用途控制、Provider 自主管理和跨组织连接。主要差异是 EDC/IDS 更偏通用数据资产交换基础设施，而本原型把重点放在可执行业务服务和生成式 typed SDK。

2025 年论文 [A Service Architecture for Dataspaces](https://arxiv.org/abs/2507.07979)也指出主流数据空间实现主要围绕带策略的数据资产，服务支持仍不足，并提出服务抽象。这为“数据空间中的受控业务服务”方向提供了外部验证，但也说明这是正在形成的共同演进方向，并非独占概念。

### 2.3 中国可信数据空间：本土直接竞争与政策窗口

国家数据局[《可信数据空间发展行动计划（2024-2028年）》](https://www.nda.gov.cn/sjj/zwgk/zcfb/1122/20241122164142182915964_pc.html)提出到 2028 年建成 100 个以上可信数据空间。其[技术架构文件](https://www.nda.gov.cn/sjj/ywpd/szkjyjcss/0430/20250430181352183912672_pc.html)和[官方问答](https://www.nda.gov.cn/sjj/ywpd/szkjyjcss/0430/ff808081-960ee4a2-0196-8636d340-0431.pdf)将服务平台与接入 Connector 作为基本组成，覆盖身份、目录、数字合约、使用控制，以及数据、算法、服务和接口资源。

国家数据局 2026 年介绍的[中小微企业融资增信可信数据空间](https://www.nda.gov.cn/sjj/ywpd/sjzy/0121/20260121135536476611581_pc.html)已经面向银行场景整合多类数据资源和 200 余项数据产品，采用隐私计算、区块链等技术支持数据“可用不可见”。

判断：银行融资增信不是空白市场，政策和试点正在快速形成。原型不能只靠“可信数据空间 + 征信”获得新颖性，必须在标准化产品接入速度、typed OSDK 开发体验、语义版本治理和可验证执行上给出量化优势。

## 3. 其他相邻方案

| 方案 | 核心抽象与能力 | 与本原型的关系 |
| --- | --- | --- |
| [AWS Clean Rooms](https://docs.aws.amazon.com/clean-rooms/latest/userguide/what-is.html) | 多方在不暴露底层数据的前提下进行受规则约束的 SQL、PySpark、ML 等分析 | 已覆盖多方受控分析和输出控制；更偏云数据/分析协作环境，不是异构 Provider 上由本体生成的业务 API |
| [Snowflake Data Clean Rooms](https://docs.snowflake.com/en/user-guide/cleanrooms/about) | 在 Snowflake 环境内用已批准模板进行多方协作，原始数据不可直接查询 | 平台原生 Clean Room；typed 业务 OSDK 和独立 Provider Runtime 不是其主要抽象 |
| [Databricks Clean Rooms](https://docs.databricks.com/aws/en/clean-rooms/) | 通过隔离的 serverless compute、Unity Catalog 和 Open Sharing 进行协作 | 适合平台内数据协作；本原型追求跨异构数据域的产品动作合同 |
| [Decentriq](https://www.decentriq.com/data-clean-rooms) | 使用机密计算等隐私增强技术，只释放批准的聚合结果 | 在隐私强度上高于当前原型；主要产品面向 Clean Room 和联合分析，不以动态本体编译 OSDK 为核心 |
| [Ocean Compute-to-Data](https://docs.oceanprotocol.com/developers/compute-to-data) | 算法到数据侧执行，以计算访问替代原始数据下载 | “计算靠近数据”高度重合；更偏数据/算法资产交易和 Web3 机制，不提供本原型的业务语义 SDK 组合 |
| [Dawex](https://www.dawex.com/en/data-exchange-technology/interoperability/) | 数据交易/数据空间平台，提供多种数据平台 Connector、REST/DSP 兼容和 ODRL 合同表达 | 在目录、交易、互操作和 Connector 生态上更成熟；主要编排数据交换，不直接等同于本体生成的本地业务计算服务 |
| [Palantir OSDK](https://www.palantir.com/docs/foundry/ontology-sdk/overview) | 从选定 Ontology 子集生成 typed SDK，供应用访问对象、动作和函数 | “Ontology -> typed SDK”最接近；通常依托 Foundry 后端，不是开放的多 Provider Runtime 联邦协议 |

## 4. 能力对比

| 能力 | Apheris | IDS / EDC | Clean Rooms | Palantir OSDK | 当前原型 |
| --- | --- | --- | --- | --- | --- |
| 原始数据留域 | 强 | 可配置 | 强 | 由平台治理 | 已验证接口不泄露；真实源留域尚未验证 |
| 多 Provider 调度 | 强 | 强 | 多协作者 | 非主要定位 | 已完成 Gateway fan-out |
| 本地可执行服务 | Compute Spec / 容器 | 应用或数据服务可扩展 | 受控分析作业 | Ontology action/function | 产品动作 Runtime |
| 动态语义合同 | 弱至中 | 语义目录/ODRL | 模板和 schema | 强 | 强，DOIR + 分级 + 产品投影 |
| typed 业务 SDK | CLI/Python 工作流 | 非核心 | 非核心 | 强 | 已生成 Python OSDK |
| 逐 Provider 凭证与来源 | 有日志/治理 | 协议与审计可扩展 | 平台审计 | 平台治理 | 已返回逐 Provider 签名 Receipt |
| 谁做业务聚合 | Orchestrator 可做 | 取决于应用 | Clean Room 查询/任务 | 应用或平台函数 | 银行应用 |
| 当前成熟度 | 商业产品 | 标准与开源生态 | 商业产品 | 商业平台 | 技术原型 |

## 5. 新颖性边界

### 不应作为独占卖点

- 数据“可用不可见”或原始数据不下载。
- Provider 本地部署 Connector/Runtime。
- 中心 Gateway/Orchestrator fan-out 到多个数据域。
- 用途策略、数字合同、目录、审计和凭证。
- 从语义模型生成 typed SDK。

这些要素均已有成熟先例。仅把它们并置，也容易被行业团队复现。

### 可以重点验证的组合创新

- **Policy-aware OSDK compiler**：本体、字段分级、用途和产品投影共同决定 SDK 的可见输入输出，并形成兼容性版本规则。
- **Provider-neutral product action**：银行只看到同一个产品动作和逻辑 Provider ID；不同数据方可用不同物理 schema 和 adapter 实现同一合同。
- **Provenance-preserving fan-out**：一次 OSDK 调用返回逐 Provider 的 typed 结果、错误、运行版本和签名 Receipt，不把来源揉成 Gateway 自有业务分数。
- **Business-owned composition**：银行掌握评分模型、权重和最低来源策略；基础设施不获得或固化银行的核心风险算法。
- **Service product over data asset**：交付可执行、受版本控制的业务能力，而不是卖一张表、一个下载链接或任意计算容器权限。

这些差异目前有设计与部分代码证据，但还需要真实 adapter、可靠身份和可重放审计来建立可信度。

## 6. 真正的进入门槛

按重要性排序：

1. **监管与信任门槛**：银行是否认可 Provider 的身份、执行环境、算法版本、输出控制和 Receipt；需要安全评估、等保/密评适配、审计制度和责任边界。
2. **Provider 接入门槛**：异构表、GIS、API、主数据和质量规则的映射成本远高于写一个 Gateway；需要 adapter SDK、映射测试和合规扫描工具。
3. **语义一致性门槛**：同一业务对象在不同 Provider 的口径、时间窗、缺失值和质量等级不同；必须提供 conformance test 和版本兼容机制。
4. **隐私与输出泄露门槛**：字段隐藏不等于隐私安全；还需最小群体阈值、差分隐私、查询预算、推断攻击防护和结果审核。
5. **跨主体身份与合同门槛**：需要 OIDC/mTLS、证书与密钥轮换、ODRL/DSP 合同映射、授权撤销和组织级信任锚。
6. **运行时可信门槛**：Provider 需验证允许执行的代码、镜像、资源限制和沙箱，必要时引入 TEE、远程证明或可验证构建。
7. **分布式可靠性门槛**：幂等、超时、重试、调用配额预留、部分失败、长任务、事件回放和跨重启审计都必须有明确语义。
8. **网络效应门槛**：一旦积累银行认可的 Provider、标准产品模板、行业本体和认证 adapter，生态与历史质量数据才会形成难复制的商业壁垒。

## 7. 建议产品路线

短期不要尝试重做一个完整 EDC、Clean Room 或联邦学习平台。更有效的路线是：

1. 以银行融资增信为第一个垂直场景，定义 3 至 5 个可认证的 Product Action 和输出质量合同。
2. 把真实 SQLite/DuckDB/GIS adapter、Provider conformance kit、语义映射测试做成第一道工程壁垒。
3. 把 OSDK 编译器扩展为策略感知的兼容性编译器，自动产生变更报告、SDK 版本和 Provider 适配失败原因。
4. 把逐 Provider Receipt 做成可独立验签的证据包，加入固定 Provider 身份、密钥轮换、时间戳和重放验证。
5. 与 DSP/ODRL 互操作，把数据空间协议当作合同与发现层；本项目集中解决“合同签完后，业务应用如何安全、稳定、typed 地调用服务”。
6. 用量化指标证明价值：Provider 接入周期、银行开发代码量、合同变更影响范围、失败可定位时间、敏感字段暴露面和审计取证时间。

## 8. 最终判断

市场不是空白，且 Apheris、可信数据空间试点和 Clean Room 厂商已经证明客户愿意为跨组织受控计算付费。当前方案的新颖性不在单个基础技术，而在“动态语义产品编译 + typed OSDK + 多 Provider 本地 Runtime + 来源保留 + 银行业务侧聚合”的工程组合。

这个组合值得继续，但代码本身还没有形成显著壁垒。下一阶段若能完成真实异构 adapter、Provider conformance、可信身份、持久化 Receipt 和 DSP/ODRL 兼容，项目会从“合理的架构原型”进入“可被银行和数据方认真评估的产品技术底座”。
