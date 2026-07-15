import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  Activity,
  BadgeCheck,
  Boxes,
  CheckCircle2,
  Factory,
  FileCheck2,
  KeyRound,
  Network,
  Play,
  RefreshCcw,
  ShieldCheck,
} from "lucide-react";
import "./styles.css";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

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

function Metric({ label, value, tone = "neutral" }) {
  return (
    <div className={`metric metric-${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function Section({ title, icon: Icon, children }) {
  return (
    <section className="section">
      <div className="section-title">
        <Icon size={18} aria-hidden="true" />
        <h2>{title}</h2>
      </div>
      {children}
    </section>
  );
}

function ProductTable({ products }) {
  const rows = Object.values(products || {});
  return (
    <table>
      <thead>
        <tr>
          <th>产品</th>
          <th>版本</th>
          <th>用途</th>
          <th>可读字段</th>
          <th>动作</th>
          <th>原始导出</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((product) => (
          <tr key={product.id}>
            <td>{product.id}</td>
            <td>{product.product_version}</td>
            <td>{product.purpose}</td>
            <td>{product.readable_fields.length}</td>
            <td>{product.actions.join(", ")}</td>
            <td>{product.raw_export ? "允许" : "禁止"}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function JobList({ jobs }) {
  const rows = Object.values(jobs || {}).slice(-6).reverse();
  if (!rows.length) {
    return <div className="empty">还没有执行作业。点击上方按钮跑一条链路。</div>;
  }
  return (
    <div className="job-list">
      {rows.map((job) => (
        <div className="job-row" key={job.job_id}>
          <div>
            <strong>{job.product_id}</strong>
            <span>{job.provider_id} · {job.job_id}</span>
          </div>
          <span className={`status status-${job.status}`}>{job.status}</span>
        </div>
      ))}
    </div>
  );
}

function ReceiptPane({ receipt }) {
  if (!receipt) {
    return <div className="empty">执行成功后会显示最新凭证。</div>;
  }
  const fields = [
    "request_id",
    "purpose",
    "entitlement_id",
    "application_digest",
    "ontology_version",
    "mapping_version",
    "product_version",
    "input_hash",
    "output_hash",
    "previous_event_hash",
    "signature_algorithm",
  ];
  return (
    <div className="receipt-grid">
      {fields.map((field) => (
        <div key={field}>
          <span>{field}</span>
          <strong>{String(receipt[field])}</strong>
        </div>
      ))}
    </div>
  );
}

function Topology() {
  const nodes = [
    ["Agent", "需求方编排"],
    ["Catalog", "产品发现"],
    ["Policy", "用途授权"],
    ["OSDK", "命名接口"],
    ["Runtime", "数据域执行"],
    ["Receipt", "签名凭证"],
  ];
  return (
    <div className="topology" aria-label="执行拓扑">
      {nodes.map(([name, desc], index) => (
        <React.Fragment key={name}>
          <div className="topology-node">
            <strong>{name}</strong>
            <span>{desc}</span>
          </div>
          {index < nodes.length - 1 && <div className="topology-line" />}
        </React.Fragment>
      ))}
    </div>
  );
}

function App() {
  const [state, setState] = useState(null);
  const [latestResult, setLatestResult] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState("");

  async function refresh() {
    const next = await api("/demo/state");
    setState(next);
  }

  useEffect(() => {
    refresh().catch((err) => setError(err.message));
  }, []);

  async function runAction(name, path, payload) {
    setBusy(name);
    setError("");
    try {
      const result = await api(path, {
        method: "POST",
        body: payload ? JSON.stringify(payload) : undefined,
      });
      setLatestResult(result);
      await refresh();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy("");
    }
  }

  const latestReceipt = useMemo(() => {
    if (!latestResult) return null;
    if (latestResult.jobs?.length) return latestResult.jobs.at(-1).receipt;
    return latestResult.receipt || null;
  }, [latestResult]);

  const productCount = Object.keys(state?.products || {}).length;
  const jobCount = Object.keys(state?.jobs || {}).length;
  const entitlementCount = Object.keys(state?.entitlements || {}).length;
  const auditCount = state?.audit_events?.length || 0;

  return (
    <main>
      <header className="app-header">
        <div>
          <p className="eyebrow">Dynamic Ontology OSDK</p>
          <h1>可信数据产品流转 Demo Console</h1>
        </div>
        <button className="icon-button" onClick={refresh} title="刷新状态">
          <RefreshCcw size={18} />
          刷新
        </button>
      </header>

      {error && <div className="error">{error}</div>}

      <div className="metrics">
        <Metric label="产品" value={productCount} tone="blue" />
        <Metric label="授权" value={entitlementCount} tone="green" />
        <Metric label="作业" value={jobCount} tone="amber" />
        <Metric label="审计事件" value={auditCount} tone="slate" />
      </div>

      <section className="action-bar">
        <button
          onClick={() =>
            runAction("power", "/demo/run/power-credit", {
              enterprise_id: "91300000DEMO0007",
            })
          }
          disabled={Boolean(busy)}
          title="运行企业用电征信双 Provider 链路"
        >
          <Play size={18} />
          企业征信链路
        </button>
        <button
          onClick={() => runAction("changchun", "/demo/run/changchun")}
          disabled={Boolean(busy)}
          title="运行长春开挖风险评估"
        >
          <Network size={18} />
          长春开挖风险
        </button>
        <button
          onClick={() =>
            runAction("recompile", "/demo/recompile-coordinate-core")
          }
          disabled={Boolean(busy)}
          title="将管线精确坐标升级为核心数据并重新编译产品"
        >
          <ShieldCheck size={18} />
          坐标升为核心数据
        </button>
        {busy && <span className="busy">正在执行 {busy}...</span>}
      </section>

      <div className="layout">
        <Section title="产品工厂" icon={Factory}>
          <ProductTable products={state?.products || {}} />
        </Section>

        <Section title="执行拓扑" icon={Boxes}>
          <Topology />
        </Section>

        <Section title="授权与作业" icon={KeyRound}>
          <JobList jobs={state?.jobs || {}} />
        </Section>

        <Section title="执行凭证" icon={FileCheck2}>
          <ReceiptPane receipt={latestReceipt} />
        </Section>

        <Section title="治理状态" icon={BadgeCheck}>
          <div className="governance">
            <div>
              <CheckCircle2 size={18} />
              分类分级参与产品编译
            </div>
            <div>
              <CheckCircle2 size={18} />
              Product OSDK 不暴露自由 SQL
            </div>
            <div>
              <CheckCircle2 size={18} />
              Provider Runtime 返回受控摘要
            </div>
            <div>
              <Activity size={18} />
              管线坐标核心数据状态：{state?.coordinate_core ? "已升级" : "未升级"}
            </div>
          </div>
        </Section>
      </div>
    </main>
  );
}

createRoot(document.getElementById("root")).render(<App />);

