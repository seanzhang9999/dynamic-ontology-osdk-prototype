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

## 本地运行

安装并运行后端：

```bash
python3 -m pip install -r requirements.txt
make api
```

另开终端运行前端：

```bash
cd ui/demo-console
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

访问：

- API: http://127.0.0.1:8000/health
- Demo Console: http://127.0.0.1:5173

测试：

```bash
make test
cd ui/demo-console && npm run build
```

Docker Compose：

```bash
docker compose up --build
```

## 已下载参考资料

- `references/raw/`：Palantir 官方页面 HTML 快照。
- `references/external/ai_mcp_multi_agent_oosdk-public/`：候选 OOSDK GitHub 仓库浅克隆。
- `references/external/Agentic-OPS/`：Agentic-OPS GitHub 仓库浅克隆。

LevelUp / Medium 文章页面可通过浏览器访问，但直接 `curl` 下载两次超时，因此未形成原始 HTML 快照；调研笔记保留了原文 URL 与访问说明。

## 建议下一步

若继续深化，优先把当前内存态 Registry/Policy/Audit 替换为 SQLite 持久化，并将 Product Compiler 的 DOIR 输入从 Python fixture 切换为 `scenarios/*/mappings/*.yaml`。
