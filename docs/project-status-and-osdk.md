# 项目状态：动态本体 OSDK 可信数据产品原型

**状态快照：2026-07-17，基于 `main` 当前工作树（基线提交 `49d577e`）**

## 1. 结论先行

项目现在已经验证以下完整路径：

```text
银行应用
  -> 生成的 typed Product OSDK
  -> 独立 Gateway 进程
  -> 并行 HTTP fan-out
  -> 多个独立 Provider Runtime 进程
  -> 逐 Provider 受控结果和签名 Receipt
  -> 银行应用自行聚合
```

这意味着“远程 OSDK 经 Gateway 调用本地 Provider Runtime”“Gateway 同时连接不同 Provider”“单 Provider 故障不影响其他结果”已经从同进程设计变为可运行实现。Gateway 不持有 Provider 数据，也不计算银行信用总分。

但项目仍不能表述为生产级数据留域平台：Provider Runtime 当前读取的是进程内合成 fixture，Provider mapping 仍未执行真实 SQL/GIS/API 查询；Registry、Entitlement、Audit 和签名密钥仍是内存态；服务间身份使用开发共享密钥。准确定位是：**跨进程联邦数据产品调用的技术原型已经成立，真实异构数据源和生产信任链尚未完成。**

## 2. 当前业务场景

| 场景 | 业务目标 | 当前结果 |
| --- | --- | --- |
| 企业用电征信 | 银行一次调用电网与综合能源 Provider，获得可用于风险模型的特征摘要 | Gateway 并行调用两个 Runtime，返回逐 Provider 分数、质量摘要、运行版本和 Receipt；银行决定权重与聚合 |
| 长春城市生命线开挖风险 | 施工方提交工程范围，管线数据方本地计算风险 | Changchun Runtime 返回风险等级、影响资产类型和建议，不返回精确坐标、管段 ID 或拓扑 |

## 3. 当前服务职责

```text
gateway_app.py
  身份校验、产品合同、Entitlement、Provider 路由、fan-out、响应关联

provider_app.py
  固定 Provider 身份、内部 Gateway 凭据校验、本地动作执行、Receipt 签发

control_plane.py
  Gateway 侧产品目录、Registry Lite 和 Entitlement Store，不加载 Provider 数据

runtime.py
  Provider 侧业务动作、输出投影、执行轨迹和签名审计

osdk_generator.py
  ProviderBinding、typed 业务输入、逐 Provider 结果和 MultiProviderResult 生成
```

Docker Compose 中 `gateway`、`grid-runtime`、`integrated-energy-runtime`、`changchun-runtime` 是独立服务。`legacy-demo` 仅用于保持当前 Demo Console 的原有双场景可视化，不能作为新拆分架构的验收入口。

## 4. 已验证的技术路线

| 技术路线点 | 状态 | 当前证据与边界 |
| --- | --- | --- |
| DOIR 到产品合同编译 | 已验证 | 编译 manifest、动作 schema、Python SDK、MCP 声明和 OpenAPI 元数据；字段分级与版本变化有测试 |
| 敏感字段不进入产品表面 | 已验证 | `HIDDEN`、`INTERNAL_ONLY`、`COMPUTE_ONLY` 等分级限制 readable fields 和输出；用电明细与管线坐标不会出现在产品结果 |
| 业务动作真实计算 | 已验证 | 信用特征和开挖风险由记录或空间规则计算，不是固定 JSON 返回；输入数据仍是合成 fixture |
| Gateway 与 Provider 进程拆分 | 已验证 | Gateway 通过 HTTP 调 Provider 内部动作入口；Provider 固定自身 `provider_id`，拒绝错误身份和无内部凭据请求 |
| 多 Provider Gateway fan-out | 已验证 | 一个 OSDK 请求携带多个逻辑 Provider binding；Gateway 并发调度，返回 `completed`、`partial` 或 `failed` |
| Gateway 不做业务聚合 | 已验证 | 响应只含 `provider_results` 和技术状态；代码与测试确认没有 `aggregated_credit_score` 等银行业务结果 |
| typed 多 Provider OSDK | 已验证 | 生成 `ProviderBinding`、逐 Provider action result 和 `MultiProviderResult`；业务 client 不持有 Provider URL |
| Provider 故障隔离 | 已验证 | 一个 Runtime 不可用时返回 `partial`，其他 Provider 的结果和 Receipt 保留 |
| 用途授权与撤销 | 已验证但未持久化 | Gateway 对每个 Provider 单独预检和扣减 Entitlement；撤销的 Provider 不会收到 Runtime 请求 |
| 结果完整性 Receipt | 已验证但未持久化 | 每个 Provider 进程生成带 input/output hash、前序 hash 和 Ed25519 签名的 Receipt；篡改后验签失败 |
| 真实数据留域接入 | 未验证 | Runtime 只加载本 Provider 的 fixture，但尚未连接独立 SQLite/DuckDB/GIS/API 数据源 |
| 生产级跨组织信任 | 未验证 | 内部服务认证是共享开发 key，没有 mTLS、OIDC、密钥轮换、远程证明或持久化审计 |

## 5. 多 Provider 合同

生成的 Product OSDK 不区分 Provider URL，而是在业务动作中传递逻辑绑定：

```python
response = client.compute_credit_features(
    providers=[
        ProviderBinding(provider_id="grid", entitlement_id="ent_grid"),
        ProviderBinding(
            provider_id="integrated-energy",
            entitlement_id="ent_energy",
        ),
    ],
    enterprise_id="91300000DEMO0007",
    months=12,
)
```

