"""Typed boundary for future OMS, carrier, payment, and inventory adapters."""

from pydantic import BaseModel, Field


class ExternalLookupRequest(BaseModel):
    order_id: str = Field(min_length=4, max_length=32)


class ExternalLookupResponse(BaseModel):
    success: bool
    source: str
    result: dict | None = None
    error: str | None = None


def tracking_lookup(order_id: str) -> ExternalLookupResponse:
    from app.tools.database_tools import get_tracking

    request = ExternalLookupRequest(order_id=order_id)
    result = get_tracking(request.order_id)
    return ExternalLookupResponse(success=result["success"], source="synthetic_shipment_system", result=result["data"], error=result["error"])
