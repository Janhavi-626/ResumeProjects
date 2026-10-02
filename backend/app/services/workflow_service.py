import json
import logging
import time
from datetime import datetime
from uuid import uuid4

from langgraph.types import Command

from app.graph.workflow import get_workflow
from app.models.database import AgentRun, Approval, AuditLog, Message, SessionLocal, SessionRecord, ToolCall, Workflow
from app.models.schemas import AgentResponse, PolicySource, ProposedAction, WorkflowStatus
from app.services.memory_service import append_message

logger = logging.getLogger("returns.workflow")


def _as_json(value) -> str:
    return json.dumps(value, default=str)


def _save_state(workflow_id: str, session_id: str, user_id: str, state: dict, status: str, latency_ms: float = 0) -> None:
    safe_state = {key: value for key, value in state.items() if key != "__interrupt__"}
    safe_state["status"] = status
    with SessionLocal() as db:
        record = db.get(Workflow, workflow_id)
        if record:
            record.status = status
            record.state_json = _as_json(safe_state)
            record.updated_at = datetime.utcnow()
        else:
            db.add(Workflow(workflow_id=workflow_id, session_id=session_id, user_id=user_id, status=status, state_json=_as_json(safe_state)))
        db.add(AuditLog(audit_id=str(uuid4()), workflow_id=workflow_id, event="workflow_state_saved", details=_as_json({"status": status, "current_stage": state.get("current_stage")})))
        db.add(AgentRun(run_id=str(uuid4()), workflow_id=workflow_id, agent="langgraph_supervisor", status=status, latency_ms=latency_ms, details=_as_json({"current_stage": state.get("current_stage"), "retrieval_count": len(state.get("retrieved_documents", [])), "human_review": status == WorkflowStatus.HUMAN_REVIEW.value})))
        call_log = state.get("tool_call_log", [])
        if not call_log:
            call_log = [{"tool": result.get("action_type", "business_action"), "status": "success" if result.get("success") else "error", "result": result} for result in state.get("tool_results", [])]
        for index, call in enumerate(call_log):
            call_id = f"{workflow_id}:{call.get('tool', 'tool')}"
            record = db.get(ToolCall, call_id)
            details = {key: value for key, value in call.items() if key != "tool"}
            if record is None:
                db.add(ToolCall(call_id=call_id, workflow_id=workflow_id, tool_name=call.get("tool", f"tool_{index}"), status=call.get("status", "unknown"), result=_as_json(details)))
            else:
                record.status = call.get("status", record.status)
                record.result = _as_json(details)
        db.commit()


def _format_response(state: dict, status: str, workflow_id: str, session_id: str) -> AgentResponse:
    triage = state.get("triage", {})
    findings = state.get("investigation_result", {})
    sources = [
        PolicySource(
            document_id=str(source.get("document_id", "")),
            title=str(source.get("title", "Policy source")),
            source=str(source.get("source", "")),
            category=str(source.get("category", "")),
            page=int(source.get("page", 1)),
            section=str(source.get("section", "")),
            version=str(source.get("version", "")),
            effective_date=str(source.get("effective_date", "")),
            excerpt=str(source.get("text", "")),
            citation=str(source.get("citation", "")),
        )
        for source in state.get("retrieved_documents", [])
    ]
    actions = state.get("proposed_actions", [])
    approval_required = status == WorkflowStatus.HUMAN_REVIEW.value
    return AgentResponse(
        workflow_id=workflow_id,
        session_id=session_id,
        status=status,
        intent=state.get("intent", "return_exception"),
        classification=findings.get("issue_type", triage.get("category", "unknown")),
        confidence=float(state.get("confidence", 0)),
        evidence=findings.get("evidence", []),
        policy_sources=sources,
        recommended_action=ProposedAction.model_validate(actions[0]) if actions else None,
        approval_required=approval_required,
        completed_actions=state.get("completed_actions", []),
        pending_actions=actions if approval_required else [],
        final_response=state.get("final_response", ""),
        workflow_state={
            "current_stage": "human_approval" if approval_required else state.get("current_stage", "response"),
            "agent_status": ["triage", "data_retrieval", "policy_retrieval", "investigation", "validation", "human_approval" if approval_required else "action", "response"],
            "tool_results": state.get("tool_results", []),
            "tool_activity": state.get("tool_call_log", []),
            "errors": state.get("errors", []),
            "validation_result": state.get("validation_result", {}),
        },
    )