Gateway 对共享业务 payload 校验一次产品合同，对每个 Provider 分别校验 Entitlement 并并行执行。响应保持来源：

```text
status: completed | partial | failed
provider_results:
  grid:               succeeded | denied | failed + result + receipt
  integrated-energy:  succeeded | denied | failed + result + receipt
```

银行随后在自己的代码中定义：必须成功的最少 Provider 数、来源权重、缺失来源降级规则和最终评分。这样可避免 Gateway 获得或固化银行的核心风控算法，也避免基础设施把不同来源的审计证据揉成一个不可追溯结果。

## 6. 内存态现在影响什么

“内存态只影响工程实施，不影响关键技术路线验证”现在比拆分前更接近事实，但仍不能完全成立。

它**不再否定**以下结论：

- Gateway 与 Provider 确实存在网络和进程边界。
- 一个 Gateway 请求可以并行路由到两个独立 Runtime。
- Provider 只能执行自身固定身份范围内的动作。
- 多 Provider 的部分失败合同能够工作。
- Gateway 不需要加载 Provider 数据或执行银行聚合。

它仍然**影响**以下关键结论：

| 内存态实现 | 尚未证明的能力 | 业务风险 |
| --- | --- | --- |
| Registry 使用 SQLite `:memory:` | 产品发布历史、兼容性、回滚和可重放编译 | 重启后无法证明当时执行的是哪一版合同 |
| Entitlement 使用 Python 字典 | 跨实例撤销、并发配额和事务一致性 | 重启丢失；当前先扣配额再远程执行，网络失败也会消耗调用次数 |
| Audit 和 Ed25519 私钥在 Runtime 进程内 | Provider 身份连续性和跨重启取证 | 重启后无法以同一身份验证历史 Receipt |
| Provider 数据是 fixture 列表 | 真实数据最小权限访问、物理隔离和 connector 防绕过 | 只能证明 Runtime 输出边界，不能证明生产数据源不会被旁路读取 |
| Provider route 来自环境变量 | 动态发现、健康路由和组织注册 | 适合原型，不适合大规模 Provider 网络 |

因此，当前可以说“核心联邦调用和产品合同路线已经验证”；不能说“内存态只剩落库工作”或“生产数据不出域已经完成验证”。

## 7. Dummy 与真实实现边界

不是 dummy 的部分：

- DOIR 编译、字段分级、产品版本和 SDK 生成。
- Gateway 合同校验、逐 Provider 授权、并发 fan-out 和部分失败处理。
- Provider 身份范围校验、业务计算、输出投影、哈希和 Ed25519 签名。
- 生成的 OSDK 通过 HTTP 调 Gateway，不导入后端 Runtime 对象。

仍是关键替身的部分：

| 位置 | 当前实现 | 下一阶段验收标准 |
| --- | --- | --- |
| Provider 数据 | 每进程只加载本 Provider 的合成 fixture | 每个 Provider 连接独立 SQLite/DuckDB/GeoPackage 或 API，且物理 schema 不同 |
| Provider adapter | 映射描述和字段存在性校验 | 映射驱动真实查询、转换、过滤和聚合；Runtime 只有本 Provider 连接权限 |
| 服务身份 | 静态 API key 和共享内部 key | OIDC/JWT 或 mTLS 工作负载身份、Provider 证书、密钥轮换 |
| Policy / Registry / Audit | 内存存储与启动时密钥 | 持久化、重启可恢复、撤销可传播、Receipt 可历史验签 |
| 隐私控制 | 输出 schema 过滤 | 最小群体阈值、查询预算、推断泄露测试，必要时差分隐私或机密计算 |

## 8. 已完成的运行验证

自动化测试覆盖编译器、生成 SDK、Gateway fan-out、撤销、Provider 作用域、业务 Runtime 和 Receipt 验签。手工多进程 HTTP 验收还完成了两种路径：

1. Gateway 同时调用 `grid` 和 `integrated-energy` Runtime，生成的 `EnterpriseEnergyCreditClient` 获得两个成功结果、两个不同的 Runtime 标识和两个签名 Receipt。
2. 停止 `integrated-energy` Runtime 后重复同一 OSDK 调用，响应为 `partial`；`grid` 结果继续成功，失败来源为 `provider_unavailable`。

本次收尾验证结果：Python 单元测试 `22` 项全部通过，Demo Console 的 Vite 生产构建通过。当前机器未安装 Docker CLI，因此未执行 `docker compose config` 或容器级验收；独立进程 HTTP 验收使用本机 Python/Uvicorn 完成。

## 9. 下一阶段优先级

1. **真实异构 adapter**：先将两个用电 Provider 分别接入不同 schema 的 SQLite/DuckDB，再将长春场景接入 GeoPackage 或空间数据库。
2. **持久化证据链**：保存 Entitlement、作业、Receipt、Provider 公钥和产品发布版本，增加重启回放测试。
3. **可靠执行语义**：加入 request idempotency、配额 reservation/commit、重试和长任务状态，解决当前“请求失败但配额已扣”问题。
4. **可信服务身份**：用 mTLS/OIDC 替代开发共享密钥，并将 requester 与 Provider 身份写入可验证 Receipt。
5. **数据空间互操作**：优先兼容 DSP/ODRL 的目录、合同和策略表达，不重做完整数据空间基础设施。
6. **业务壁垒验证**：建设银行产品本体、Provider conformance kit 和接入时效指标，证明相较定制接口或 Clean Room 的工程优势。

竞品、新颖性和进入门槛的专项结论见 `docs/research/2026-07-17-data-service-landscape-and-novelty.md`。
