from app.prompts.response_prompt import RESPONSE_PROMPT


def compose_response(state: dict) -> str:
    triage = state.get("triage", {})
    findings = state.get("investigation_result", {})
    data = state.get("retrieved_data", {})
    order = data.get("order") or {}
    sources = state.get("retrieved_documents", [])
    actions = state.get("tool_results", [])
    lines = ["Known Facts"]
    if order:
        lines.append(f"- Order {order['order_id']} is {order['status']} with a total of {order['currency']} {order['total']:.2f}.")
    elif triage.get("missing_information"):
        lines.append("- I could not identify an order from the information provided.")
    else:
        lines.append("- No matching order record was found.")
    lines.append("\nEvidence")
    lines.extend(f"- {item}" for item in findings.get("evidence", []) or ["- No verified case evidence is available."])
    lines.append("\nApplicable Policy")
    lines.extend(f"- {source.get('citation')} (v{source.get('version')}, effective {source.get('effective_date')}): {source.get('text', '')[:220]}" for source in sources[:3])
    if not sources:
        lines.append("- No applicable policy source was retrieved.")
    lines.extend(["\nRecommended Resolution", f"- {findings.get('recommended_action', 'request_order_id').replace('_', ' ')}."])
    lines.append("\nCompleted Actions")
    successful = [action for action in actions if action.get("success")]
    if successful:
        lines.extend(f"- {action.get('action_type', 'Action')} recorded with reference {action.get('action_id')}." for action in successful)
    else:
        lines.append("- No business action has been completed.")
    lines.append("\nPending Approval")
    if state.get("status") == "human_review_required":
        lines.append("- An authorized reviewer must approve or reject the proposed action before it can be recorded.")
    elif (state.get("human_approval") or {}).get("decision") == "reject":
        lines.append("- The proposed action was rejected; no action was executed.")
    else:
        lines.append("- No approval is pending.")
    lines.append("\nSources")
    lines.extend(f"- {source.get('citation')}" for source in sources[:5])
    if triage.get("missing_information"):
        lines.extend(["\nNext Step", "- Please share the order ID (for example, ORD1001) so I can check the relevant records."])
    return "\n".join(lines)


__all__ = ["compose_response", "RESPONSE_PROMPT"]