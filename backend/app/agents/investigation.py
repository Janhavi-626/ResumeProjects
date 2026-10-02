from datetime import datetime

from app.models.schemas import InvestigationResult


def investigate_case(query: str, category: str, data: dict, documents: list[dict], missing_information: list[str]) -> InvestigationResult:
    order = data.get("order") or {}
    customer = data.get("customer") or {}
    payment = data.get("payment") or {}
    tracking = data.get("tracking") or {}
    returned = data.get("return") or {}
    evidence = []
    if order:
        evidence.append(f"Order {order['order_id']} is recorded with status {order['status']} and total {order['currency']} {order['total']:.2f}.")
    if tracking:
        evidence.append(f"Carrier tracking status is {tracking['status']}.")
        if tracking.get("delivered_at"):
            delivered = datetime.fromisoformat(tracking["delivered_at"])
            days = max((datetime.utcnow() - delivered.replace(tzinfo=None)).days, 0)
            evidence.append(f"Verified delivery scan was {days} days ago.")
            if days > 30 and category not in {"refund_pending", "wrong_item", "missing_item"}:
                category = "late_return"
    if returned:
        evidence.append(f"Return record {returned['return_id']} is {returned['status']} and is classified as {returned['issue_type']}.")
        if returned["issue_type"] != "standard":
            category = returned["issue_type"]
    if order and order.get("total", 0) >= 300 and category == "standard_return":
        category = "high_value"
    if payment:
        evidence.append(f"Payment status is {payment['status']}; refund status is {payment['refund_status']}.")
    if customer:
        evidence.append(f"Customer tier is {customer['tier']} with {customer['return_count']} recorded returns.")
        if customer.get("risk_flag"):
            category = "fraud_risk"
            evidence.append("A restricted operations review flag is present; this is not a fraud finding.")
    if data.get("inventory"):
        inventory = data["inventory"]
        evidence.append(f"Inventory reports {inventory['on_hand']} on hand with disposition {inventory['disposition']}.")
    if data.get("errors"):
        evidence.extend(f"Evidence source unavailable: {error}" for error in data["errors"])
    citations = [document.get("citation", f"{document['document_id']} {document['section']}") for document in documents]
    requires_approval = (
        category in {"late_return", "damaged_item", "fraud_risk", "high_value", "duplicate_request"}
        or (order and order.get("total", 0) >= 300)
        or "refund" in query.lower()
        or bool(missing_information)
    )
    if category == "refund_pending":
        recommendation = "investigate_refund_status"
    elif category in {"damaged_item", "wrong_item", "missing_item"}:
        recommendation = "return_case_and_inspection"
    elif category == "late_return":
        recommendation = "request_refund" if "refund" in query.lower() else "human_review"
    elif category == "high_value" and "refund" in query.lower():
        recommendation = "request_refund"
    elif category == "lost_shipment":
        recommendation = "shipment_investigation"
    elif category == "fraud_risk":
        recommendation = "specialist_review"
    elif missing_information:
        recommendation = "request_order_id"
    else:
        recommendation = "create_return_case"
    confidence = 0.42 if missing_information or not order else (0.91 if evidence and documents else 0.76)
    summary = f"{category.replace('_', ' ').capitalize()} assessment based on {len(evidence)} operational evidence item(s) and {len(citations)} policy citation(s)."
    return InvestigationResult(
        issue_type=category,
        evidence=evidence,
        policy_reference=citations,
        recommended_action=recommendation,
        confidence=confidence,
        requires_human_review=requires_approval or confidence < 0.7,
        summary=summary,
    )