import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  Activity,
  BookOpen,
  Bot,
  Boxes,
  Code2,
  Database,
  FileCheck2,
  GitBranch,
  Hammer,
  MapPinned,
  Network,
  PackageCheck,
  RefreshCcw,
  Search,
  ShieldCheck,
  Trash2,
  Zap,
} from "lucide-react";
import "./styles.css";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const TABS = [
  {
    id: "power-credit",
    label: "用电征信",
    productId: "enterprise-energy-credit",
    icon: Zap,
    dataKey: "power-credit",
  },
  {
    id: "changchun-risk",
    label: "长春开挖风险",
    productId: "changchun-excavation-risk",
    icon: MapPinned,
    dataKey: "changchun-risk",
  },
  {
    id: "ontology-ops",
    label: "动态本体运维",
    productId: "changchun-excavation-risk",
    icon: Hammer,
    dataKey: "ontology-ops",
  },
  {
    id: "deployment-view",
    label: "部署视图",
    productId: "enterprise-energy-credit",
    icon: Network,
    dataKey: "deployment",
  },
];

const exposureText = {
  HIDDEN: "隐藏：不进 OSDK，不可输出",
  INTERNAL_ONLY: "治理内部：只给 OntologyOps",
  COMPUTE_ONLY: "仅计算：Runtime 内部可用",
  MASKED: "脱敏：可读但需脱敏",
  AGGREGATE_ONLY: "聚合：只出摘要",
  EXTERNAL_RESULT: "结果：可作为产品输出",
};

const objectText = {
  Enterprise: "企业主体",
  EnergyUsage: "月度用电记录",
  BillingRecord: "缴费记录",
  CreditResult: "征信评估结果",
  PipelineSegment: "管线段",
  ExcavationProject: "开挖项目",
  RiskAssessment: "开挖风险评估",
  MonitoringSignal: "监测摘要",
  HazardEvent: "历史隐患",
  ProductProjection: "数据产品投影",
  SourceDataset: "源数据集",
  SourceField: "源字段",
  RuntimeBinding: "运行时绑定",
  ApplicationManifest: "应用清单",
  Entitlement: "授权许可",
  ExecutionReceipt: "执行凭证",
};

const fieldText = {
  enterprise_id: "企业统一标识",
  masked_name: "脱敏企业名",
  period: "用电月份",
  kwh: "月度用电量",
  raw_monthly_kwh: "原始月度用电明细",
  payment_status: "缴费状态",
  late_days: "逾期天数",
  credit_score: "征信评分",
  risk_level: "风险等级",
  coverage_months: "覆盖月份数",
  usage_stability_index: "用电稳定性指数",
  late_payment_count_band: "逾期次数区间",
  quality_summary: "数据质量摘要",
  explanation: "评分解释",
  segment_id: "管线段编号",
  exact_coordinates: "精确坐标",
  asset_type: "资产类型",
  owner_detail: "权属详情",
  excavation_area: "开挖范围",
  excavation_depth: "开挖深度",
  construction_method: "施工方式",
  overall_risk: "总体风险",
  affected_asset_types: "受影响资产类型",
  affected_segment_count: "受影响管线段数",
  recommendations: "处置建议",
};

const relationText = {
  "has monthly usage": "拥有月度用电记录",
  "has billing records": "关联缴费记录",
  "produces credit result": "生成征信评估结果",
  "spatially intersects": "空间相交 / 缓冲区命中",
  "contributes to risk": "参与风险评分",
  "produces assessment": "生成风险评估结果",
};

const cardinalityText = {
  one_to_one: "一对一",
  one_to_many: "一对多",
  many_to_one: "多对一",
  many_to_many: "多对多",
};

const columnText = {
  unified_credit_code: "统一社会信用代码",
  usage_month: "用电月份",
  total_kwh: "总用电量",
  source_row_id: "源数据行号",
  payment_status: "缴费状态",
  late_days: "逾期天数",
  enterprise_no: "企业编号",
  period_code: "账期",
  energy_qty: "能源用量",
  settle_status: "结算状态",
  segment_id: "管线段编号",
  asset_type: "资产类型",
  geometry: "几何坐标",
  depth: "埋深",
  material: "材质",
  alerts_30d: "30天告警数",
  quality: "质量分",
  count: "次数",
  severity: "严重程度",
  product_id: "产品编号",
  product_version: "产品版本",
  ontology_version: "本体版本",
  actions: "OSDK动作",
  readable_fields: "可读字段数",
  entitlement_id: "授权编号",
  provider_id: "数据域",
  purpose: "使用目的",
  used_calls: "已用次数",
  max_calls: "调用上限",
  revoked: "是否撤销",
  event_hash: "审计事件哈希",
  request_id: "请求编号",
  output_hash: "输出哈希",
  workload_id: "工作负载编号",
  image_digest: "镜像摘要",
  network_policy: "网络策略",
  attestation: "运行证明",
  action_id: "动作编号",
  runtime_endpoint: "Runtime 路由",
  contract_version: "合约版本",
  request_signature: "请求签名",
  input_hash: "输入哈希",
};

const scenarioStory = {
  "power-credit": {
    intent: "帮我查询选中企业的用电征信，并返回可验证凭证。",
    tool: "enterprise_energy_credit.compute_credit_features",
    value: "智能体 Agent 不写 SQL，而是读取产品目录，申请授权后并行调用两个 Provider 的 Product OSDK。",
    boundary: "国家电网和综合能源各自在本地计算特征；银行侧只得到摘要、解释和凭证。",
  },
  "changchun-risk": {
    intent: "评估这个开挖工程是否影响城市生命线资产，并给出处置建议。",
    tool: "changchun_excavation_risk.assess_excavation_risk",
    value: "智能体 Agent 只提交工程参数和区域，风险动作在长春 Runtime 内部使用坐标、规则和监测摘要。",
    boundary: "精确坐标和权属详情不出域；外部只得到风险等级、影响类型、建议和凭证。",
  },
  "ontology-ops": {
    intent: "把管线精确坐标升级为核心数据，并重新编译受影响的数据产品。",
    tool: "ontology_ops.recompile_product_projection",
    value: "智能体 Agent / 运维台先看全量本体，再识别受影响产品投影，最后触发 OSDK 重新编译。",
    boundary: "本体可以很大，但每个产品只拿被治理规则允许的安全投影。",
  },
  "deployment-view": {
    intent: "把客户 OSDK 作为独立 workload 运行，经可信数据空间网关调用受控 Runtime。",
    tool: "GatewayRuntimeAdapter.execute_action",
    value: "同一套 OSDK 可在客户侧运行，也可在我方沙箱运行；网络策略只允许访问可信数据空间网关。",
    boundary: "OSDK workload 不直连数据库或 Runtime 内网；网关负责身份、合约、路由、审计和调用约束。",
  },
};

