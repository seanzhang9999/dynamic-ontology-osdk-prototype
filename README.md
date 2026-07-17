# Dynamic Ontology OSDK Prototype

创建日期：2026-07-15

本项目用于调研 Palantir Ontology SDK / OSDK、开放 OOSDK 相关资料，并设计一个可开发原型：把用户的结构化数据与非结构化数据映射到动态本体中间层，再从中间层生成面向应用和 Agent 的动态本体 SDK。

## 项目目标

1. 调研并整理 Palantir OSDK / Ontology / Ontology MCP 的公开技术资料。
2. 调研 Level Up / GitConnected 文章《Why I’m Building an Open Ontology SDK...》作者、公开 GitHub 线索与相关 OOSDK 资料。
3. 设计原型开发计划，证明动态本体 OSDK 可以暴露给 Agent，用于快速开发精确、可用的数据应用。

## 当前产物

- `FINAL_RESEARCH_REPORT.md`：面向最终计划制定者的完整综合研究报告。
- `references/source-index.md`：所有来源、下载状态、可复查链接。
- `references/palantir-osdk-research.md`：Palantir Ontology / OSDK / Ontology MCP 技术要点。
- `references/open-oosdk-author-github.md`：文章作者、候选 GitHub、OOSDK 仓库调研。
- `references/agentic-ops-research.md`：Agentic-OPS 的 Agent 编排、HITL、审计和 Ontology context 调研。
- `prototype-plan/prototype-development-plan.md`：原型架构、阶段计划、应用验证方案。
- `prototype-plan/trusted-data-product-flow-demo-plan.md`：基于可信数据产品流转 Demo 方案展开的双场景原型设计与四周开发计划。
- `specs/dynamic-ontology-ir.md`：动态本体中间表示（DOIR）初版规范。
- `examples/sample-doir.yaml`：一个简化的动态本体中间层示例。
- `core/trusted_data_demo/`：可信数据产品流转 MVP 的后端核心实现。
- `ui/demo-console/`：React + Vite Demo Console。
- `scenarios/`：企业用电征信与长春开挖风险的映射、产品和应用 manifest。
- `docs/`：Demo 合同、数据字典、验收清单和演示脚本。
- `docs/project-status-and-osdk.md`：项目现状说明，重点解释当前 OSDK 的真实实现程度、能力边界和后续演进方向。
- `docs/demo-architecture-implementation-guide.md`：演示说明、架构说明和未来实施技术门槛评估的融合文档。
- `docs/research/2026-07-17-data-service-landscape-and-novelty.md`：数据空间、Clean Room、Apheris、Palantir OSDK 等方案对标及新颖性、进入门槛评估。

## 本地运行

推荐使用 Docker Compose 运行拆分后的 Gateway 和三个 Provider Runtime：

```bash
docker compose up --build
```

服务入口：

- Gateway: http://127.0.0.1:8000/health
- Grid Provider Runtime: http://127.0.0.1:8010/health
- Integrated Energy Provider Runtime: http://127.0.0.1:8011/health
- Changchun Provider Runtime: http://127.0.0.1:8012/health
- Demo Console: http://127.0.0.1:5173
- Legacy all-in-one Demo API: http://127.0.0.1:8090/health

当前 Demo Console 暂时连接 `legacy-demo`，用于保留原有双场景可视化；生成的 Product OSDK 和新的 fan-out API 连接 `gateway:8000`。

不使用 Docker 时，先安装后端依赖，再分别启动 `gateway_app` 与按 `DEMO_PROVIDER_ID` 配置的 `provider_app`。原有单进程 Demo 仍可使用：

```bash
python3 -m pip install -r requirements.txt
make api
```

另开终端运行前端开发服务器：

```bash
cd ui/demo-console
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

## 多 Provider OSDK

OSDK 只使用逻辑 Provider ID 和各 Provider 的 Entitlement，不感知 Provider Runtime 地址：

```python
from enterprise_energy_credit import (
    EnterpriseEnergyCreditClient,
    ProviderBinding,
    ProviderRuntimeClient,
)

runtime = ProviderRuntimeClient(
    base_url="http://127.0.0.1:8000",
    api_key="demo_key_bank_agent",
    requester_agent="agent:bank-risk",
)
client = EnterpriseEnergyCreditClient(runtime=runtime)
response = client.compute_credit_features(
    providers=[
        ProviderBinding(provider_id="grid", entitlement_id="ent_grid"),
        ProviderBinding(
            provider_id="integrated-energy",
            entitlement_id="ent_integrated_energy",
        ),
    ],
    enterprise_id="91300000DEMO0007",
    months=12,
)

# Gateway 返回逐 Provider 结果；银行在自己的应用中决定权重和聚合规则。
scores = [
    item.result.credit_score
    for item in response.provider_results.values()
    if item.status == "succeeded" and item.result is not None
]
bank_score = sum(scores) / len(scores) if scores else None
```

当部分 Runtime 不可用或某个 Entitlement 被拒绝时，响应状态为 `partial`，成功 Provider 的结果和 Receipt 仍然保留。Gateway 不计算银行信用总分。

## 验证


```bash
make test
cd ui/demo-console && npm run build
```

## 已下载参考资料

- `references/raw/`：Palantir 官方页面 HTML 快照。
- `references/external/ai_mcp_multi_agent_oosdk-public/`：候选 OOSDK GitHub 仓库浅克隆。
- `references/external/Agentic-OPS/`：Agentic-OPS GitHub 仓库浅克隆。

LevelUp / Medium 文章页面可通过浏览器访问，但直接 `curl` 下载两次超时，因此未形成原始 HTML 快照；调研笔记保留了原文 URL 与访问说明。

## 当前边界与下一步

Gateway 与 Provider Runtime 已完成进程和 HTTP 边界拆分，生成的 OSDK 已支持一次请求 fan-out 到多个 Provider。Provider 数据目前仍来自各进程内的合成 fixture，Registry、Policy、Audit 仍为内存态，服务身份仍使用开发共享密钥。下一阶段应优先完成真实 SQLite/DuckDB/GIS adapter、持久化 Receipt/Entitlement，以及 OIDC/mTLS 或工作负载身份。详细边界见 `docs/project-status-and-osdk.md`。
