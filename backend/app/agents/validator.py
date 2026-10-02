from app.config.settings import get_settings
from app.models.schemas import ValidationResult


def validate_state(state: dict, after_action: bool = False) -> ValidationResult:
    findings = state.get("investigation_result") or {}
    if state.get("triage", {}).get("missing_information"):
        return ValidationResult(decision="PASS", confidence=0.9, reasons=["Clarification response; no account action will be executed."])
    if not (state.get("retrieved_data") or {}).get("order"):
        return ValidationResult(decision="BLOCK", confidence=0.2, reasons=["No matching order was found; no business action is authorized."])
    if not findings.get("evidence"):
        return ValidationResult(decision="HUMAN_REVIEW", confidence=0.3, reasons=["No operational evidence is available."])
    if not findings.get("policy_reference"):
        if state.get("retry_count", 0) < get_settings().max_workflow_retries:
            return ValidationResult(decision="RETRY", confidence=0.45, reasons=["Policy retrieval returned no citations; retrying within the configured limit."])
        return ValidationResult(decision="HUMAN_REVIEW", confidence=0.45, reasons=["No policy citation was retrieved."])
    if findings.get("confidence", 0) < get_settings().confidence_threshold:
        return ValidationResult(decision="HUMAN_REVIEW", confidence=findings.get("confidence", 0), reasons=["Confidence is below the configured threshold."])
    if after_action and any(not result.get("success") for result in state.get("tool_results", [])):
        return ValidationResult(decision="BLOCK", confidence=0.2, reasons=["An action tool did not confirm success."])
    if findings.get("requires_human_review") and state.get("human_approval") is None:
        return ValidationResult(decision="HUMAN_REVIEW", confidence=findings["confidence"], reasons=["Policy or risk criteria require an authorized reviewer."])
    return ValidationResult(decision="PASS", confidence=findings.get("confidence", 0.7), reasons=["Evidence, citations, and action constraints passed."])