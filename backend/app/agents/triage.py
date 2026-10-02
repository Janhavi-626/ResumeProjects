import re

from app.models.schemas import TriageResult
from app.prompts.triage_prompt import TRIAGE_PROMPT
from app.services.llm_service import get_chat_model

_CATEGORIES = {
    "damaged_item": ("damaged", "broken", "cracked"),
    "late_return": ("late", "days ago", "outside the return window", "after the return window"),
    "wrong_item": ("wrong product", "wrong item", "received the wrong"),
    "missing_item": ("missing item", "item missing", "missing from"),
    "lost_shipment": ("lost", "not delivered", "never arrived"),
    "refund_pending": ("refund", "money back", "has not arrived"),
    "duplicate_request": ("duplicate", "already requested"),
    "fraud_risk": ("fraud", "unusual activity", "risk"),
}


def triage_request(query: str) -> TriageResult:
    lowered = query.lower()
    category = next((name for name, terms in _CATEGORIES.items() if any(term in lowered for term in terms)), "standard_return")
    entities = {}
    for key, pattern in (("order_id", r"\bORD\d{4,}\b"), ("customer_id", r"\bCUS\d{4,}\b"), ("product_id", r"\bPROD\d{4,}\b")):
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            entities[key] = match.group(0).upper()
    missing = [] if "order_id" in entities else ["order_id"]
    if "order_id" in entities and not any(word in lowered for word in ("return", "refund", "damaged", "wrong", "missing", "lost")):
        category = "return_inquiry"
    priority = "high" if category in {"fraud_risk", "lost_shipment", "late_return"} else "medium"
    deterministic = TriageResult(
        category=category,
        priority=priority,
        entities=entities,
        missing_information=missing,
        confidence=0.94 if not missing else 0.42,
        recommended_route="clarify" if missing else "investigate_return",
    )
    model = get_chat_model()
    if model is None:
        return deterministic
    try:
        candidate = model.with_structured_output(TriageResult).invoke([("system", TRIAGE_PROMPT), ("human", query)])
        allowed = {"damaged_item", "late_return", "wrong_item", "missing_item", "lost_shipment", "refund_pending", "duplicate_request", "fraud_risk", "standard_return", "return_inquiry"}
        return TriageResult(
            intent="return_exception",
            category=candidate.category if candidate.category in allowed else deterministic.category,
            priority=candidate.priority if candidate.priority in {"low", "medium", "high"} else deterministic.priority,
            entities=deterministic.entities,
            missing_information=deterministic.missing_information,
            confidence=min(candidate.confidence, deterministic.confidence),
            recommended_route=deterministic.recommended_route,
        )
    except Exception:
        return deterministic


__all__ = ["triage_request", "TRIAGE_PROMPT"]