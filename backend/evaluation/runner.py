import time
from pathlib import Path
from uuid import uuid4

from app.graph import nodes
from app.models.database import init_db
from app.models.database import Evaluation, SessionLocal
from evaluation.dataset.cases import CASES
from evaluation.metrics import calculate_metrics
from evaluation.report import write_report
from scripts.seed_database import seed_database
from app.services.workflow_service import run_workflow


def _expected_classification(case: dict) -> str | None:
    by_group = {
        "normal": "standard_return",
        "ambiguous": "return_inquiry",
        "missing_information": "standard_return",
        "tool_failure": "standard_return",
        "prompt_injection": "return_inquiry",
        "policy_conflict": "late_return",
    }
    if case["group"] != "human_approval":
        return by_group.get(case["group"])
    if "ORD1001" in case["query"]:
        return "damaged_item"
    if "ORD1002" in case["query"]:
        return "late_return"
    if "ORD1005" in case["query"]:
        return "high_value"
    if "ORD1009" in case["query"]:
        return "fraud_risk"
    return "refund_pending"


def main() -> None:
    init_db()
    seed_database()
    original_retrieval = nodes.retrieve_case_data
    rows = []
    try:
        for index, case in enumerate(CASES):
            if case["fault"] == "database_lookup":
                nodes.retrieve_case_data = lambda _entities: {"order": None, "errors": ["Simulated database lookup timeout."]}
            started = time.perf_counter()
            try:
                result = run_workflow(case["query"], "evaluation-runner")
                rows.append({
                    **{key: case[key] for key in ("case_id", "group")},
                    "status": result.status,
                    "classification": result.classification,
                    "approval_required": result.approval_required,
                    "expected_escalation": case["expected"] == "human_review" if case["group"] in {"policy_conflict", "human_approval"} else None,
                    "expected_classification": _expected_classification(case),
                    "citation_count": len(result.policy_sources),
                    "citations_valid": bool(result.policy_sources) and all(source.document_id and source.section and source.citation.startswith(source.document_id) for source in result.policy_sources),
                    "retrieval_relevant": bool(result.policy_sources),
                    "grounded": all(action.get("success", False) for action in result.completed_actions) and bool(result.evidence or case["group"] == "missing_information"),
                    "policy_compliant": not (result.approval_required and result.completed_actions),
                    "response_useful": bool(result.final_response) and "Known Facts" in result.final_response,
                    "tool_success": case["group"] != "tool_failure" and (all(action.get("success", False) for action in result.completed_actions) if result.completed_actions else True),
                    "latency_ms": (time.perf_counter() - started) * 1000,
                })
            except Exception as exc:
                rows.append({"case_id": case["case_id"], "group": case["group"], "status": "error", "citation_count": 0, "latency_ms": (time.perf_counter() - started) * 1000, "error": type(exc).__name__})
            finally:
                nodes.retrieve_case_data = original_retrieval
    finally:
        nodes.retrieve_case_data = original_retrieval
    metrics = calculate_metrics(rows)
    with SessionLocal() as db:
        for metric, score in metrics.items():
            if isinstance(score, (int, float)):
                db.add(Evaluation(evaluation_id=str(uuid4()), workflow_id="EVALUATION-LATEST", metric=metric, score=float(score)))
        db.commit()
    destination = Path(__file__).resolve().parent / "report.md"
    write_report(metrics, rows, destination)
    print(f"Evaluated {metrics['case_count']} cases. Citation rate={metrics['citation_rate']:.2f}; human escalation accuracy={metrics['human_escalation_accuracy']:.2f}. Report: {destination}")


if __name__ == "__main__":
    main()