"use client";

import Link from "next/link";
import { useState } from "react";
import { ArrowUpRight, Check, CircleAlert, Clock3, Database, FileSearch, GitBranch, LoaderCircle, MessageSquareText, PackageCheck, RotateCcw, ShieldCheck, Sparkles, Truck, X } from "lucide-react";
import { decideApproval, runInvestigation } from "@/lib/api";
import type { AgentResponse, ProposedAction } from "@/types/api";

const examples = [
  "My order ORD1001 arrived damaged. Can I return it?",
  "My order ORD1002 was delivered 37 days ago and I want a refund.",
  "I received the wrong product for order ORD1003.",
  "My refund for ORD1004 has not arrived.",
  "I want a refund for a high-value product. Order ORD1005.",
  "The product is outside the return window, but it was damaged during delivery. ORD1002",
  "I don't remember my order ID.",
];

const stages = [
  { id: "triage", title: "Triage", icon: MessageSquareText },
  { id: "data_retrieval", title: "Data retrieval", icon: Database },
  { id: "policy_retrieval", title: "Policy retrieval", icon: FileSearch },
  { id: "investigation", title: "Investigation", icon: GitBranch },
  { id: "validation", title: "Validation", icon: ShieldCheck },
  { id: "human_approval", title: "Human approval", icon: Check },
  { id: "action", title: "Action", icon: PackageCheck },
  { id: "response", title: "Response", icon: Sparkles },
];

function WorkflowRail({ result }: { result: AgentResponse | null }) {
  const active = result?.workflow_state.current_stage;
  const reviewIndex = stages.findIndex((stage) => stage.id === "human_approval");
  const activeIndex = stages.findIndex((stage) => stage.id === active);
  return <div className="workflow-rail">{stages.map((stage, index) => {
    const reached = result && (index < activeIndex || (result.status === "completed" && index !== reviewIndex));
    const isCurrent = result?.status === "human_review_required" ? stage.id === "human_approval" : stage.id === active;
    const Icon = stage.icon;
    return <div className={`rail-step ${reached ? "is-done" : ""} ${isCurrent ? "is-current" : ""}`} key={stage.id}>
      <span className="rail-icon"><Icon size={15} strokeWidth={1.8} /></span><span>{stage.title}</span>
      {index < stages.length - 1 && <span className="rail-connector" />}
    </div>;
  })}</div>;
}

function SourceCard({ source }: { source: AgentResponse["policy_sources"][number] }) {
  return <article className="source-card">
    <div className="source-meta"><span className="source-code">{source.document_id}</span><span>v{source.version}</span></div>
    <h3>{source.title}</h3><p className="source-section">{source.section} · Effective {source.effective_date}</p>
    <p className="source-excerpt">{source.excerpt}</p><span className="citation">{source.citation}</span>
  </article>;
}

