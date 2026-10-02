from app.tools import business_tools


def execute_proposed_action(state: dict) -> list[dict]:
    if state.get("triage", {}).get("missing_information"):
        return []
    investigation = state.get("investigation_result", {})
    if state.get("human_approval") is None and investigation.get("requires_human_review"):
        return []
    approval = state.get("human_approval") or {}
    if approval.get("decision") == "reject":
        return []
    action = approval.get("modified_action") or (state.get("proposed_actions") or [{}])[0]
    action_type = action.get("action_type", "return_case")
    order = state.get("retrieved_data", {}).get("order") or {}
    entities = state.get("entities", {})
    workflow_id = state["workflow_id"]
    payload = {"order_id": entities.get("order_id"), "action": action}
    key = business_tools.make_idempotency_key(workflow_id, action_type, payload)
    if action_type == "refund_review_request":
        result = business_tools.request_refund(workflow_id, entities.get("customer_id", "unknown"), entities["order_id"], float(action.get("parameters", {}).get("amount", order.get("total", 0))), key)
    elif action_type == "replacement_review_request":
        result = business_tools.request_replacement(workflow_id, entities.get("customer_id", "unknown"), entities["order_id"], entities.get("product_id", "unknown"), key)
    elif action_type == "operations_escalation":
        result = business_tools.create_escalation(workflow_id, entities.get("customer_id", "unknown"), entities.get("order_id"), investigation.get("summary", "Operations review requested."), key)
    else:
        result = business_tools.create_return_case(workflow_id, entities.get("customer_id", "unknown"), entities["order_id"], investigation.get("summary", "Return investigation opened."), key)
    return [result]