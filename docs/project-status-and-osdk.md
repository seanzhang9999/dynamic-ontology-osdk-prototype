# 项目说明：动态本体 OSDK 可信数据产品流转 Demo

本文说明当前项目的目标、代码结构、可运行能力，以及最重要的：本项目中 **OSDK 的实际实现情况**。它用于帮助后续研发、评审或外部沟通准确理解“已经做成了什么”和“还没有做成什么”。

## 1. 项目当前定位

本项目是一个 **MVP 原型**，目标是验证：

- 数据提供方保留原始数据，需求方应用进入数据域执行。
- 动态本体把异构数据源映射成稳定的业务对象、查询和动作。
- Product OSDK 只暴露经过产品投影和策略允许的命名能力，不暴露表、字段、SQL、连接串或原始文件。
- Policy Service、Provider Runtime、Audit Receipt 共同保证用途受控、结果受控、过程可审计。

当前已经有两个可演示场景：

| 场景 | 目标 | 当前状态 |
| --- | --- | --- |
| 企业用电征信 | 同一银行应用进入国家电网、综合能源两个异构 Provider Runtime，本地计算征信特征，原始用电数据不出域 | 已实现可运行链路 |
| 长春城市生命线开挖风险 | 施工应用提交开挖范围，Runtime 本地使用管线数据计算风险，只输出摘要和凭证 | 已实现可运行链路 |

## 2. 代码结构

核心代码位置：

```text
core/trusted_data_demo/
  app.py        FastAPI API 入口
  compiler.py   Product Compiler 与 OSDK/MCP/OpenAPI 元数据生成
  runtime.py    两个场景的 Provider Runtime 与演示编排
  policy.py     授权、用途、期限、撤销、配额校验
  audit.py      哈希链事件、Ed25519 签名凭证、凭证验证
  fixtures.py   合成数据、DOIR fixture、产品定义
  models.py     ProductPackage、Entitlement、Receipt 等模型
  geo.py        长春场景的轻量空间计算
```

前端控制台：

```text
ui/demo-console/
  src/main.jsx
  src/styles.css
```

场景配置：

```text
scenarios/power-credit/
scenarios/changchun-lifeline/
```

文档：

```text
docs/demo-contract.md
docs/data-dictionary.md
docs/acceptance-checklist.md
docs/demo-script.md
```

## 3. 当前可运行能力

启动后端：

```bash
PYTHONPATH=core .venv/bin/python -m uvicorn trusted_data_demo.app:app --host 127.0.0.1 --port 8000
```

启动前端：

```bash
cd ui/demo-console
VITE_API_BASE_URL=http://127.0.0.1:8000 npm run dev -- --host 127.0.0.1 --port 5173
```

访问：

- API: http://127.0.0.1:8000/health
- Demo Console: http://127.0.0.1:5173

Demo Console 当前按产品流转链路展示：

- 产品工厂：产品版本、用途、动作、原始导出策略。
- 动态本体：对象、字段、类型、分类分级以及 OSDK 暴露含义。
- OSDK 调用面：由本体和产品策略生成的 Python OSDK、MCP Tool、输出 schema、Runtime 内部依赖。
- 执行拓扑：Agent、Catalog、Policy、OSDK、Runtime、Receipt 的调用关系。
- 执行凭证：用业务语言解释授权、应用、本体/映射/产品版本、输入输出 hash、审计链和签名验证。

主要演示接口：

```bash
curl -X POST http://127.0.0.1:8000/demo/run/power-credit \
  -H 'Content-Type: application/json' \
  -d '{"enterprise_id":"91300000DEMO0007"}'

curl -X POST http://127.0.0.1:8000/demo/run/changchun

curl -X POST http://127.0.0.1:8000/demo/recompile-coordinate-core
```

测试：

```bash
PYTHONPATH=core .venv/bin/python -m unittest discover -s tests
cd ui/demo-console && npm run build
```

## 4. OSDK 在本项目中的含义

本项目中的 OSDK 不是一个泛化数据访问 SDK，也不是数据库 ORM。它表示：

```text
由动态本体和产品策略编译出来的、面向某个可信数据产品的受控能力接口。
```

它的职责是：

- 把底层表、字段、文件、GIS 图层隐藏起来。
- 只暴露命名 Query/Action。
- 把分类分级、用途、输出粒度、质量门槛编译进产品接口。
- 给 Agent 或业务应用提供稳定的调用面。
- 配合 Provider Runtime 和 Policy Service 防止绕过。

