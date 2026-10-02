from app.models.database import SessionLocal, SupportCase
from app.tools.business_tools import create_support_ticket
from app.tools.database_tools import get_order


def test_operational_order_tool_returns_authoritative_seed_data():
    result = get_order("ORD1001")
    assert result["success"] is True
    assert result["data"]["customer_id"] == "CUS1001"
    assert result["data"]["total"] == 120.0


def test_business_action_is_idempotent():
    result_a = create_support_ticket("WF-TEST", "CUS1001", "ORD1001", "Review case", "idempotency-test-key")
    result_b = create_support_ticket("WF-TEST", "CUS1001", "ORD1001", "Review case", "idempotency-test-key")
    assert result_a == result_b
    with SessionLocal() as db:
        assert db.query(SupportCase).filter_by(case_id=result_a["action_id"]).count() == 1