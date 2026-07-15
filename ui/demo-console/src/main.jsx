import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  Activity,
  BookOpen,
  Code2,
  Database,
  FileCheck2,
  Hammer,
  KeyRound,
  MapPinned,
  RefreshCcw,
  Search,
  ShieldCheck,
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
];

const exposureText = {
  HIDDEN: "隐藏：不进 OSDK，不可输出",
  INTERNAL_ONLY: "治理内部：只给 OntologyOps",
  COMPUTE_ONLY: "仅计算：Runtime 内部可用",
  MASKED: "脱敏：可读但需脱敏",
  AGGREGATE_ONLY: "聚合：只出摘要",
  EXTERNAL_RESULT: "结果：可作为产品输出",
};

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
      {result?.aggregated_credit_score && (
        <ResultGrid
          items={[
            ["企业", result.enterprise_id],
            ["聚合分数", result.aggregated_credit_score],
            ["风险等级", result.risk_level],
            ["Provider", result.provider_count],
          ]}
        />
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

function OntologyPanel({ productPackage }) {
  const ontology = productPackage?.ontology_model;
  const objects = Object.entries(ontology?.object_types || {});
  if (!ontology) return <div className="empty">等待产品包加载。</div>;
  return (
    <div className="ontology-panel">
      <div className="ontology-summary">
        <strong>{ontology.ontology.display_name}</strong>
        <span>
          本体对象定义了 OSDK 可引用的业务语义；字段暴露级别决定能否被读、能否输出、或只能在 Runtime 内计算。
        </span>
      </div>
      <div className="object-list">
        {objects.map(([objectName, objectType]) => (
          <div className="object-card" key={objectName}>
            <div className="object-card-title">
              <strong>{objectName}</strong>
              <span>{Object.keys(objectType.properties || {}).length} fields</span>
            </div>
            <div className="field-list">
              {Object.entries(objectType.properties || {}).map(([field, property]) => (
                <div className="field-row" key={field}>
                  <div>
                    <strong>{field}</strong>
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
              <td>{row.business_object}</td>
              <td>{row.fields}</td>
              <td>{row.sample_rows}</td>
              <td>{row.osdk_exposure}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function TaskPanel({ activeTab, task, latestResult, productPackage }) {
  const traces = tracesFor(activeTab, latestResult);
  const runningSteps = task?.status === "running" ? task.steps : [];
  return (
    <aside className="task-panel">
      <div className="task-header">
        <div>
          <span>实时运行情况</span>
          <strong>{TABS.find((tab) => tab.id === activeTab)?.label}</strong>
        </div>
        <Activity size={20} />
      </div>

      {runningSteps.length > 0 ? (
        <div className="live-steps">
          {runningSteps.map((step, index) => (
            <LiveStep step={step} index={index} key={step.title} />
          ))}
        </div>
      ) : traces.length > 0 ? (
        <TraceList traces={traces} />
      ) : (
        <div className="empty dark">
          左侧提交任务后，这里会显示从前端查询、OSDK 调用、本体映射、底层数据读取到凭证签名的全过程。
        </div>
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
  const [latestByTab, setLatestByTab] = useState({});
  const [liveTaskByTab, setLiveTaskByTab] = useState({});
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

  const isBusy = liveTask?.status === "running";
  const enterpriseOptions = state?.enterprise_options || [];
  const sourceRows = state?.source_tables?.[activeConfig.dataKey] || [];

  function runPower() {
    runWithTimeline(
      "power-credit",
      [
        { title: "读取前端企业选择", detail: selectedEnterpriseId },
        { title: "签发两个 Provider 授权", detail: "grid + integrated-energy" },
        { title: "生成并调用 Product OSDK", detail: "compute_credit_features" },
        { title: "Provider 本地映射底层表", detail: "monthly_usage / billing" },
        { title: "返回受控征信结果和凭证", detail: "raw rows blocked" },
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
        { title: "提交开挖风险参数", detail: changchunForm.project_id },
        { title: "签发施工安全用途授权", detail: "construction_safety_assessment" },
        { title: "调用风险评估 OSDK", detail: "assess_excavation_risk" },
        { title: "Runtime 本地执行空间规则", detail: "GIS geometry stays local" },
        { title: "返回风险摘要和凭证", detail: "coordinates blocked" },
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
        { title: "选择核心数据字段", detail: "PipelineSegment.exact_coordinates" },
        { title: "更新 DOIR 分类分级", detail: "COMPUTE_ONLY" },
        { title: "重新编译产品投影", detail: "changchun-excavation-risk@1.1.0" },
        { title: "生成新 OSDK 合同", detail: "read interface shrinks, action remains" },
      ],
      () => api("/demo/recompile-coordinate-core", { method: "POST" }),
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

      <TabNav activeTab={activeTab} setActiveTab={setActiveTab} />

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
          </Section>

          <Section title="动态本体结构和内容" icon={BookOpen}>
            <OntologyPanel productPackage={activePackage} />
          </Section>

          <Section title="底层数据表" icon={Database}>
            <DataTables rows={sourceRows} />
          </Section>
        </div>

        <div className="workspace-right">
          <TaskPanel
            activeTab={activeTab}
            task={liveTask}
            latestResult={latestResult}
            productPackage={activePackage}
          />
          <ReceiptStatus receipt={latestReceipt} valid={receiptValid} />
        </div>
      </div>
    </main>
  );
}

createRoot(document.getElementById("root")).render(<App />);