const agentValue = [
  {
    label: "发现",
    section: "顶部意图条 + 产品 OSDK",
    problem: "告诉用户智能体先读产品目录和 OSDK/MCP 描述，而不是猜表结构。",
  },
  {
    label: "授权",
    section: "实时运行情况 + 授权指标",
    problem: "说明每次调用都有用途、数据域、调用方和期限约束，不绕过 Policy。",
  },
  {
    label: "编排",
    section: "右侧执行明细 + 部署视图",
    problem: "展示同一命名动作如何跨 Provider / 网关执行，同时不接触 SQL、连接串或原始文件。",
  },
  {
    label: "适配",
    section: "动态本体运维",
    problem: "展示本体分类变化后，产品投影和 OSDK 接口会重新编译收缩。",
  },
  {
    label: "验证",
    section: "凭证中心 / Receipt",
    problem: "说明结果不是一句话答案，而是带授权、应用、本体、产品、Runtime 和 hash 的可验证凭证。",
  },
];

const deploymentModes = {
  "customer-side": {
    label: "客户侧 OSDK Workload",
    runtime: "客户侧 Kubernetes / VM / Agent Runtime",
    trust: "客户控制应用和 OSDK 运行环境，网络只放行到可信数据空间网关。",
    workloadId: "customer-bank-agent",
  },
  "vendor-sandbox": {
    label: "我方独立 OSDK 沙箱",
    runtime: "我方受控沙箱 / per-customer workload",
    trust: "客户代码或 OSDK 包在独立沙箱运行，仍必须经过可信数据空间网关调用 Runtime。",
    workloadId: "vendor-hosted-customer-osdk",
  },
};

const deploymentRows = [
  {
    table: "osdk_workload.sandbox_manifest",
    business_object: "ApplicationManifest",
    fields: "workload_id, image_digest, network_policy, attestation",
    sample_rows: 2,
    osdk_exposure: "OSDK 作为独立 workload 运行，只允许访问网关",
    preview_rows: [
      {
        workload_id: "customer-bank-agent",
        image_digest: "sha256:customer-osdk-runner",
        network_policy: "egress:tds-gateway-only",
        attestation: "sha256:workload-attestation",
      },
      {
        workload_id: "vendor-hosted-customer-osdk",
        image_digest: "sha256:isolated-osdk-sandbox",
        network_policy: "egress:tds-gateway-only",
        attestation: "sha256:sandbox-attestation",
      },
    ],
  },
  {
    table: "tds_gateway.action_route",
    business_object: "RuntimeBinding",
    fields: "product_id, action_id, runtime_endpoint, contract_version",
    sample_rows: 2,
    osdk_exposure: "网关按产品合约路由，不暴露 Runtime 内网地址",
    preview_rows: [
      {
        product_id: "enterprise-energy-credit",
        action_id: "compute_credit_features",
        runtime_endpoint: "provider-runtime/power-credit",
        contract_version: "product-contract@1.0.0",
      },
      {
        product_id: "changchun-excavation-risk",
        action_id: "assess_excavation_risk",
        runtime_endpoint: "provider-runtime/changchun-risk",
        contract_version: "product-contract@1.1.0",
      },
    ],
  },
  {
    table: "tds_gateway.audit_envelope",
    business_object: "ExecutionReceipt",
    fields: "request_signature, entitlement_id, input_hash, output_hash",
    sample_rows: 1,
    osdk_exposure: "每次跨域调用都带签名请求和可验证凭证",
    preview_rows: [
      {
        request_signature: "ed25519:gateway-request-signature",
        entitlement_id: "ent_demo_gateway",
        input_hash: "sha256:request-payload",
        output_hash: "sha256:result-summary",
      },
    ],
  },
];

const fullOntologyNodes = [
  { id: "SourceDataset", group: "治理底座", products: ["power-credit", "changchun-risk"] },
  { id: "SourceField", group: "治理底座", products: ["power-credit", "changchun-risk"] },
  { id: "Enterprise", group: "企业用电征信", products: ["power-credit"] },
  { id: "EnergyUsage", group: "企业用电征信", products: ["power-credit"] },
  { id: "BillingRecord", group: "企业用电征信", products: ["power-credit"] },
  { id: "CreditResult", group: "企业用电征信", products: ["power-credit"] },
  { id: "PipelineSegment", group: "长春生命线", products: ["changchun-risk"] },
  { id: "ExcavationProject", group: "长春生命线", products: ["changchun-risk"] },
  { id: "RiskAssessment", group: "长春生命线", products: ["changchun-risk"] },
  { id: "MonitoringSignal", group: "长春生命线", products: ["changchun-risk"] },
  { id: "HazardEvent", group: "长春生命线", products: ["changchun-risk"] },
  { id: "ProductProjection", group: "产品编译", products: ["power-credit", "changchun-risk"] },
  { id: "RuntimeBinding", group: "产品编译", products: ["power-credit", "changchun-risk"] },
  { id: "ApplicationManifest", group: "智能体执行", products: ["power-credit", "changchun-risk"] },
  { id: "Entitlement", group: "智能体执行", products: ["power-credit", "changchun-risk"] },
  { id: "ExecutionReceipt", group: "智能体执行", products: ["power-credit", "changchun-risk"] },
];

const productProjectionCards = [
  {
    id: "power-credit",
    title: "企业用电征信产品投影",
    action: "compute_credit_features",
    objects: ["Enterprise", "EnergyUsage", "BillingRecord", "CreditResult"],
    output: "征信评分、风险等级、稳定性、逾期区间、质量摘要、凭证",
  },
  {
    id: "changchun-risk",
    title: "长春开挖风险产品投影",
    action: "assess_excavation_risk",
    objects: ["ExcavationProject", "PipelineSegment", "RiskAssessment"],
    output: "风险等级、影响资产类型、影响段数、处置建议、质量摘要、凭证",
  },
];

