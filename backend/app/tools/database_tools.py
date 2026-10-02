import logging
import time
from typing import Any

from pydantic import BaseModel

from app.models.database import (
    Customer,
    Inventory,
    Order,
    OrderItem,
    Payment,
    ReturnItem,
    ReturnRequest,
    SessionLocal,
    Shipment,
    SupportCase,
)

logger = logging.getLogger("returns.tools")


class IdentifierInput(BaseModel):
    identifier: str


class ToolOutput(BaseModel):
    success: bool
    data: Any = None
    error: str | None = None


def _run_tool(name: str, operation):
    started = time.perf_counter()
    try:
        result = operation()
        logger.info("tool completed", extra={"tool": name, "status": "success", "latency_ms": round((time.perf_counter() - started) * 1000, 2)})
        return ToolOutput(success=True, data=result).model_dump()
    except Exception as exc:
        logger.exception("tool failed", extra={"tool": name, "status": "error"})
        return ToolOutput(success=False, error=f"{name} unavailable: {type(exc).__name__}").model_dump()


def get_customer(customer_id: str) -> dict:
    IdentifierInput(identifier=customer_id)

    def operation():
        with SessionLocal() as db:
            row = db.get(Customer, customer_id)
            return None if row is None else {
                "customer_id": row.customer_id,
                "name": row.name,
                "tier": row.tier,
                "return_count": row.return_count,
                "risk_flag": row.risk_flag,
            }

    return _run_tool("get_customer", operation)


def get_order(order_id: str) -> dict:
    IdentifierInput(identifier=order_id)

    def operation():
        with SessionLocal() as db:
            row = db.get(Order, order_id)
            if row is None:
                return None
            items = db.query(OrderItem).filter_by(order_id=order_id).all()
            return {
                "order_id": row.order_id,
                "customer_id": row.customer_id,
                "status": row.status,
                "order_date": row.order_date.isoformat(),
                "delivered_at": row.delivered_at.isoformat() if row.delivered_at else None,
                "total": row.total,
                "currency": row.currency,
                "items": [{"product_id": item.product_id, "product_name": item.product_name, "quantity": item.quantity, "unit_price": item.unit_price} for item in items],
            }

    return _run_tool("get_order", operation)


def get_return_request(return_id: str) -> dict:
    IdentifierInput(identifier=return_id)

    def operation():
        with SessionLocal() as db:
            row = db.get(ReturnRequest, return_id)
            if row is None:
                return None
            items = db.query(ReturnItem).filter_by(return_id=return_id).all()
            return {
                "return_id": row.return_id,
                "order_id": row.order_id,
                "customer_id": row.customer_id,
                "reason": row.reason,
                "status": row.status,
                "issue_type": row.issue_type,
                "requested_at": row.requested_at.isoformat(),
                "items": [{"product_id": item.product_id, "quantity": item.quantity, "condition": item.condition} for item in items],
            }

    return _run_tool("get_return_request", operation)


def get_tracking(order_id: str) -> dict:
    IdentifierInput(identifier=order_id)

    def operation():
        with SessionLocal() as db:
            row = db.query(Shipment).filter_by(order_id=order_id).first()
            return None if row is None else {
                "shipment_id": row.shipment_id,
                "carrier": row.carrier,
                "tracking_number": row.tracking_number,
                "status": row.status,
                "delivered_at": row.delivered_at.isoformat() if row.delivered_at else None,
            }

    return _run_tool("get_tracking", operation)


def get_payment(order_id: str) -> dict:
    IdentifierInput(identifier=order_id)

    def operation():
        with SessionLocal() as db:
            row = db.query(Payment).filter_by(order_id=order_id).first()
            return None if row is None else {
                "payment_id": row.payment_id,
                "status": row.status,
                "amount": row.amount,
                "refund_status": row.refund_status,
                "refunded_amount": row.refunded_amount,
            }

    return _run_tool("get_payment", operation)


def get_inventory(product_id: str) -> dict:
    IdentifierInput(identifier=product_id)

    def operation():
        with SessionLocal() as db:
            row = db.get(Inventory, product_id)
            return None if row is None else {
                "product_id": row.product_id,
                "warehouse_id": row.warehouse_id,
                "on_hand": row.on_hand,
                "disposition": row.disposition,
            }

    return _run_tool("get_inventory", operation)


def get_customer_return_history(customer_id: str) -> dict:
    IdentifierInput(identifier=customer_id)

    def operation():
        with SessionLocal() as db:
            rows = db.query(ReturnRequest).filter_by(customer_id=customer_id).all()
            return [{"return_id": row.return_id, "order_id": row.order_id, "issue_type": row.issue_type, "status": row.status} for row in rows]

    return _run_tool("get_customer_return_history", operation)


def get_previous_support_cases(customer_id: str) -> dict:
    IdentifierInput(identifier=customer_id)

    def operation():
        with SessionLocal() as db:
            rows = db.query(SupportCase).filter_by(customer_id=customer_id).limit(20).all()
            return [{"case_id": row.case_id, "order_id": row.order_id, "category": row.category, "status": row.status, "summary": row.summary} for row in rows]

    return _run_tool("get_previous_support_cases", operation)