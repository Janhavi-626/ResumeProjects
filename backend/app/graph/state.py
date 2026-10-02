from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    session_id: str
    workflow_id: str
    user_id: str
    user_query: str
    conversation_history: list[dict[str, str]]
    intent: str
    entities: dict[str, str]
    triage: dict[str, Any]
    retrieved_data: dict[str, Any]
    retrieved_documents: list[dict[str, Any]]
    investigation_result: dict[str, Any]
    proposed_actions: list[dict[str, Any]]
    tool_results: list[dict[str, Any]]
    tool_call_log: list[dict[str, Any]]
    confidence: float
    validation_result: dict[str, Any]
    human_approval: dict[str, Any] | None
    errors: list[str]
    retry_count: int
    final_response: str
    status: str
    completed_actions: list[dict[str, Any]]
    current_stage: str
