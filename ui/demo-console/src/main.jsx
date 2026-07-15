import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  Activity,
  BadgeCheck,
  Boxes,
  BookOpen,
  CheckCircle2,
  Code2,
  Factory,
  FileCheck2,
  KeyRound,
  Link2,
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

function Section({ title, icon: Icon, children, wide = false }) {
  return (
    <section className={`section ${wide ? "section-wide" : ""}`}>
      <div className="section-title">
        <Icon size={18} aria-hidden="true" />
        <h2>{title}</h2>
      </div>
      {children}
    </section>
  );
}

const exposureText = {
  HIDDEN: "隐藏：不进 OSDK，不可输出",
  INTERNAL_ONLY: "治理内部：只给 OntologyOps",
  COMPUTE_ONLY: "仅计算：Runtime 内部可用",
  MASKED: "脱敏：可读但需脱敏",
  AGGREGATE_ONLY: "聚合：只出摘要",
  EXTERNAL_RESULT: "结果：可作为产品输出",
};

function ProductSelector({ products, selectedProductId, onSelect }) {
  return (
    <div className="product-switcher" aria-label="选择产品">
      {Object.values(products || {}).map((product) => (
        <button
          className={product.id === selectedProductId ? "selected" : ""}
          key={product.id}
          onClick={() => onSelect(product.id)}
          title={`查看 ${product.id} 的动态本体和 OSDK`}
        >
          {product.id === "enterprise-energy-credit" ? "企业用电征信" : "长春开挖风险"}
        </button>
      ))}
    </div>
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

function OntologyExplorer({ productPackage }) {
  const ontology = productPackage?.ontology_model;
  const objects = Object.entries(ontology?.object_types || {});
  if (!ontology) {
    return <div className="empty">产品包加载后会显示动态本体。</div>;
  }
  return (
    <div className="ontology-explorer">
      <div className="explain-line">
        <strong>{ontology.ontology.display_name}</strong>
        <span>
          本体把底层表、字段、GIS 图层映射成业务对象；OSDK 只从这些对象里选择被产品策略允许的字段和动作。
        </span>
      </div>
      <div className="object-grid">
        {objects.map(([objectName, objectType]) => {
          const properties = Object.entries(objectType.properties || {});
          return (
            <div className="object-panel" key={objectName}>
              <div className="object-title">
                <strong>{objectName}</strong>
                <span>{properties.length} fields</span>
              </div>
              <table>
                <thead>
                  <tr>
                    <th>字段</th>
                    <th>类型</th>
                    <th>OSDK 暴露</th>
                  </tr>
                </thead>
                <tbody>
                  {properties.map(([propertyName, property]) => (
                    <tr key={propertyName}>
                      <td>{propertyName}</td>
                      <td>{property.type}</td>
                      <td>
                        <span className={`exposure exposure-${property.exposure}`}>
                          {property.exposure}
                        </span>
                        <small>{exposureText[property.exposure]}</small>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function OsdkPane({ productPackage }) {
  if (!productPackage) {
    return <div className="empty">选择产品后会显示 OSDK 合同。</div>;
  }
  const manifest = productPackage.product_manifest;
  const outputs = Object.keys(productPackage.product_schema.properties || {});
  const dependencies = Object.entries(
    productPackage.runtime_binding.internal_dependencies || {},
  );
  return (
    <div className="osdk-layout">
      <div className="osdk-copy">
        <strong>OSDK 如何利用动态本体</strong>
        <p>
          Compiler 从本体对象、分类分级和产品用途里裁剪接口，生成 Product OSDK。应用看到的是
          <code>{manifest.actions.join(", ")}</code>
          这样的命名动作；Runtime 才能在数据域内使用 COMPUTE_ONLY 字段。
        </p>
        <div className="flow-strip">
          <span>DOIR 本体</span>
          <Link2 size={16} />
          <span>产品投影</span>
          <Link2 size={16} />
          <span>OSDK / MCP</span>
          <Link2 size={16} />
          <span>Provider Runtime</span>
          <Link2 size={16} />
          <span>受控结果</span>
        </div>
      </div>
      <div className="code-shell">
        <div className="code-title">Generated Python OSDK</div>
        <pre>{productPackage.python_osdk}</pre>
      </div>
      <div className="osdk-facts">
        <div>
          <strong>产品输出 schema</strong>
          <ul>
            {outputs.map((field) => (
              <li key={field}>{field}</li>
            ))}
          </ul>
        </div>
        <div>
          <strong>MCP Tools</strong>
          <ul>
            {productPackage.mcp_tools.map((tool) => (
              <li key={tool.name}>{tool.name}</li>
            ))}
          </ul>
        </div>
        <div>
          <strong>Runtime 内部依赖</strong>
          <ul>
            {dependencies.map(([action, spec]) => (
              <li key={action}>
                {action}: {(spec.depends_on || []).join(", ")}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
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

function ReceiptPane({ receipt, valid }) {
  if (!receipt) {
    return (
      <div className="receipt-explainer">
        <div className="empty">执行成功后会显示最新凭证。</div>
        <div className="receipt-meaning">
          <strong>凭证是什么</strong>
          <p>
            凭证是一份签名执行证明：它记录授权、应用、产品、本体、映射、输入输出 hash 和审计链位置。
            它不保存原始数据，但能证明某次结果是在什么约束下产生的。
          </p>
        </div>
      </div>
    );
  }
  const groups = [
    {
      title: "谁、为何、用什么应用",
      fields: [
        ["request_id", "请求编号"],
        ["purpose", "被批准的用途"],
        ["requester_agent", "请求方 Agent"],
        ["provider_agent", "数据域 Runtime"],
        ["entitlement_id", "授权令牌"],
        ["application_digest", "应用包指纹"],
      ],
    },
    {
      title: "用了哪个本体和产品版本",
      fields: [
        ["ontology_version", "本体版本"],
        ["mapping_version", "映射版本"],
        ["product_version", "数据产品版本"],
        ["runtime_version", "运行时版本"],
        ["data_window", "数据时间窗口"],
      ],
    },
    {
      title: "结果是否可校验",
      fields: [
        ["input_hash", "输入 hash"],
        ["output_hash", "输出 hash"],
        ["previous_event_hash", "上一审计事件"],
        ["signature_algorithm", "签名算法"],
      ],
    },
  ];
  return (
    <div className="receipt-explainer">
      <div className={`verification ${valid ? "valid" : "unknown"}`}>
        <ShieldCheck size={18} />
        {valid ? "签名验证通过，凭证未被篡改" : "等待签名验证"}
      </div>
      <div className="receipt-groups">
        {groups.map((group) => (
          <div className="receipt-group" key={group.title}>
            <strong>{group.title}</strong>
            {group.fields.map(([field, label]) => (
              <div className="receipt-field" key={field}>
                <span>{label}</span>
                <code>{String(receipt[field])}</code>
              </div>
            ))}
          </div>
        ))}
      </div>
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
  const [selectedProductId, setSelectedProductId] = useState("enterprise-energy-credit");
  const [receiptValid, setReceiptValid] = useState(null);
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

  const productCount = Object.keys(state?.products || {}).length;
  const jobCount = Object.keys(state?.jobs || {}).length;
  const entitlementCount = Object.keys(state?.entitlements || {}).length;
  const auditCount = state?.audit_events?.length || 0;
  const activePackage = state?.product_packages?.[selectedProductId];

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

      <ProductSelector
        products={state?.products || {}}
        selectedProductId={selectedProductId}
        onSelect={setSelectedProductId}
      />

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
        <Section title="产品工厂" icon={Factory} wide>
          <ProductTable products={state?.products || {}} />
        </Section>

        <Section title="动态本体" icon={BookOpen} wide>
          <OntologyExplorer productPackage={activePackage} />
        </Section>

        <Section title="OSDK 调用面" icon={Code2} wide>
          <OsdkPane productPackage={activePackage} />
        </Section>

        <Section title="执行拓扑" icon={Boxes}>
          <Topology />
        </Section>

        <Section title="授权与作业" icon={KeyRound}>
          <JobList jobs={state?.jobs || {}} />
        </Section>

        <Section title="执行凭证" icon={FileCheck2} wide>
          <ReceiptPane receipt={latestReceipt} valid={receiptValid} />
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
