from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class WorkflowStatus(StrEnum):
    RUNNING = "running"
    HUMAN_REVIEW = "human_review_required"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"


class TriageResult(BaseModel):
    intent: str = "return_exception"
    category: str
    priority: str = "medium"
    entities: dict[str, str] = Field(default_factory=dict)
    missing_information: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    recommended_route: str = "investigate_return"


class PolicySource(BaseModel):
    document_id: str
    title: str
    source: str
    category: str
    page: int = 1
    section: str
    version: str
    effective_date: str
    excerpt: str
    citation: str


class InvestigationResult(BaseModel):
    issue_type: str
    evidence: list[str]
    policy_reference: list[str]
    recommended_action: str
    confidence: float = Field(ge=0, le=1)
    requires_human_review: bool
    summary: str


class ProposedAction(BaseModel):
    action_type: str
    description: str
    requires_approval: bool = True
    expected_impact: str
    parameters: dict[str, Any] = Field(default_factory=dict)


class ValidationResult(BaseModel):
    decision: str
    reasons: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)


class ChatRequest(BaseModel):
    message: str = Field(min_length=3, max_length=4000)
    session_id: str | None = None
    user_id: str = "demo-agent"


class ApprovalRequest(BaseModel):
    decision: str
    modified_action: ProposedAction | None = None
    reviewer: str = "operations-manager"
    comment: str = ""

    model_config = ConfigDict(extra="forbid")


class AgentResponse(BaseModel):
    workflow_id: str
    session_id: str
    status: WorkflowStatus
    intent: str
    classification: str
    confidence: float
    evidence: list[str]
    policy_sources: list[PolicySource]
    recommended_action: ProposedAction | None
    approval_required: bool
    completed_actions: list[dict[str, Any]]
    pending_actions: list[dict[str, Any]]
    final_response: str
    workflow_state: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