function deploymentCode(mode) {
  const selected = deploymentModes[mode];
  const sandboxLine =
    mode === "customer-side"
      ? "# 运行位置：客户侧 OSDK Workload"
      : "# 运行位置：我方为客户启动的独立 OSDK 沙箱";
  return `${sandboxLine}
from enterprise_energy_credit import EnterpriseEnergyCreditClient, ProviderRuntimeClient

runtime = ProviderRuntimeClient(
    base_url="http://127.0.0.1:8000",
    api_key="demo_key_bank_agent",
    requester_agent="agent:bank-risk",
)

client = EnterpriseEnergyCreditClient(runtime=runtime)

result = client.compute_credit_features(
    provider_id="grid",
    enterprise_id="91300000DEMO0007",
    months=12,
    entitlement_id="<Policy 签发的授权编号>",
)

# ProviderRuntimeClient 实际发送的受控请求
POST /actions/execute
{
  "requester_agent": "agent:bank-risk",
  "provider_id": "grid",
  "product_id": "enterprise-energy-credit",
  "product_version": "enterprise-energy-credit@1.0.0",
  "action_id": "compute_credit_features",
  "entitlement_id": "<Policy 签发的授权编号>",
  "payload": {
    "enterprise_id": "91300000DEMO0007",
    "months": 12
  },
  "workload_id": "${selected.workloadId}",
  "transport": "remote-osdk-to-gateway"
}`;
}

function deploymentResult(mode) {
  const selected = deploymentModes[mode];
  return {
    mode,
    status: "success",
    result: {
      workload: selected.label,
      gateway: "可信数据空间网关",
      runtime: "我方 Product Runtime",
      boundary: "OSDK workload 不能直连数据库或 Runtime 内网",
    },
    trace: [
      {
        title: "启动独立 OSDK Workload",
        actor: selected.runtime,
        detail: selected.trust,
        facts: {
          workload_id: selected.workloadId,
          network_policy: "egress:tds-gateway-only",
        },
      },
      {
        title: "OSDK 通过网关适配器发起调用",
        actor: "GatewayRuntimeAdapter",
        detail: "OSDK 仍调用同一个 Product Client，但 runtime 被替换成网关适配器。",
        code: deploymentCode(mode),
      },
      {
        title: "可信数据空间网关校验并路由",
        actor: "Trusted Data Space Gateway",
        detail: "网关校验 workload 身份、请求签名、产品合约、entitlement_id 和路由策略。",
        facts: {
          checks: [
            "workload_attestation",
            "request_signature",
            "product_contract",
            "entitlement_id",
            "route_policy",
          ],
        },
      },
      {
        title: "我方 Runtime 执行实际计算",
        actor: "Product Runtime",
        detail: "Runtime 收到受控 action_id 后，再执行 Policy 校验、本体映射、本地计算和输出过滤。",
        facts: {
          action_id: "compute_credit_features",
          internal_dependencies: ["EnergyUsage.kwh", "BillingRecord.late_days"],
        },
      },
      {
        title: "返回摘要结果和凭证",
        actor: "Audit Service + Gateway",
        detail: "结果和 receipt 通过网关返回 OSDK workload；后续可扩展成多 Runtime 联合计算编排。",
        facts: {
          returned: ["CreditResult", "ExecutionReceipt"],
          future_extension: "federated_runtime_orchestration",
        },
      },
    ],
  };
}

async function api(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }
  return response.json();
}

const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

function Section({ title, icon: Icon, children }) {
  return (
    <section className="panel">
      <div className="panel-title">
        <Icon size={17} aria-hidden="true" />
        <h2>{title}</h2>
      </div>
      {children}
    </section>
  );
}

function Metric({ label, value, hint }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
      {hint && <small>{hint}</small>}
    </div>
  );
}

function TabNav({ activeTab, setActiveTab }) {
  return (
    <nav className="tab-nav" aria-label="Demo scenarios">
      {TABS.map((tab) => {
        const Icon = tab.icon;
        return (
          <button
            className={activeTab === tab.id ? "active" : ""}
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
          >
            <Icon size={17} />
            {tab.label}
          </button>
        );
      })}
    </nav>
  );
}

function NarrativeStrip({ activeTab, selectedEnterpriseId, changchunForm }) {
  const story = scenarioStory[activeTab];
  const subject =
    activeTab === "power-credit"
      ? selectedEnterpriseId
      : activeTab === "changchun-risk"
        ? changchunForm.project_id
        : activeTab === "deployment-view"
          ? "OSDK workload"
          : "PipelineSegment.exact_coordinates";
  return (
    <section className="narrative-strip">
      <div>
        <span>用户意图</span>
        <strong>{story.intent}</strong>
        <small>当前对象：{subject}</small>
      </div>
      <div>
        <span>智能体 Agent 决策</span>
        <strong>{story.tool}</strong>
        <small>{story.value}</small>
      </div>
      <div>
        <span>可信边界</span>
        <strong>OSDK 只暴露产品动作</strong>
        <small>{story.boundary}</small>
      </div>
    </section>
  );
}

function AgentIntentCard({ activeTab, subject }) {
  const story = scenarioStory[activeTab];
  return (
    <div className="agent-intent">
      <div className="agent-intent-title">
        <Bot size={16} />
        <strong>智能体 Agent 执行视角</strong>
      </div>
      <div className="agent-intent-grid">
        <div>
          <span>自然语言目标</span>
          <p>{story.intent}</p>
        </div>
        <div>
          <span>选择的 OSDK / MCP Tool</span>
          <code>
            {story.tool}({JSON.stringify({ subject })})
          </code>
        </div>
        <div>
          <span>为什么不是直接查表</span>
          <p>{story.boundary}</p>
        </div>
      </div>
    </div>
  );
}