def run_workflow(message: str, user_id: str, session_id: str | None = None) -> AgentResponse:
    started = time.perf_counter()
    workflow_id = f"WF-{uuid4().hex[:12].upper()}"
    session_id = session_id or f"SES-{uuid4().hex[:12].upper()}"
    with SessionLocal() as db:
        if not db.get(SessionRecord, session_id):
            db.add(SessionRecord(session_id=session_id, user_id=user_id))
        db.add(Message(message_id=str(uuid4()), session_id=session_id, role="user", content=message[:4000]))
        db.commit()
    append_message(session_id, "user", message)
    initial = {
        "workflow_id": workflow_id,
        "session_id": session_id,
        "user_id": user_id,
        "user_query": message,
        "conversation_history": [],
        "retry_count": 0,
        "errors": [],
        "tool_results": [],
        "completed_actions": [],
        "human_approval": None,
        "status": "running",
    }
    config = {"configurable": {"thread_id": workflow_id}}
    result = get_workflow().invoke(initial, config=config)
    if result.get("__interrupt__"):
        status = WorkflowStatus.HUMAN_REVIEW.value
        pending_payload = result["__interrupt__"][0].value
        result["pending_approval"] = pending_payload
        from app.agents.response import compose_response

        result["status"] = status
        result["final_response"] = compose_response(result)
    else:
        status = result.get("status", WorkflowStatus.COMPLETED.value)
        if result.get("validation_result", {}).get("decision") == "BLOCK":
            status = WorkflowStatus.BLOCKED.value
    _save_state(workflow_id, session_id, user_id, result, status, (time.perf_counter() - started) * 1000)
    append_message(session_id, "assistant", result.get("final_response", ""))
    with SessionLocal() as db:
        db.add(Message(message_id=str(uuid4()), session_id=session_id, role="assistant", content=result.get("final_response", "")[:4000]))
        db.commit()
    logger.info("workflow completed", extra={"workflow_id": workflow_id, "session_id": session_id, "status": status, "retrieval_count": len(result.get("retrieved_documents", [])), "human_review": status == WorkflowStatus.HUMAN_REVIEW.value})
    return _format_response(result, status, workflow_id, session_id)


def approve_workflow(workflow_id: str, decision: str, reviewer: str, comment: str, modified_action: dict | None = None) -> AgentResponse:
    started = time.perf_counter()
    normalized = decision.lower()
    if normalized not in {"approve", "reject", "modify"}:
        raise ValueError("decision must be approve, reject, or modify")
    if normalized == "modify" and not modified_action:
        raise ValueError("modified_action is required for modify decisions")
    if modified_action:
        ProposedAction.model_validate(modified_action)
    with SessionLocal() as db:
        record = db.get(Workflow, workflow_id)
        if not record:
            raise LookupError("workflow not found")
        if record.status != WorkflowStatus.HUMAN_REVIEW.value:
            raise ValueError("workflow is not waiting for human approval")
        state = json.loads(record.state_json)
        db.add(Approval(approval_id=str(uuid4()), workflow_id=workflow_id, decision=normalized, reviewer=reviewer[:120], comment=comment[:1000]))
        db.add(AuditLog(audit_id=str(uuid4()), workflow_id=workflow_id, event="human_approval", details=_as_json({"decision": normalized, "reviewer": reviewer[:120]})))
        db.commit()
    payload = {"decision": normalized}
    if modified_action:
        payload["modified_action"] = modified_action
    config = {"configurable": {"thread_id": workflow_id}}
    graph = get_workflow()
    checkpoint = graph.get_state(config)
    if checkpoint.values and checkpoint.next:
        result = graph.invoke(Command(resume=payload), config=config)
    else:
        restored = {key: value for key, value in state.items() if key != "pending_approval"}
        restored.update({"status": "running", "human_approval": payload, "workflow_id": workflow_id})
        result = graph.invoke(restored, config=config)
    status = result.get("status", WorkflowStatus.COMPLETED.value)
    if result.get("validation_result", {}).get("decision") == "BLOCK":
        status = WorkflowStatus.BLOCKED.value
    _save_state(workflow_id, state["session_id"], state["user_id"], result, status, (time.perf_counter() - started) * 1000)
    with SessionLocal() as db:
        db.add(Message(message_id=str(uuid4()), session_id=state["session_id"], role="assistant", content=result.get("final_response", "")[:4000]))
        db.commit()
    return _format_response(result, status, workflow_id, state["session_id"])


def get_workflow_record(workflow_id: str) -> dict | None:
    with SessionLocal() as db:
        record = db.get(Workflow, workflow_id)
        if not record:
            return None
        state = json.loads(record.state_json)
        response = _format_response(state, record.status, record.workflow_id, record.session_id)
        return {**response.model_dump(mode="json"), "created_at": record.created_at.isoformat(), "updated_at": record.updated_at.isoformat(), "pending_approval": state.get("pending_approval")}
