from datetime import datetime

from langgraph.types import interrupt

from app.agents.action import execute_proposed_action
from app.agents.data_retrieval import retrieve_case_data
from app.agents.investigation import investigate_case
from app.agents.response import compose_response
from app.agents.retrieval import retrieve_policy_context
from app.agents.triage import triage_request
from app.agents.validator import validate_state
from app.models.schemas import ProposedAction


def triage_node(state: dict) -> dict:
    triage = triage_request(state["user_query"]).model_dump()
    entities = {**triage["entities"]}
    return {"triage": triage, "intent": triage["intent"], "entities": entities, "confidence": triage["confidence"], "current_stage": "triage"}


def retrieval_node(state: dict) -> dict:
    entities = dict(state.get("entities", {}))
    data = retrieve_case_data(entities)
    return {"entities": entities, "retrieved_data": data, "tool_call_log": state.get("tool_call_log", []) + data.get("tool_call_log", []), "errors": state.get("errors", []) + data.get("errors", []), "current_stage": "data_retrieval"}


def policy_node(state: dict) -> dict:
    category = state.get("triage", {}).get("category", "return inquiry")
    docs = retrieve_policy_context(state.get("user_query", ""), category)
    return {"retrieved_documents": docs, "current_stage": "policy_retrieval"}


def investigation_node(state: dict) -> dict:
    result = investigate_case(
        state.get("user_query", ""),
        state.get("triage", {}).get("category", "unknown"),
        state.get("retrieved_data", {}),
        state.get("retrieved_documents", []),
        state.get("triage", {}).get("missing_information", []),
    ).model_dump()
    order = state.get("retrieved_data", {}).get("order") or {}
    recommendation = result["recommended_action"]
    action_type = "refund_review_request" if recommendation == "request_refund" else "replacement_review_request" if recommendation == "request_replacement" else "operations_escalation" if recommendation in {"specialist_review", "human_review", "shipment_investigation", "investigate_refund_status"} else "return_case"
    action = ProposedAction(
        action_type=action_type,
        description=recommendation.replace("_", " "),
        requires_approval=result["requires_human_review"],
        expected_impact=f"Creates a review record for order {order.get('order_id', 'not identified')}; does not issue funds or reserve inventory.",
        parameters={"amount": order.get("total", 0)} if action_type == "refund_review_request" else {},
    ).model_dump()
    return {"investigation_result": result, "confidence": result["confidence"], "proposed_actions": [action], "current_stage": "investigation"}


def validation_node(state: dict) -> dict:
    result = validate_state(state).model_dump()
    return {"validation_result": result, "current_stage": "validation"}


def approval_node(state: dict) -> dict:
    decision = interrupt({
        "workflow_id": state["workflow_id"],
        "proposed_action": (state.get("proposed_actions") or [{}])[0],
        "evidence": (state.get("investigation_result") or {}).get("evidence", []),
        "policy_sources": state.get("retrieved_documents", []),
        "confidence": state.get("confidence", 0),
        "expected_impact": (state.get("proposed_actions") or [{}])[0].get("expected_impact", ""),
    })
    if isinstance(decision, str):
        decision = {"decision": decision}
    modified = decision.get("modified_action")
    if modified:
        decision["modified_action"] = ProposedAction.model_validate(modified).model_dump()
    return {"human_approval": decision, "current_stage": "human_approval"}


def action_node(state: dict) -> dict:
    results = execute_proposed_action(state)
    action_log = [{"tool": result.get("action_type", "business_action"), "status": "success" if result.get("success") else "error", "error": result.get("error")} for result in results]
    return {"tool_results": results, "completed_actions": results, "tool_call_log": state.get("tool_call_log", []) + action_log, "current_stage": "action"}


def post_action_validation_node(state: dict) -> dict:
    result = validate_state(state, after_action=True).model_dump()
    return {"validation_result": result, "current_stage": "post_action_validation"}


def retry_node(state: dict) -> dict:
    return {"retry_count": state.get("retry_count", 0) + 1, "current_stage": "retrieval_retry"}


def response_node(state: dict) -> dict:
    status = state.get("status", "completed")
    if status == "running":
        status = "blocked" if state.get("validation_result", {}).get("decision") == "BLOCK" else "completed"
    return {"final_response": compose_response({**state, "status": status}), "status": status, "current_stage": "response"}