换句话说，OSDK 是“产品能力合同”，不是最终安全边界。真正的执行与校验由 Provider Runtime、Policy Service、Audit Service 完成。

## 5. OSDK 的实际实现情况

当前 OSDK 处于 **MVP 元数据生成 + Runtime 合同验证阶段**，不是完整生产级 SDK。

### 5.1 已实现

`core/trusted_data_demo/compiler.py` 中的 `compile_product()` 会生成 `ProductPackage`，包含：

- `product_manifest`
- `product_schema`
- `runtime_binding`
- `quality_certificate`
- `compatibility_report`
- `python_osdk`
- `mcp_tools`
- `openapi`

可以通过 API 查看产品包：

```bash
curl http://127.0.0.1:8000/products/enterprise-energy-credit
curl http://127.0.0.1:8000/products/changchun-excavation-risk
```

其中 `python_osdk` 是生成出来的 Python SDK 代码字符串。例如企业用电征信产品会生成类似：

```python
class EnterpriseEnergyCreditClient:
    def __init__(self, runtime):
        self.runtime = runtime

    def compute_credit_features(self, **payload):
        return self.runtime.execute_action(
            "enterprise-energy-credit",
            "compute_credit_features",
            payload,
        )
```

长春开挖风险产品会生成类似：

```python
class ChangchunExcavationRiskClient:
    def __init__(self, runtime):
        self.runtime = runtime

    def assess_excavation_risk(self, **payload):
        return self.runtime.execute_action(
            "changchun-excavation-risk",
            "assess_excavation_risk",
            payload,
        )
```

`mcp_tools` 目前是 MCP Tool 的 JSON 声明，表达 Agent 可见的工具名称、输入 schema 和输出 schema。

`openapi` 目前是最小 OpenAPI 元数据，用来说明产品动作最终会落到 Runtime 的受控执行接口。

### 5.2 OSDK 编译规则已生效

当前编译器已经实现分类分级对接口的影响：

| 暴露级别 | 当前行为 |
| --- | --- |
| `HIDDEN` | 不进入 readable fields，也不能作为产品输出 |
| `INTERNAL_ONLY` | 不作为外部产品输出 |
| `COMPUTE_ONLY` | 可被 Runtime 本地计算使用，但不能直接输出 |
| `AGGREGATE_ONLY` | 可作为聚合/摘要语义暴露 |
| `EXTERNAL_RESULT` | 可进入产品输出 schema |

测试覆盖了两个关键点：

- 企业用电征信中 `EnergyUsage.kwh`、`EnergyUsage.raw_monthly_kwh` 不会出现在产品可读接口或输出中。
- 长春场景中“管线精确坐标”升级为核心数据后，产品版本变为 `1.1.0`，坐标读取面仍然不暴露，但 `assess_excavation_risk` 动作仍可使用坐标在本地计算。

### 5.3 Product OSDK 与 Runtime 的关系

目前调用链是：

```text
Product Compiler
  -> ProductPackage
  -> python_osdk / mcp_tools / openapi / runtime_binding
  -> Provider Runtime
  -> Policy Service
  -> Audit Receipt
```

Runtime 当前提供的受控 API 包括：

- `GET /products/{product_id}`
- `POST /entitlements`
- `POST /entitlements/verify`
- `POST /entitlements/{entitlement_id}/revoke`
- `POST /policy/evaluate`
- `POST /applications/submit`
- `POST /jobs/execute`
- `GET /jobs/{job_id}`
- `GET /receipts/{job_id}`
- `POST /receipts/verify`

业务应用并不直接拿数据库连接，也不直接读取源表。它只能提交产品动作请求，由 Runtime 做：

- 产品版本确认
- application manifest 检查
- entitlement 校验
- purpose 校验
- provider 校验
- output granularity 校验
- 本地计算
- 输出白名单
- 凭证签名

### 5.4 Demo Console 如何使用 OSDK

当前前端 Demo Console **没有直接 import 生成的 SDK 包**。

它调用后端演示 API：

- `/demo/run/power-credit`
- `/demo/run/changchun`
- `/demo/recompile-coordinate-core`
- `/demo/state`

因此，前端证明的是“产品包、Runtime、策略和凭证链路可运行”，不是“前端应用通过 npm 包形式消费 TypeScript OSDK”。

这点很重要：当前 OSDK 的实现重点在 **后端产品编译和受控 Runtime 合同**，还没有做到完整 SDK 分发。

## 6. 两个产品的 OSDK 表面

### 6.1 企业用电征信产品

Product ID:

```text
enterprise-energy-credit
```

Purpose:

```text
enterprise_credit_assessment
```

