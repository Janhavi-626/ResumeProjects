"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Activity, ArrowLeft, CheckCircle2, Clock3, ShieldAlert, Workflow } from "lucide-react";

type Metrics = {
  workflows: number;
  pending_approvals: number;
  agent_runs: number;
  tool_calls: number;
  evaluations: number;
  errors: number;
  mean_latency_ms: number;
  retrieval_count: number;
  workflow_executions: { workflow_id: string; status: string; updated_at: string }[];
  agent_executions: { workflow_id: string; agent: string; status: string; latency_ms: number }[];
  tool_activity: { workflow_id: string; tool: string; status: string }[];
  evaluation_results: { metric: string; score: number }[];
};

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

export default function AdminPage() {
  const [metrics, setMetrics] = useState<Metrics>();
  const [error, setError] = useState("");
  useEffect(() => {
    fetch(`${API}/api/metrics`, { cache: "no-store" })
      .then((response) => response.json())
      .then(setMetrics)
      .catch(() => setError("Metrics service is unavailable."));
  }, []);

  const cards = [
    { label: "Workflow executions", value: metrics?.workflows ?? "—", icon: Workflow, note: "Persisted investigations" },
    { label: "Human review queue", value: metrics?.pending_approvals ?? "—", icon: ShieldAlert, note: "Awaiting authorization" },
    { label: "Tool actions", value: metrics?.tool_calls ?? "—", icon: Activity, note: "Recorded tool invocations" },
    { label: "Recorded errors", value: metrics?.errors ?? "—", icon: ShieldAlert, note: "Failed tool calls" },
    { label: "Mean latency", value: metrics ? `${Math.round(metrics.mean_latency_ms)} ms` : "—", icon: Clock3, note: "Recent workflow runs" },
    { label: "Retrieved sources", value: metrics?.retrieval_count ?? "—", icon: Activity, note: "Cited policy chunks" },
    { label: "Evaluation metrics", value: metrics?.evaluations ?? "—", icon: CheckCircle2, note: "Persisted quality scores" },
  ];

  return <main className="admin-shell">
    <header className="admin-topbar"><Link href="/" className="back-link"><ArrowLeft size={16} /> Investigation desk</Link><span className="environment-tag"><span /> DEMO ENVIRONMENT</span></header>
    <section className="admin-content">
      <div className="eyebrow"><span className="eyebrow-line" /> QUALITY / 02</div>
      <h1>System observability</h1>
      <p className="admin-intro">Execution health and workflow oversight for the returns assistant.</p>
      <div className="metrics-grid">{cards.map(({ label, value, icon: Icon, note }) => <article className="metric-card" key={label}><div className="metric-top"><span>{label}</span><Icon size={17} /></div><strong>{value}</strong><small>{note}</small></article>)}</div>
      {error && <p role="alert" className="error-banner">{error}</p>}

      <section className="admin-section">
        <div className="admin-section-title"><div><span className="panel-kicker">OPERATIONAL HEALTH</span><h2>Service status</h2></div><span className="healthy-pill"><i /> Running</span></div>
        <div className="health-table"><div><span>Supervisor graph</span><b><CheckCircle2 size={15} /> Available</b></div><div><span>Relational store</span><b><CheckCircle2 size={15} /> Connected</b></div><div><span>Policy retrieval</span><b><CheckCircle2 size={15} /> Local fallback ready</b></div><div><span>Approval interrupts</span><b><CheckCircle2 size={15} /> Checkpointed</b></div></div>
      </section>

      <section className="admin-section">
        <div className="admin-section-title"><div><span className="panel-kicker">RECENT RUNS</span><h2>Workflow executions</h2></div><Workflow size={17} /></div>
        <div className="execution-list">{metrics?.workflow_executions.length ? metrics.workflow_executions.map((row) => <div className="execution-row" key={row.workflow_id}><code>{row.workflow_id}</code><span>{row.status.replaceAll("_", " ")}</span><time>{new Date(row.updated_at).toLocaleString()}</time></div>) : <p className="empty-admin">No workflow executions recorded yet.</p>}</div>
      </section>

      <div className="admin-columns">
        <section className="admin-section">
          <div className="admin-section-title"><div><span className="panel-kicker">AGENT ACTIVITY</span><h2>Agent executions</h2></div><Activity size={17} /></div>
          <div className="execution-list">{metrics?.agent_executions.length ? metrics.agent_executions.map((row, index) => <div className="execution-row" key={`${row.workflow_id}-${index}`}><code>{row.agent}</code><span>{row.status.replaceAll("_", " ")}</span><time>{Math.round(row.latency_ms)} ms</time></div>) : <p className="empty-admin">No agent runs recorded yet.</p>}</div>
        </section>
        <section className="admin-section">
          <div className="admin-section-title"><div><span className="panel-kicker">TOOL AUDIT</span><h2>Business tool calls</h2></div><ShieldAlert size={17} /></div>
          <div className="execution-list">{metrics?.tool_activity.length ? metrics.tool_activity.map((row, index) => <div className="execution-row" key={`${row.workflow_id}-${index}`}><code>{row.tool}</code><span>{row.status}</span><time>{row.workflow_id}</time></div>) : <p className="empty-admin">No business actions recorded yet.</p>}</div>
        </section>
      </div>

      <section className="admin-section">
        <div className="admin-section-title"><div><span className="panel-kicker">QUALITY CONTROLS</span><h2>Evaluation results</h2></div><Clock3 size={17} /></div>
        {metrics?.evaluation_results.length ? <div className="evaluation-list">{metrics.evaluation_results.map((row) => <div key={row.metric}><span className="eval-index">EVAL</span><span>{row.metric.replaceAll("_", " ")}</span><strong className="eval-score">{row.score.toFixed(3)}</strong></div>)}</div> : <div className="evaluation-list">{["Intent classification", "Citation correctness", "Tool selection and arguments", "Policy compliance", "Human escalation correctness", "Grounded response usefulness"].map((item, index) => <div key={item}><span className="eval-index">0{index + 1}</span><span>{item}</span><span className="eval-ready">DATASET READY</span></div>)}</div>}
      </section>
      <p className="admin-footnote">Evaluation runs use synthetic cases and persist scores through <code>python -m evaluation.runner</code>.</p>
    </section>
  </main>;
}
