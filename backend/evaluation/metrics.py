def calculate_metrics(rows: list[dict]) -> dict:
    count = max(len(rows), 1)
    classification = [row for row in rows if row.get("expected_classification")]
    escalation = [row for row in rows if row.get("expected_escalation") is not None]
    grounded = sum(bool(row.get("grounded")) for row in rows) / count
    return {
        "case_count": len(rows),
        "retrieval_relevance": sum(bool(row.get("retrieval_relevant")) for row in rows) / count,
        "citation_rate": sum(bool(row.get("citation_count")) for row in rows) / count,
        "citation_correctness": sum(bool(row.get("citations_valid")) for row in rows) / count,
        "human_escalation_accuracy": sum(row["expected_escalation"] == row.get("approval_required") for row in escalation) / max(len(escalation), 1),
        "classification_accuracy": sum(row["expected_classification"] == row.get("classification") for row in classification) / max(len(classification), 1),
        "policy_compliance": sum(bool(row.get("policy_compliant")) for row in rows) / count,
        "groundedness": grounded,
        "hallucination_rate": 1 - grounded,
        "response_usefulness": sum(bool(row.get("response_useful")) for row in rows) / count,
        "mean_latency_ms": sum(row.get("latency_ms", 0) for row in rows) / count,
        "tool_success_rate": sum(row.get("tool_success", True) for row in rows) / count,
    }