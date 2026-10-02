import json
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

from app.config.settings import get_settings


class Base(DeclarativeBase):
    pass


class JsonText:
    @staticmethod
    def encode(value: Any) -> str:
        return json.dumps(value, default=str)

    @staticmethod
    def decode(value: str | None) -> Any:
        return json.loads(value) if value else None


class User(Base):
    __tablename__ = "users"
    user_id: Mapped[str] = mapped_column(String, primary_key=True)
    display_name: Mapped[str] = mapped_column(String)
    role: Mapped[str] = mapped_column(String, default="support_agent")
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Customer(Base):
    __tablename__ = "customers"
    customer_id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    email: Mapped[str] = mapped_column(String)
    tier: Mapped[str] = mapped_column(String, default="standard")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    return_count: Mapped[int] = mapped_column(Integer, default=0)
    risk_flag: Mapped[bool] = mapped_column(Boolean, default=False)


class Order(Base):
    __tablename__ = "orders"
    order_id: Mapped[str] = mapped_column(String, primary_key=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.customer_id"))
    status: Mapped[str] = mapped_column(String, default="delivered")
    order_date: Mapped[datetime] = mapped_column(DateTime)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    total: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String, default="USD")


class OrderItem(Base):
    __tablename__ = "order_items"
    item_id: Mapped[str] = mapped_column(String, primary_key=True)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.order_id"))
    product_id: Mapped[str] = mapped_column(String)
    product_name: Mapped[str] = mapped_column(String)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    unit_price: Mapped[float] = mapped_column(Float)


class ReturnRequest(Base):
    __tablename__ = "returns"
    return_id: Mapped[str] = mapped_column(String, primary_key=True)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.order_id"))
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.customer_id"))
    reason: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="requested")
    requested_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    issue_type: Mapped[str] = mapped_column(String, default="standard")


class ReturnItem(Base):
    __tablename__ = "return_items"
    item_id: Mapped[str] = mapped_column(String, primary_key=True)
    return_id: Mapped[str] = mapped_column(ForeignKey("returns.return_id"))
    product_id: Mapped[str] = mapped_column(String)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    condition: Mapped[str] = mapped_column(String, default="unknown")


class Payment(Base):
    __tablename__ = "payments"
    payment_id: Mapped[str] = mapped_column(String, primary_key=True)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.order_id"))
    status: Mapped[str] = mapped_column(String)
    amount: Mapped[float] = mapped_column(Float)
    refund_status: Mapped[str] = mapped_column(String, default="none")
    refunded_amount: Mapped[float] = mapped_column(Float, default=0)


class Shipment(Base):
    __tablename__ = "shipments"
    shipment_id: Mapped[str] = mapped_column(String, primary_key=True)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.order_id"))
    carrier: Mapped[str] = mapped_column(String)
    tracking_number: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Inventory(Base):
    __tablename__ = "inventory"
    product_id: Mapped[str] = mapped_column(String, primary_key=True)
    warehouse_id: Mapped[str] = mapped_column(String)
    on_hand: Mapped[int] = mapped_column(Integer)
    disposition: Mapped[str] = mapped_column(String, default="sellable")


class SupportCase(Base):
    __tablename__ = "support_cases"
    case_id: Mapped[str] = mapped_column(String, primary_key=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.customer_id"))
    order_id: Mapped[str | None] = mapped_column(String, nullable=True)
    category: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="open")
    summary: Mapped[str] = mapped_column(Text)


class Workflow(Base):
    __tablename__ = "workflows"
    workflow_id: Mapped[str] = mapped_column(String, primary_key=True)
    session_id: Mapped[str] = mapped_column(String, index=True)
    user_id: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, index=True)
    state_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SessionRecord(Base):
    __tablename__ = "sessions"
    session_id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Message(Base):
    __tablename__ = "messages"
    message_id: Mapped[str] = mapped_column(String, primary_key=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.session_id"))
    role: Mapped[str] = mapped_column(String)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AgentRun(Base):
    __tablename__ = "agent_runs"
    run_id: Mapped[str] = mapped_column(String, primary_key=True)
    workflow_id: Mapped[str] = mapped_column(String, index=True)
    agent: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)
    latency_ms: Mapped[float] = mapped_column(Float, default=0)
    details: Mapped[str] = mapped_column(Text, default="{}")


class ToolCall(Base):
    __tablename__ = "tool_calls"
    call_id: Mapped[str] = mapped_column(String, primary_key=True)
    workflow_id: Mapped[str] = mapped_column(String, index=True)
    tool_name: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)
    result: Mapped[str] = mapped_column(Text, default="{}")


class Approval(Base):
    __tablename__ = "approvals"
    approval_id: Mapped[str] = mapped_column(String, primary_key=True)
    workflow_id: Mapped[str] = mapped_column(ForeignKey("workflows.workflow_id"))
    decision: Mapped[str] = mapped_column(String)
    reviewer: Mapped[str] = mapped_column(String)
    comment: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    audit_id: Mapped[str] = mapped_column(String, primary_key=True)
    workflow_id: Mapped[str] = mapped_column(String, index=True)
    event: Mapped[str] = mapped_column(String)
    details: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Evaluation(Base):
    __tablename__ = "evaluations"
    evaluation_id: Mapped[str] = mapped_column(String, primary_key=True)
    workflow_id: Mapped[str] = mapped_column(String, index=True)
    metric: Mapped[str] = mapped_column(String)
    score: Mapped[float] = mapped_column(Float)


class DocumentRecord(Base):
    __tablename__ = "documents"
    document_id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String)
    source: Mapped[str] = mapped_column(String)
    category: Mapped[str] = mapped_column(String)
    version: Mapped[str] = mapped_column(String)


class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    chunk_id: Mapped[str] = mapped_column(String, primary_key=True)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.document_id"))
    section: Mapped[str] = mapped_column(String)
    page: Mapped[int] = mapped_column(Integer, default=1)
    content: Mapped[str] = mapped_column(Text)


class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"
    __table_args__ = (UniqueConstraint("key", name="uq_idempotency_key"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String, nullable=False)
    action_type: Mapped[str] = mapped_column(String)
    result: Mapped[str] = mapped_column(Text)


def _make_engine():
    url = get_settings().database_url
    if url.startswith("sqlite"):
        database_path = url.removeprefix("sqlite:///")
        if database_path and database_path != ":memory:":
            path = Path(database_path)
            if not path.is_absolute():
                path = Path(__file__).resolve().parents[2] / path
            path.parent.mkdir(parents=True, exist_ok=True)
            url = f"sqlite:///{path}"
        return create_engine(url, connect_args={"check_same_thread": False})
    return create_engine(url, pool_pre_ping=True)


engine = _make_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
