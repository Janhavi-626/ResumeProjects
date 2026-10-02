import hashlib
import json
import logging
from uuid import uuid4

from sqlalchemy.exc import IntegrityError

from app.models.database import IdempotencyRecord, SessionLocal, SupportCase

logger = logging.getLogger("returns.actions")


def _execute_once(idempotency_key: str, action_type: str, operation) -> dict:
    if not idempotency_key:
        return {"success": False, "error": "idempotency_key is required"}
    with SessionLocal() as db:
        existing = db.query(IdempotencyRecord).filter_by(key=idempotency_key).first()
        if existing:
            return json.loads(existing.result)
        try:
            result = operation(db)
            db.add(IdempotencyRecord(key=idempotency_key, action_type=action_type, result=json.dumps(result)))
            db.commit()
            logger.info("business action recorded", extra={"tool": action_type, "status": "success"})
            return result
        except IntegrityError:
            db.rollback()
            existing = db.query(IdempotencyRecord).filter_by(key=idempotency_key).first()
            return json.loads(existing.result) if existing else {"success": False, "error": "duplicate action conflict"}
        except Exception as exc:
            db.rollback()
            logger.exception("business action failed", extra={"tool": action_type})
            return {"success": False, "error": f"Action could not be recorded: {type(exc).__name__}"}


def _case_action(action_type: str, workflow_id: str, customer_id: str, order_id: str | None, summary: str, idempotency_key: str) -> dict:
    def operation(db):
        case_id = f"CASE-{uuid4().hex[:10].upper()}"
        db.add(SupportCase(case_id=case_id, customer_id=customer_id, order_id=order_id, category=action_type, status="open", summary=summary[:500]))
        return {"success": True, "action_id": case_id, "action_type": action_type, "status": "recorded", "workflow_id": workflow_id}

    return _execute_once(idempotency_key, action_type, operation)


def create_support_ticket(workflow_id: str, customer_id: str, order_id: str | None, summary: str, idempotency_key: str) -> dict:
    return _case_action("support_ticket", workflow_id, customer_id, order_id, summary, idempotency_key)


def create_return_case(workflow_id: str, customer_id: str, order_id: str, summary: str, idempotency_key: str) -> dict:
    return _case_action("return_case", workflow_id, customer_id, order_id, summary, idempotency_key)


def request_refund(workflow_id: str, customer_id: str, order_id: str, amount: float, idempotency_key: str) -> dict:
    return _case_action("refund_review_request", workflow_id, customer_id, order_id, f"Refund review requested for {amount:.2f}; this does not issue funds.", idempotency_key)


def request_replacement(workflow_id: str, customer_id: str, order_id: str, product_id: str, idempotency_key: str) -> dict:
    return _case_action("replacement_review_request", workflow_id, customer_id, order_id, f"Replacement review requested for {product_id}; reservation not performed.", idempotency_key)


def update_case(workflow_id: str, customer_id: str, order_id: str | None, summary: str, idempotency_key: str) -> dict:
    return _case_action("case_update", workflow_id, customer_id, order_id, summary, idempotency_key)


def create_escalation(workflow_id: str, customer_id: str, order_id: str | None, summary: str, idempotency_key: str) -> dict:
    return _case_action("operations_escalation", workflow_id, customer_id, order_id, summary, idempotency_key)


def send_customer_notification(workflow_id: str, customer_id: str, order_id: str | None, summary: str, idempotency_key: str) -> dict:
    return _case_action("notification_draft", workflow_id, customer_id, order_id, f"Notification drafted, not delivered: {summary}", idempotency_key)


def make_idempotency_key(workflow_id: str, action_type: str, payload: dict) -> str:
    canonical = json.dumps(payload, sort_keys=True, default=str)
    digest = hashlib.sha256(canonical.encode()).hexdigest()[:16]
    return f"{workflow_id}:{action_type}:{digest}"