export default function Home() {
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<AgentResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [sessionId, setSessionId] = useState<string>();
  const [modifyMode, setModifyMode] = useState(false);
  const [modifiedType, setModifiedType] = useState("return_case");

  async function submit(text = query) {
    if (!text.trim() || busy) return;
    setBusy(true); setError(""); setQuery(text);
    try {
      const response = await runInvestigation(text, sessionId);
      setResult(response); setSessionId(response.session_id); setModifyMode(false);
    } catch (caught) { setError(caught instanceof Error ? caught.message : "The investigation could not be started."); }
    finally { setBusy(false); }
  }

  async function approval(decision: "approve" | "reject" | "modify") {
    if (!result || busy) return;
    setBusy(true); setError("");
    const action: ProposedAction | undefined = decision === "modify" ? {
      ...(result.recommended_action || { action_type: modifiedType, description: "Modified review action", requires_approval: true, expected_impact: "Creates an operations review record.", parameters: {} }),
      action_type: modifiedType,
    } : undefined;
    try { setResult(await decideApproval(result.workflow_id, decision, action)); setModifyMode(false); }
    catch (caught) { setError(caught instanceof Error ? caught.message : "Approval could not be submitted."); }
    finally { setBusy(false); }
  }

  const currentStatus = result?.status === "human_review_required" ? "Approval needed" : result?.status === "completed" ? "Investigation complete" : "Ready for a case";

  return <main className="app-shell">
    <aside className="sidebar">
      <div className="brand"><div className="brand-mark"><RotateCcw size={19} /></div><div><span className="brand-title">Northstar</span><span className="brand-sub">RETURNS OPERATIONS</span></div></div>
      <div className="workspace-label">WORKSPACE</div>
      <Link className="nav-link nav-active" href="/"><GitBranch size={17} /> Case investigation <span className="nav-count">01</span></Link>
      <Link className="nav-link" href="/admin"><Clock3 size={17} /> Evaluations</Link>
      <div className="sidebar-bottom"><div className="connected-dot"><span /> All systems operational</div><div className="user-profile"><div className="avatar">OM</div><div><strong>Operations Manager</strong><small>Returns team</small></div><ArrowUpRight size={14} /></div></div>
    </aside>

    <section className="main-area">
      <header className="topbar"><div className="breadcrumb">Operations <span>/</span> Returns <span>/</span> <strong>Investigation desk</strong></div><div className="topbar-right"><span className="environment-tag"><span /> DEMO ENVIRONMENT</span><div className="date-label">{new Intl.DateTimeFormat("en", { weekday: "short", month: "short", day: "numeric" }).format(new Date())}</div></div></header>
      <div className="page-content">
        <div className="page-heading"><div><div className="eyebrow"><span className="eyebrow-line" /> CASEWORK / 01</div><h1>Return investigation</h1><p>Review the record, policy, and next best action before anything changes.</p></div><div className="case-status"><span className={`status-dot ${result?.status === "human_review_required" ? "status-amber" : ""}`} />{currentStatus}</div></div>

        <section className="workflow-panel" aria-label="Workflow progress"><div className="panel-topline"><div><span className="panel-kicker">AGENT WORKFLOW</span><strong>{result?.workflow_id || "No active workflow"}</strong></div><span className="workflow-progress-label">{result ? result.workflow_state.current_stage.replaceAll("_", " ") : "Awaiting request"}</span></div><WorkflowRail result={result} /></section>

        <div className="investigation-grid">
          <section className="request-column">
            <div className="section-heading"><div><span className="panel-kicker">NEW INVESTIGATION</span><h2>What happened?</h2></div><span className="count-label">{result ? `CASE ${result.classification.replaceAll("_", " ").toUpperCase()}` : "INTAKE"}</span></div>
            <form className="request-form" onSubmit={(event) => { event.preventDefault(); void submit(); }}>
              <label htmlFor="request">Customer statement</label><textarea id="request" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Describe the return issue and include an order number if available…" rows={4} maxLength={4000} />
              <div className="form-footer"><span>{query.length}/4,000</span><button className="primary-button" disabled={busy || query.trim().length < 3} type="submit">{busy ? <LoaderCircle className="spin" size={16} /> : <FileSearch size={16} />}{busy ? "Investigating" : "Investigate case"}</button></div>
            </form>
            <div className="examples"><div className="examples-heading">QUICK SCENARIOS <span>7</span></div>{examples.map((example, index) => <button className="example-row" key={example} onClick={() => void submit(example)} disabled={busy}><span className="example-number">0{index + 1}</span><span>{example}</span><ArrowUpRight size={14} /></button>)}</div>
            {error && <div role="alert" className="error-banner"><CircleAlert size={16} />{error}</div>}
          </section>

          <section className="evidence-column">
            <div className="section-heading"><div><span className="panel-kicker">CASE FILE</span><h2>Evidence & decision</h2></div>{result && <span className="confidence"><span>{Math.round(result.confidence * 100)}%</span> confidence</span>}</div>
            {!result ? <div className="empty-state"><div className="empty-icon"><FileSearch size={21} /></div><strong>Investigation evidence will appear here</strong><p>Submit a case to retrieve operational records and applicable policy.</p><span>TOOL-GROUNDED · CITED · APPROVAL-GATED</span></div> : <>
              <div className="classification-strip"><div><span className="field-label">CLASSIFICATION</span><strong>{result.classification.replaceAll("_", " ")}</strong></div><div><span className="field-label">INTENT</span><strong>{result.intent.replaceAll("_", " ")}</strong></div><div><span className="field-label">WORKFLOW</span><strong>{result.workflow_id}</strong></div></div>
              <div className="evidence-list"><div className="subheading"><span>Verified evidence</span><span>{result.evidence.length} items</span></div>{result.evidence.length ? result.evidence.map((item, index) => <div className="evidence-item" key={`${item}-${index}`}><span className="evidence-check"><Check size={12} /></span><p>{item}</p></div>) : <p className="muted-note">No account records were accessed.</p>}</div>
              <div className="recommendation"><div className="recommendation-icon"><Sparkles size={16} /></div><div><span className="field-label">RECOMMENDED RESOLUTION</span><strong>{result.recommended_action?.description || "Request more information"}</strong><p>{result.recommended_action?.expected_impact || "No account action is proposed."}</p></div></div>
              {result.approval_required && <section className="approval-box"><div className="approval-title"><div className="approval-symbol"><ShieldCheck size={17} /></div><div><span className="panel-kicker">HUMAN REVIEW REQUIRED</span><h3>Authorize proposed action</h3></div><span className="pending-pill">PENDING</span></div><p className="approval-reason">Policy exception, value, risk, or confidence criteria require an operations decision. The workflow is paused; no business action has run.</p><div className="approval-impact"><span>EXPECTED IMPACT</span><p>{result.recommended_action?.expected_impact}</p></div>{modifyMode && <label className="modify-select">Modified action<select value={modifiedType} onChange={(event) => setModifiedType(event.target.value)}><option value="return_case">Open return case</option><option value="operations_escalation">Escalate to operations</option><option value="refund_review_request">Request refund review</option><option value="replacement_review_request">Request replacement review</option></select></label>}<div className="approval-actions"><button className="approve-button" disabled={busy} onClick={() => void approval("approve")}><Check size={15} /> Approve</button><button className="reject-button" disabled={busy} onClick={() => void approval("reject")}><X size={15} /> Reject</button><button className="modify-button" disabled={busy} onClick={() => modifyMode ? void approval("modify") : setModifyMode(true)}>{modifyMode ? "Confirm edit" : "Modify"}</button></div></section>}
              {!result.approval_required && result.completed_actions.length > 0 && <div className="completed-banner"><Check size={15} /><span>Action confirmed by tool · {result.completed_actions[0].action_id}</span></div>}
              <div className="response-card"><div className="response-head"><Sparkles size={15} /><span>GROUNDED CUSTOMER RESPONSE</span></div><pre>{result.final_response}</pre></div>
            </>}
          </section>

          <aside className="sources-column"><div className="sources-head"><div><span className="panel-kicker">KNOWLEDGE BASE</span><h2>Policy sources</h2></div><span className="source-count">{result?.policy_sources.length ?? 0}</span></div>{result?.policy_sources.length ? <div className="sources-list">{result.policy_sources.map((source, index) => <SourceCard source={source} key={`${source.document_id}-${index}`} />)}</div> : <div className="sources-empty"><FileSearch size={18} /><p>Applicable policy citations appear with the investigation.</p></div>}
            {result && <div className="tool-activity"><div className="subheading"><span>Tool activity</span><Truck size={15} /></div>{result.workflow_state.tool_results.length ? result.workflow_state.tool_results.map((item, index) => <div className="tool-row" key={index}><span className="tool-state"><Check size={11} /></span><span>Business action</span><span className="tool-result">confirmed</span></div>) : <><div className="tool-row"><span className="tool-state"><Check size={11} /></span><span>Operational lookups</span><span className="tool-result">complete</span></div><div className="tool-row"><span className="tool-state"><Check size={11} /></span><span>Policy retrieval</span><span className="tool-result">{result.policy_sources.length} sources</span></div></>}</div>}
          </aside>
        </div>
        <footer className="page-footer"><span>Decisions stay with your team.</span><span>Agentic Returns Assistant <i /> Audit trail enabled</span></footer>
      </div>
    </section>
  </main>;
}