function PowerWorkbench({
  enterprises,
  selectedEnterpriseId,
  setSelectedEnterpriseId,
  run,
  result,
  busy,
}) {
  return (
    <div className="workbench">
      <div className="form-row">
        <label>
          企业
          <select
            value={selectedEnterpriseId}
            onChange={(event) => setSelectedEnterpriseId(event.target.value)}
          >
            {enterprises.map((enterprise) => (
              <option value={enterprise.id} key={enterprise.id}>
                {enterprise.name} · {enterprise.id}
              </option>
            ))}
          </select>
        </label>
        <button onClick={run} disabled={busy}>
          <Search size={17} />
          查询征信
        </button>
      </div>
      <div className="note">
        前端只选择企业并提交产品动作。底层的电量、缴费字段由 Runtime 在数据域内通过动态本体映射读取。
      </div>
      <AgentIntentCard activeTab="power-credit" subject={selectedEnterpriseId} />
      {result?.aggregated_credit_score && (
        <ResultGrid
          items={[
            ["企业", result.enterprise_id],
            ["银行侧聚合分数", result.aggregated_credit_score],
            ["风险等级", result.risk_level],
            ["Provider", result.provider_count],
          ]}
        />
      )}
      {result?.aggregation_owner === "bank-application" && (
        <div className="note">
          Gateway 保留各 Provider 的独立结果与凭证，最终权重和评分规则由银行应用执行。
        </div>
      )}
    </div>
  );
}

function ChangchunWorkbench({ form, setForm, run, result, busy }) {
  return (
    <div className="workbench">
      <div className="form-row">
        <label>
          工程 ID
          <input
            value={form.project_id}
            onChange={(event) => setForm({ ...form, project_id: event.target.value })}
          />
        </label>
        <label>
          开挖深度
          <input
            type="number"
            step="0.1"
            value={form.excavation_depth}
            onChange={(event) =>
              setForm({ ...form, excavation_depth: event.target.value })
            }
          />
        </label>
        <label>
          施工方式
          <select
            value={form.construction_method}
            onChange={(event) =>
              setForm({ ...form, construction_method: event.target.value })
            }
          >
            <option value="MECHANICAL">机械开挖</option>
            <option value="MANUAL">人工探挖</option>
          </select>
        </label>
        <button onClick={run} disabled={busy}>
          <Search size={17} />
          评估风险
        </button>
      </div>
      <div className="note">
        前端提交区域和施工参数；管线精确坐标、拓扑和监测摘要只在长春 Runtime 内部用于计算。
      </div>
      <AgentIntentCard activeTab="changchun-risk" subject={form.project_id} />
      {result?.result && (
        <ResultGrid
          items={[
            ["风险等级", result.result.overall_risk],
            ["影响资产", result.result.affected_asset_types.join(", ")],
            ["影响段数", result.result.affected_segment_count],
            ["质量门槛", result.result.quality_summary.quality_gate],
          ]}
        />
      )}
    </div>
  );
}

function OpsWorkbench({ run, result, busy, coordinateCore }) {
  const versionAfter =
    result?.result?.version_after ||
    (coordinateCore ? "changchun-excavation-risk@1.1.0" : "changchun-excavation-risk@1.0.0");
  return (
    <div className="workbench">
      <div className="ops-action">
        <div>
          <strong>管线精确坐标分类升级</strong>
          <p>
            将 `PipelineSegment.exact_coordinates` 升级为核心数据后，OSDK 不生成坐标读取接口，但
            `assess_excavation_risk` 仍可在数据域内使用坐标计算。
          </p>
        </div>
        <button onClick={run} disabled={busy}>
          <ShieldCheck size={17} />
          重新编译 OSDK
        </button>
      </div>
      <ResultGrid
        items={[
          ["坐标核心数据", coordinateCore ? "已启用" : "未启用"],
          ["当前产品版本", versionAfter],
          ["运维目标", "接口收缩，动作保留"],
          ["影响对象", "PipelineSegment"],
        ]}
      />
      <AgentIntentCard
        activeTab="ontology-ops"
        subject="PipelineSegment.exact_coordinates"
      />
    </div>
  );
}

function DeploymentWorkbench({ mode, setMode, run, result, busy }) {
  const selected = deploymentModes[mode];
  return (
    <div className="workbench">
      <div className="deployment-mode-grid">
        {Object.entries(deploymentModes).map(([id, item]) => (
          <button
            className={`deployment-mode ${mode === id ? "active" : ""}`}
            key={id}
            onClick={() => setMode(id)}
            type="button"
          >
            <strong>{item.label}</strong>
            <span>{item.runtime}</span>
          </button>
        ))}
      </div>
      <div className="note">
        {selected.trust} 关键点是：客户的 OSDK 和调用逻辑变成独立 workload，之后所有 Runtime 调用都经过可信数据空间网关。
      </div>
      <div className="deployment-code-card">
        <div className="data-preview-title">
          <strong>实际代码演示</strong>
          <span>{selected.label}</span>
        </div>
        <pre>{deploymentCode(mode)}</pre>
      </div>
      <button onClick={run} disabled={busy}>
        <Network size={17} />
        模拟网关调用
      </button>
      {result?.result && (
        <ResultGrid
          items={[
            ["Workload", selected.label],
            ["网关状态", result.status],
            ["征信评分", result.result.credit_score],
            ["Receipt", result.receipt_id],
          ]}
        />
      )}
    </div>
  );
}

function DeploymentTopologyView({ mode }) {
  const selected = deploymentModes[mode];
  const nodes = [
    ["客户 / Agent", "提交业务意图，调用 Product OSDK"],
    [selected.label, selected.runtime],
    ["可信数据空间网关", "身份、合约、签名、授权、路由、审计"],
    ["我方 Product Runtime", "Policy、本体映射、实际计算、输出过滤"],
    ["凭证与联合计算扩展", "Receipt 返回；后续可编排多个 Runtime"],
  ];
  return (
    <div className="deployment-topology">
      <div className="ontology-summary">
        <strong>通用部署模型：OSDK 是独立 workload，Runtime 是受控计算端</strong>
        <span>
          无论 OSDK 在客户侧还是我方沙箱运行，它都只通过可信数据空间网关调用 Runtime。这个边界也为后续联邦计算、TEE、MPC 或多 Runtime 编排留下空间。
        </span>
      </div>
      <div className="topology-chain">
        {nodes.map(([title, detail], index) => (
          <React.Fragment key={title}>
            <div className={`topology-node ${index === 1 ? "active" : ""}`}>
              <strong>{title}</strong>
              <span>{detail}</span>
            </div>
            {index < nodes.length - 1 && <div className="topology-arrow">→</div>}
          </React.Fragment>
        ))}
      </div>
      <div className="deployment-boundary-grid">
        <div>
          <strong>客户侧运行</strong>
          <p>客户保留应用和 Agent 运行控制权；OSDK workload 只允许出网到可信数据空间网关。</p>
        </div>
        <div>
          <strong>我方沙箱运行</strong>
          <p>客户 OSDK 包或调用逻辑在我方隔离沙箱运行；仍按 workload 身份经网关访问 Runtime。</p>
        </div>
        <div>
          <strong>联合计算扩展</strong>
          <p>多个 OSDK workload 或多个 Runtime 可以由网关编排，先交换摘要、凭证或隐私计算任务。</p>
        </div>
      </div>
    </div>
  );
}

