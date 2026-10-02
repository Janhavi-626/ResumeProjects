from fastapi import APIRouter, HTTPException
from starlette.concurrency import run_in_threadpool

from app.models.schemas import ApprovalRequest
from app.services.workflow_service import approve_workflow

router = APIRouter()


@router.post("/approval/{workflow_id}")
async def decide_approval(workflow_id: str, request: ApprovalRequest):
    try:
        response = await run_in_threadpool(approve_workflow, workflow_id, request.decision, request.reviewer, request.comment, request.modified_action.model_dump() if request.modified_action else None)
        return response.model_dump(mode="json")
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc