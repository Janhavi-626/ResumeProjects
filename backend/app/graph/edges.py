from app.config.settings import get_settings


def after_validation(state: dict) -> str:
    if state.get("triage", {}).get("missing_information"):
        return "response"
    decision = state.get("validation_result", {}).get("decision")
    if decision == "BLOCK":
        return "response"
    if decision == "HUMAN_REVIEW" or (state.get("investigation_result", {}).get("requires_human_review") and state.get("human_approval") is None):
        return "human_approval"
    if decision == "RETRY" and state.get("retry_count", 0) < get_settings().max_workflow_retries:
        return "retry"
    if decision in {"BLOCK", "RETRY"}:
        return "response"
    return "action"


def after_approval(state: dict) -> str:
    if state.get("human_approval", {}).get("decision") in {"approve", "modify"}:
        return "action"
    return "response"


def after_post_action_validation(state: dict) -> str:
    return "response"