function ResultGrid({ items }) {
  return (
    <div className="result-grid">
      {items.map(([label, value]) => (
        <div key={label}>
          <span>{label}</span>
          <strong>{String(value)}</strong>
        </div>
      ))}
    </div>
  );
}

function OntologyPanel({
  productPackage,
  activeTab,
  allPackages,
  coordinateCore,
  deploymentMode,
}) {
  if (activeTab === "ontology-ops") {
    return (
      <OntologyOpsCompilerView
        allPackages={allPackages}
        coordinateCore={coordinateCore}
      />
    );
  }
  if (activeTab === "deployment-view") {
    return <DeploymentTopologyView mode={deploymentMode} />;
  }
  const ontology = productPackage?.ontology_model;
  const objects = Object.entries(ontology?.object_types || {});
  const links = Object.entries(ontology?.link_types || {});
  if (!ontology) return <div className="empty">等待产品包加载。</div>;
  return (
    <div className="ontology-panel">
      <div className="ontology-summary">
        <strong>{ontology.ontology.display_name}</strong>
        <span>
          本体对象定义了 OSDK 可引用的业务语义；字段暴露级别决定能否被读、能否输出、或只能在 Runtime 内计算。
        </span>
      </div>
      <OntologyGraph links={links} />
      <div className="object-list">
        {objects.map(([objectName, objectType]) => (
          <div className="object-card" key={objectName}>
            <div className="object-card-title">
              <NameWithCode label={objectText[objectName] || objectName} code={objectName} />
              <span>{Object.keys(objectType.properties || {}).length} fields</span>
            </div>
            <div className="field-list">
              {Object.entries(objectType.properties || {}).map(([field, property]) => (
                <div className="field-row" key={field}>
                  <div>
                    <NameWithCode label={fieldText[field] || field} code={field} />
                    <span>{property.type}</span>
                  </div>
                  <div>
                    <span className={`exposure exposure-${property.exposure}`}>
                      {property.exposure}
                    </span>
                    <small>{exposureText[property.exposure]}</small>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function OntologyOpsCompilerView({ allPackages, coordinateCore }) {
  const activeProjection = coordinateCore ? "changchun-risk" : "changchun-risk";
  const compileRows = [
    [
      "PipelineSegment.exact_coordinates",
      coordinateCore ? "COMPUTE_ONLY" : "INTERNAL_ONLY",
      coordinateCore
        ? "不生成读取接口；仅 assess_excavation_risk 可在 Runtime 内部使用"
        : "治理内部可见；升级后会触发接口收缩",
    ],
    ["PipelineSegment.owner_detail", "HIDDEN", "完全不进入 OSDK，不允许输出"],
    ["RiskAssessment.overall_risk", "EXTERNAL_RESULT", "进入结果模型，可返回给调用方"],
    ["EnergyUsage.kwh", "COMPUTE_ONLY", "只用于用电征信本地计算，不返回明细"],
    ["EnergyUsage.raw_monthly_kwh", "HIDDEN", "原始用电序列被裁掉，不生成接口"],
    ["ExecutionReceipt.output_hash", "EXTERNAL_RESULT", "作为凭证校验材料返回"],
  ];
  const packageCount = Object.keys(allPackages || {}).length;
  return (
    <div className="ops-compiler-view">
      <div className="ontology-summary">
        <strong>动态本体不是一个产品接口，而是产品编译的语义原料库</strong>
        <span>
          当前 Registry 中有 {packageCount} 个产品包。运维页展示全量语义资产，然后说明每个产品只会编译出一部分安全 OSDK。
        </span>
      </div>

      <div className="compiler-stage">
        <div className="compiler-stage-title">
          <Boxes size={16} />
          <strong>1. 全量动态本体</strong>
          <span>跨场景、跨治理对象统一登记；未进入当前产品的对象不会出现在该产品 OSDK 中。</span>
        </div>
        <div className="full-ontology-grid">
          {fullOntologyNodes.map((node) => (
            <div
              className={`ontology-chip ${
                node.products.includes(activeProjection) ? "selected" : ""
              }`}
              key={node.id}
            >
              <NameWithCode label={objectText[node.id] || node.id} code={node.id} />
              <small>{node.group}</small>
            </div>
          ))}
        </div>
      </div>

      <div className="compiler-stage">
        <div className="compiler-stage-title">
          <GitBranch size={16} />
          <strong>2. 产品投影</strong>
          <span>产品投影从全量本体里选对象、动作和输出，再交给分类分级规则裁剪。</span>
        </div>
        <div className="projection-grid">
          {productProjectionCards.map((projection) => (
            <div
              className={`projection-card ${
                projection.id === activeProjection ? "active" : ""
              }`}
              key={projection.id}
            >
              <strong>{projection.title}</strong>
              <code>{projection.action}</code>
              <div className="projection-objects">
                {projection.objects.map((objectName) => (
                  <span key={objectName}>{objectText[objectName] || objectName}</span>
                ))}
              </div>
              <small>{projection.output}</small>
            </div>
          ))}
        </div>
      </div>

      <div className="compiler-stage">
        <div className="compiler-stage-title">
          <PackageCheck size={16} />
          <strong>3. 编译裁剪结果</strong>
          <span>同一个本体字段会因为分类分级不同，被编译成可输出、仅计算、仅治理或完全隐藏。</span>
        </div>
        <table className="compile-table">
          <thead>
            <tr>
              <th>本体字段</th>
              <th>分类分级</th>
              <th>编译到 OSDK 的结果</th>
            </tr>
          </thead>
          <tbody>
            {compileRows.map(([field, exposure, result]) => (
              <tr key={field}>
                <td>{field}</td>
                <td>
                  <span className={`exposure exposure-${exposure}`}>{exposure}</span>
                </td>
                <td>{result}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <div className="compile-diff">
          <strong>{coordinateCore ? "已重新编译" : "待演示重新编译"}</strong>
          <span>
            {coordinateCore
              ? "坐标读取接口被移除，但风险评估动作保留；智能体 Agent 重新读取 OSDK 后只能调用受控动作。"
              : "点击重新编译后，坐标字段会从可治理查看变成仅 Runtime 内部计算，OSDK 接口随之收缩。"}
          </span>
        </div>
      </div>
    </div>
  );
}

function NameWithCode({ label, code }) {
  const showCode = label !== code;
  return (
    <span className="name-with-code">
      <strong>{label}</strong>
      {showCode && <code>{code}</code>}
    </span>
  );
}

function OntologyGraph({ links }) {
  if (!links.length) {
    return <div className="empty">当前产品包未声明本体关系。</div>;
  }
  return (
    <div className="relation-graph" aria-label="本体关系图">
      <div className="relation-graph-title">
        <strong>本体关系图</strong>
        <span>OSDK 动作通过这些语义关系跨对象计算，但不会暴露底层表连接。</span>
      </div>
      <div className="relation-rows">
        {links.map(([name, link]) => (
          <div className="relation-row" key={name}>
            <span className="graph-node">
              <NameWithCode label={objectText[link.from] || link.from} code={link.from} />
            </span>
            <span className="graph-edge">
              <strong>{relationText[link.label] || link.label || name}</strong>
              <code>{link.label || name}</code>
            </span>
            <span className="graph-node">
              <NameWithCode label={objectText[link.to] || link.to} code={link.to} />
            </span>
            <small>
              <strong>{cardinalityText[link.cardinality] || link.cardinality}</strong>
              <code>{link.cardinality}</code>
            </small>
          </div>
        ))}
      </div>
    </div>
  );
}

function DataTables({ rows }) {
  if (!rows?.length) return <div className="empty">暂无底层数据表预览。</div>;
  return (
    <div className="table-list">
      <table>
        <thead>
          <tr>
            <th>底层表 / 资产</th>
            <th>映射本体对象</th>
            <th>关键字段</th>
            <th>样例规模</th>
            <th>OSDK 暴露</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={`${row.table}-${row.business_object}`}>
              <td>{row.table}</td>
              <td>
                <NameWithCode
                  label={objectText[row.business_object] || row.business_object}
                  code={row.business_object}
                />
              </td>
              <td>{row.fields}</td>
              <td>{row.sample_rows}</td>
              <td>{row.osdk_exposure}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="data-preview-list">
        {rows.map((row) => (
          <div className="data-preview-card" key={`preview-${row.table}`}>
            <div className="data-preview-title">
              <strong>{row.table}</strong>
              <span>数据样例</span>
            </div>
            <PreviewTable rows={row.preview_rows || []} />
          </div>
        ))}
      </div>
    </div>
  );
}

function PreviewTable({ rows }) {
  if (!rows.length) return <div className="empty compact">暂无样例行，运行任务后会出现。</div>;
  const columns = Array.from(new Set(rows.flatMap((row) => Object.keys(row))));
  return (
    <div className="preview-table-wrap">
      <table className="preview-table">
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column}>
                <NameWithCode label={columnText[column] || column} code={column} />
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, rowIndex) => (
            <tr key={rowIndex}>
              {columns.map((column) => (
                <td key={column}>{formatCell(row[column])}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function formatCell(value) {
  if (value === undefined || value === null) return "";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

function TaskPanel({ activeTab, task, latestResult, productPackage, cleared, onClear }) {
  const traces = cleared ? [] : tracesFor(activeTab, latestResult);
  const timelineSteps = cleared ? [] : task?.steps || [];
  const hasContent = timelineSteps.length > 0 || traces.length > 0;
  return (
    <aside className="task-panel">
      <div className="task-header">
        <div>
          <span>实时运行情况</span>
          <strong>{TABS.find((tab) => tab.id === activeTab)?.label}</strong>
        </div>
        <div className="task-header-actions">
          <Activity size={20} />
          <button
            className="clear-button"
            disabled={!hasContent || task?.status === "running"}
            onClick={onClear}
            title="清空当前 Tab 的运行轨迹"
          >
            <Trash2 size={14} />
            清空
          </button>
        </div>
      </div>

      {!hasContent && (
        <div className="empty dark">
          左侧提交任务后，这里会显示从前端查询、OSDK 调用、本体映射、底层数据读取到凭证签名的全过程。
        </div>
      )}
      {timelineSteps.length > 0 && (
        <div className="live-steps">
          {timelineSteps.map((step, index) => (
            <LiveStep step={step} index={index} key={step.title} />
          ))}
        </div>
      )}
      {traces.length > 0 && (
        <>
          <div className="trace-subtitle">执行明细</div>
          <TraceList traces={traces} />
        </>
      )}

      <div className="osdk-compact">
        <div className="mini-title">
          <Code2 size={15} />
          当前 OSDK
        </div>
        <pre>{productPackage?.python_osdk || "waiting for product package"}</pre>
      </div>
    </aside>
  );
}

function AgentValuePanel() {
  return (
    <div className="agent-value-panel">
      <div className="agent-value-title">
        <div>
          <Bot size={17} />
          <strong>智能体 Agent 价值闭环</strong>
        </div>
        <span>
          每格对应：闭环步骤 / 对应区域 / 解决的问题。先看这张地图，再看下面三个 Tab。
        </span>
      </div>
      <div className="agent-value-list">
        {agentValue.map((item) => (
          <div key={item.label}>
            <strong>{item.label}</strong>
            <span>{item.section}</span>
            <p>{item.problem}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function tracesFor(activeTab, result) {
  if (!result) return [];
  if (activeTab === "power-credit") {
    return (result.jobs || []).map((job) => ({
      id: job.job_id,
      title: job.provider_id,
      status: job.status,
      trace: job.trace || [],
    }));
  }
  if (activeTab === "changchun-risk" && result.trace) {
    return [
      {
        id: result.job_id,
        title: result.provider_id,
        status: result.status,
        trace: result.trace || [],
      },
    ];
  }
  if (activeTab === "ontology-ops" && result.trace) {
    return [
      {
        id: "ontology-ops",
        title: "OntologyOps",
        status: "success",
        trace: result.trace,
      },
    ];
  }
  if (activeTab === "deployment-view" && result.trace) {
    return [
      {
        id: "deployment-gateway",
        title: "远程 OSDK -> Simple Trusted Gateway",
        status: result.status || "success",
        trace: result.trace,
      },
      ...(result.runtime_trace
        ? [
            {
              id: "deployment-runtime",
              title: "Gateway -> Provider Runtime",
              status: result.status || "success",
              trace: result.runtime_trace,
            },
          ]
        : []),
    ];
  }
  return [];
}

function LiveStep({ step, index }) {
  return (
    <div className={`live-step ${step.status}`}>
      <span>{index + 1}</span>
      <div>
        <strong>{step.title}</strong>
        <small>{step.detail}</small>
      </div>
    </div>
  );
}

function TraceList({ traces }) {
  return (
    <div className="trace-list">
      {traces.map((traceGroup) => (
        <div className="trace-group" key={traceGroup.id}>
          <div className="trace-group-title">
            <strong>{traceGroup.title}</strong>
            <span>{traceGroup.status}</span>
          </div>
          {traceGroup.trace.map((step, index) => (
            <TraceStep step={step} index={index} key={`${traceGroup.id}-${index}`} />
          ))}
        </div>
      ))}
    </div>
  );
}

function TraceStep({ step, index }) {
  const facts = Object.entries(step.facts || {});
  return (
    <div className="trace-step">
      <div className="trace-index">{index + 1}</div>
      <div className="trace-body">
        <div className="trace-head">
          <strong>{step.title}</strong>
          <span>{step.actor}</span>
        </div>
        <p>{step.detail}</p>
        {step.code && (
          <div className="mini-code">
            <pre>{step.code}</pre>
          </div>
        )}
        {facts.length > 0 && (
          <dl>
            {facts.map(([key, value]) => (
              <React.Fragment key={key}>
                <dt>{key}</dt>
                <dd>
                  {typeof value === "string" || typeof value === "number"
                    ? String(value)
                    : JSON.stringify(value)}
                </dd>
              </React.Fragment>
            ))}
          </dl>
        )}
      </div>
    </div>
  );
}

function ReceiptStatus({ receipt, valid }) {
  if (!receipt) return null;
  return (
    <div className={`receipt-status ${valid ? "valid" : "pending"}`}>
      <FileCheck2 size={17} />
      {valid ? "凭证签名验证通过" : "正在验证凭证"}
      <code>{receipt.output_hash}</code>
    </div>
  );
}

function App() {
  const [state, setState] = useState(null);
  const [activeTab, setActiveTab] = useState("power-credit");
  const [selectedEnterpriseId, setSelectedEnterpriseId] = useState("91300000DEMO0007");
  const [changchunForm, setChangchunForm] = useState({
    project_id: "CC-2026-001",
    excavation_depth: "3.5",
    construction_method: "MECHANICAL",
  });
  const [deploymentMode, setDeploymentMode] = useState("customer-side");
  const [latestByTab, setLatestByTab] = useState({});
  const [liveTaskByTab, setLiveTaskByTab] = useState({});
  const [taskPanelClearedByTab, setTaskPanelClearedByTab] = useState({});
  const [receiptValid, setReceiptValid] = useState(null);
  const [error, setError] = useState("");

  async function refresh() {
    const next = await api("/demo/state");
    setState(next);
  }

  useEffect(() => {
    refresh().catch((err) => setError(err.message));
  }, []);

  const activeConfig = TABS.find((tab) => tab.id === activeTab);
  const activePackage = state?.product_packages?.[activeConfig.productId];
  const latestResult = latestByTab[activeTab];
  const liveTask = liveTaskByTab[activeTab];
  const latestReceipt = useMemo(() => {
    if (!latestResult) return null;
    if (latestResult.jobs?.length) return latestResult.jobs.at(-1).receipt;
    return latestResult.receipt || null;
  }, [latestResult]);

  useEffect(() => {
    if (!latestReceipt) {
      setReceiptValid(null);
      return;
    }
    api("/receipts/verify", {
      method: "POST",
      body: JSON.stringify(latestReceipt),
    })
      .then((result) => setReceiptValid(result.valid))
      .catch(() => setReceiptValid(false));
  }, [latestReceipt]);

  async function runWithTimeline(tabId, plannedSteps, request) {
    setError("");
    setTaskPanelClearedByTab((current) => ({ ...current, [tabId]: false }));
    const seed = plannedSteps.map((step) => ({ ...step, status: "pending" }));
    setLiveTaskByTab((current) => ({
      ...current,
      [tabId]: { status: "running", steps: seed },
    }));
    for (let index = 0; index < plannedSteps.length; index += 1) {
      setLiveTaskByTab((current) => ({
        ...current,
        [tabId]: {
          status: "running",
          steps: seed.map((step, stepIndex) => ({
            ...step,
            status:
              stepIndex < index ? "done" : stepIndex === index ? "running" : "pending",
          })),
        },
      }));
      await wait(180);
    }
    try {
      const result = await request();
      setLatestByTab((current) => ({ ...current, [tabId]: result }));
      await refresh();
      setLiveTaskByTab((current) => ({
        ...current,
        [tabId]: {
          status: "done",
          steps: seed.map((step) => ({ ...step, status: "done" })),
        },
      }));
    } catch (err) {
      setError(err.message);
      setLiveTaskByTab((current) => ({
        ...current,
        [tabId]: {
          status: "failed",
          steps: seed.map((step) => ({ ...step, status: "failed" })),
        },
      }));
    }
  }

  function clearTaskPanel() {
    setLiveTaskByTab((current) => ({ ...current, [activeTab]: null }));
    setTaskPanelClearedByTab((current) => ({ ...current, [activeTab]: true }));
  }

  const isBusy = liveTask?.status === "running";
  const enterpriseOptions = state?.enterprise_options || [];
  const sourceRows =
    activeTab === "deployment-view"
      ? deploymentRows
      : state?.source_tables?.[activeConfig.dataKey] || [];

  function runPower() {
    runWithTimeline(
      "power-credit",
      [
        { title: "智能体 Agent 接收业务意图", detail: selectedEnterpriseId },
        { title: "智能体 Agent 读取产品目录", detail: "选择 enterprise-energy-credit" },
        { title: "按用途签发两个授权", detail: "grid + integrated-energy" },
        { title: "智能体 Agent 调用 Product OSDK", detail: "compute_credit_features" },
        { title: "Provider 本地映射和计算", detail: "raw rows stay local" },
        { title: "智能体 Agent 汇总摘要并验证凭证", detail: "receipt hash + signature" },
      ],
      () =>
        api("/demo/run/power-credit", {
          method: "POST",
          body: JSON.stringify({ enterprise_id: selectedEnterpriseId }),
        }),
    );
  }

  function runChangchun() {
    runWithTimeline(
      "changchun-risk",
      [
        { title: "智能体 Agent 接收施工安全意图", detail: changchunForm.project_id },
        { title: "智能体 Agent 读取风险产品投影", detail: "changchun-excavation-risk" },
        { title: "按施工安全用途授权", detail: "construction_safety_assessment" },
        { title: "智能体 Agent 调用风险评估 OSDK", detail: "assess_excavation_risk" },
        { title: "Runtime 内部使用坐标计算", detail: "geometry stays local" },
        { title: "智能体 Agent 返回风险摘要和凭证", detail: "coordinates blocked" },
      ],
      () =>
        api("/demo/run/changchun", {
          method: "POST",
          body: JSON.stringify({
            project_id: changchunForm.project_id,
            excavation_depth: Number(changchunForm.excavation_depth),
            construction_method: changchunForm.construction_method,
          }),
        }),
    );
  }

  function runOps() {
    runWithTimeline(
      "ontology-ops",
      [
        { title: "智能体 Agent / 运维台读取全量本体", detail: "跨场景语义资产" },
        { title: "定位受影响产品投影", detail: "changchun-excavation-risk" },
        { title: "更新字段分类分级", detail: "exact_coordinates -> COMPUTE_ONLY" },
        { title: "Product Compiler 重新裁剪", detail: "只编译安全投影" },
        { title: "发布新 OSDK 合同", detail: "read interface shrinks, action remains" },
      ],
      () => api("/demo/recompile-coordinate-core", { method: "POST" }),
    );
  }

  function runDeployment() {
    runWithTimeline(
      "deployment-view",
      [
        { title: "启动 OSDK 独立 Workload", detail: deploymentModes[deploymentMode].label },
        { title: "加载客户 Product OSDK", detail: "EnterpriseEnergyCreditClient" },
        { title: "通过可信数据空间网关发起调用", detail: "ProviderRuntimeClient -> /actions/execute" },
        { title: "网关校验身份、合约和授权", detail: "signature + entitlement + route policy" },
        { title: "我方 Runtime 执行受控计算", detail: "policy + ontology binding + compute" },
        { title: "返回摘要结果和凭证", detail: "CreditResult + ExecutionReceipt" },
      ],
      () =>
        api("/demo/run/remote-power-credit", {
          method: "POST",
          body: JSON.stringify({
            enterprise_id: selectedEnterpriseId,
            provider_id: "grid",
            months: 12,
          }),
        }),
    );
  }

  return (
    <main>
      <header className="app-header">
        <div>
          <p className="eyebrow">Dynamic Ontology OSDK</p>
          <h1>可信数据产品流转 Demo Console</h1>
        </div>
        <button className="ghost-button" onClick={refresh} title="刷新状态">
          <RefreshCcw size={17} />
          刷新
        </button>
      </header>

      {error && <div className="error">{error}</div>}

      <div className="metrics">
        <Metric label="产品" value={Object.keys(state?.products || {}).length} />
        <Metric
          label="授权记录"
          value={Object.keys(state?.entitlements || {}).length}
          hint="Entitlement：某请求方对某产品/Provider/用途的调用许可"
        />
        <Metric label="作业" value={Object.keys(state?.jobs || {}).length} />
        <Metric label="审计事件" value={state?.audit_events?.length || 0} />
      </div>

      <AgentValuePanel />

      <TabNav activeTab={activeTab} setActiveTab={setActiveTab} />
      <NarrativeStrip
        activeTab={activeTab}
        selectedEnterpriseId={selectedEnterpriseId}
        changchunForm={changchunForm}
      />

      <div className="workspace">
        <div className="workspace-left">
          <Section title="前端查询工作台" icon={Search}>
            {activeTab === "power-credit" && (
              <PowerWorkbench
                enterprises={enterpriseOptions}
                selectedEnterpriseId={selectedEnterpriseId}
                setSelectedEnterpriseId={setSelectedEnterpriseId}
                run={runPower}
                result={latestByTab["power-credit"]}
                busy={isBusy}
              />
            )}
            {activeTab === "changchun-risk" && (
              <ChangchunWorkbench
                form={changchunForm}
                setForm={setChangchunForm}
                run={runChangchun}
                result={latestByTab["changchun-risk"]}
                busy={isBusy}
              />
            )}
            {activeTab === "ontology-ops" && (
              <OpsWorkbench
                run={runOps}
                result={latestByTab["ontology-ops"]}
                busy={isBusy}
                coordinateCore={Boolean(state?.coordinate_core)}
              />
            )}
            {activeTab === "deployment-view" && (
              <DeploymentWorkbench
                mode={deploymentMode}
                setMode={setDeploymentMode}
                run={runDeployment}
                result={latestByTab["deployment-view"]}
                busy={isBusy}
              />
            )}
          </Section>

          <Section
            title={
              activeTab === "deployment-view"
                ? "部署拓扑和信任边界"
                : "动态本体结构和内容"
            }
            icon={activeTab === "deployment-view" ? Network : BookOpen}
          >
            <OntologyPanel
              productPackage={activePackage}
              activeTab={activeTab}
              allPackages={state?.product_packages}
              coordinateCore={Boolean(state?.coordinate_core)}
              deploymentMode={deploymentMode}
            />
          </Section>

          <Section
            title={activeTab === "deployment-view" ? "网关合约和传输数据" : "底层数据表"}
            icon={Database}
          >
            <DataTables rows={sourceRows} />
          </Section>
        </div>

        <div className="workspace-right">
          <TaskPanel
            activeTab={activeTab}
            task={liveTask}
            latestResult={latestResult}
            productPackage={activePackage}
            cleared={Boolean(taskPanelClearedByTab[activeTab])}
            onClear={clearTaskPanel}
          />
          <ReceiptStatus receipt={latestReceipt} valid={receiptValid} />
        </div>
      </div>
    </main>
  );
}

createRoot(document.getElementById("root")).render(<App />);