动作：

```text
compute_credit_features
```

允许输出：

- `credit_score`
- `risk_level`
- `coverage_months`
- `usage_stability_index`
- `late_payment_count_band`
- `provider_count`
- `quality_summary`
- `explanation`
- `execution_receipt`

禁止输出：

- 原始月度用电明细
- 原始 kWh 序列
- 逐笔缴费流水
- 表名、源行 ID、连接串

### 6.2 长春开挖风险产品

Product ID:

```text
changchun-excavation-risk
```

Purpose:

```text
construction_safety_assessment
```

动作：

```text
assess_excavation_risk
```

允许输出：

- `overall_risk`
- `affected_asset_types`
- `affected_segment_count`
- `recommendations`
- `quality_summary`
- `execution_receipt`

禁止输出：

- 精确管线坐标
- 完整管网拓扑
- 权属单位细节
- 原始监测时间序列

## 7. 当前 OSDK 的限制

当前实现有意保持 MVP 范围，主要限制如下：

| 能力 | 当前状态 | 说明 |
| --- | --- | --- |
| Python SDK | 生成代码字符串 | 尚未写入独立 package 目录，也未发布 wheel |
| TypeScript SDK | 未实现 | 前端现在直接调用 REST demo API |
| MCP Server | 未实现 | 已生成 MCP Tool JSON 元数据，但没有启动真正 MCP server |
| OpenAPI | 最小元数据 | 可表达动作路径，但不是完整生产 OpenAPI |
| Runtime handle | 概念实现 | 生成的 SDK 依赖 `runtime.execute_action()`，尚未提供独立 client runtime 类 |
| 持久化 | 内存态 | Registry、Policy、Audit 当前重启后丢失 |
| 应用沙箱 | 轻量 manifest 校验 | 没有真正生产级容器隔离、网络隔离、文件系统隔离 |
| 多服务部署 | Compose 结构已给出 | 多个服务当前运行同一 FastAPI 应用，角色通过部署结构表达 |
| 真实数据适配 | 未实现 | 当前使用合成数据和 fixture |

## 8. 已经可以证明的事情

当前代码已经可以证明：

- 同一个企业用电征信产品合同可以服务两个异构 Provider。
- 产品输出不包含原始用电明细和缴费流水。
- Entitlement 撤销后 Runtime 会拒绝执行。
- 执行凭证可用 Ed25519 验证，篡改后验证失败。
- 分类分级变化会影响产品版本和 OSDK 可读表面。
- 长春风险产品可以在本地使用敏感坐标计算，但只输出风险摘要。

对应测试文件：

```text
tests/test_compiler.py
tests/test_runtime_policy_audit.py
```

## 9. 下一步建议

如果要把 OSDK 从 MVP 推到更像真实 SDK，建议按以下顺序做：

1. **落盘 SDK artifact**
   - 将 `python_osdk` 写入 `generated/python/{product_id}/`。
   - 生成 `pyproject.toml`、client runtime、typed models。
   - 加测试证明外部脚本可以 import 生成的 SDK 调用 Runtime。

2. **实现 MCP Server**
   - 把 `mcp_tools` JSON 接到真实 MCP server。
   - 让 Agent 通过 MCP Tool 调用产品，而不是直接调用 demo API。

3. **实现 TypeScript SDK**
   - 从 `product_schema` 生成 TS 类型。
   - 从 `runtime_binding` 生成 typed client。
   - 让 Demo Console 改为使用 TypeScript OSDK client。

4. **持久化 Registry、Policy、Audit**
   - 用 SQLite 保存产品版本、授权、作业和凭证。
   - 支持重启后继续查看历史凭证。

5. **增强 Application Host**
   - 真正执行签名应用包。
   - 限制网络、文件系统、环境变量和资源。
   - 将 Runtime handle 注入应用沙箱。

6. **接入真实数据适配器**
   - 从 fixture 切换为 CSV、DuckDB、PostgreSQL、GIS 服务或数据中台 API。
   - 保持 OSDK 合同不变，只替换 Runtime adapter。

## 10. 简短结论

当前项目已经不是纯方案文档，而是一个能跑通的可信数据产品流转 MVP。

但必须准确表述 OSDK 状态：

```text
当前已经实现了“由动态本体和产品策略生成 OSDK 合同与工具元数据，并通过 Provider Runtime 执行”的原型。

当前尚未实现“可独立安装、分发、由外部应用 import 的完整 Python/TypeScript OSDK 包”，也尚未实现真实 MCP server。
```

这也是下一阶段最值得投入的工程方向。
