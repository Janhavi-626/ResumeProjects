from uuid import uuid4

from app.graph.edges import after_validation
from app.graph.workflow import get_workflow


def _run(query: str):
    workflow_id = f"WF-{uuid4().hex[:10]}"
    state = {
        "workflow_id": workflow_id,
        "session_id": "test-session",
        "user_id": "test-user",
        "user_query": query,
        "retry_count": 0,
        "errors": [],
        "tool_results": [],
        "completed_actions": [],
        "human_approval": None,
        "status": "running",
    }
    return get_workflow().invoke(state, {"configurable": {"thread_id": workflow_id}})


def test_normal_case_executes_only_after_pass_validation():
    result = _run("Please return order ORD1010")
    assert result["status"] == "completed"
    assert result["completed_actions"][0]["success"] is True


def test_high_value_refund_pauses_for_approval():
    result = _run("I want a refund for a high-value product. Order ORD1005.")
    assert result.get("__interrupt__")
    assert result["proposed_actions"][0]["action_type"] == "refund_review_request"
    assert result["tool_results"] == []


def test_unknown_order_is_blocked_without_approval():
    result = _run("Please return order ORD9999")
    assert result["status"] == "blocked"
    assert result.get("__interrupt__") is None
    assert result["tool_results"] == []


def test_missing_order_requests_clarification_without_account_action():
    result = _run("I don't remember my order ID.")
    assert "order_id" in result["triage"]["missing_information"]
    assert result["tool_results"] == []
    assert "share the order ID" in result["final_response"]


def test_retry_route_is_bounded(monkeypatch):
    import app.graph.nodes as nodes

    monkeypatch.setattr(nodes, "retrieve_policy_context", lambda *_: [])
    result = _run("Please return order ORD1010")
    assert result["retry_count"] == 2
    assert result.get("__interrupt__")


def test_block_route_precedes_human_review():
    assert after_validation({"validation_result": {"decision": "BLOCK"}, "investigation_result": {"requires_human_review": True}}) == "response"