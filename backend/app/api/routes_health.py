from fastapi import APIRouter

import json

from app.models.database import SessionLocal, Workflow, AgentRun, ToolCall, Evaluation

router = APIRouter()


@router.get("/health")
async def health():
    try:
        with SessionLocal() as db:
            db.query(Workflow.workflow_id).limit(1).all()
        return {"status": "ok", "database": "ok", "vector_store": "optional"}
    except Exception:
        return {"status": "degraded", "database": "unavailable"}


@router.get("/metrics")
async def metrics():
    with SessionLocal() as db:
        workflows = db.query(Workflow).order_by(Workflow.updated_at.desc()).limit(12).all()
        runs = db.query(AgentRun).order_by(AgentRun.run_id.desc()).limit(20).all()
        calls = db.query(ToolCall).order_by(ToolCall.call_id.desc()).limit(20).all()
        evaluations = db.query(Evaluation).order_by(Evaluation.evaluation_id.desc()).limit(20).all()
        run_details = [json.loads(row.details or "{}") for row in runs]
        return {
            "workflows": db.query(Workflow).count(),
            "pending_approvals": db.query(Workflow).filter_by(status="human_review_required").count(),
            "agent_runs": db.query(AgentRun).count(),
            "tool_calls": db.query(ToolCall).count(),
            "evaluations": db.query(Evaluation).count(),
            "errors": db.query(ToolCall).filter_by(status="error").count(),
            "mean_latency_ms": round(sum(row.latency_ms for row in runs) / max(len(runs), 1), 2),
            "retrieval_count": sum(int(detail.get("retrieval_count", 0)) for detail in run_details),
            "workflow_executions": [{"workflow_id": row.workflow_id, "status": row.status, "session_id": row.session_id, "updated_at": row.updated_at.isoformat()} for row in workflows],
            "agent_executions": [{"workflow_id": row.workflow_id, "agent": row.agent, "status": row.status, "latency_ms": row.latency_ms} for row in runs],
            "tool_activity": [{"workflow_id": row.workflow_id, "tool": row.tool_name, "status": row.status} for row in calls],
            "evaluation_results": [{"workflow_id": row.workflow_id, "metric": row.metric, "score": row.score} for row in evaluations],
        }