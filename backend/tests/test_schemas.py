import pytest
from pydantic import ValidationError

from app.models.schemas import ApprovalRequest, TriageResult


def test_triage_schema_bounds_confidence():
    result = TriageResult(category="damaged_item", confidence=0.9)
    assert result.intent == "return_exception"
    with pytest.raises(ValidationError):
        TriageResult(category="damaged_item", confidence=1.1)


def test_approval_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        ApprovalRequest(decision="approve", secret="not-allowed")