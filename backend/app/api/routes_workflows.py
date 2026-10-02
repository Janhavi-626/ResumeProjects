from fastapi import APIRouter, HTTPException

from app.models.database import Message, SessionLocal, Workflow
from app.services.workflow_service import get_workflow_record

router = APIRouter()


@router.get("/workflows/{workflow_id}")
async def workflow_details(workflow_id: str):
    result = get_workflow_record(workflow_id)
    if not result:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return result


@router.get("/sessions/{session_id}")
async def session_details(session_id: str):
    with SessionLocal() as db:
        workflows = db.query(Workflow).filter_by(session_id=session_id).order_by(Workflow.created_at.desc()).all()
        messages = db.query(Message).filter_by(session_id=session_id).order_by(Message.created_at.asc()).all()
        if not workflows and not messages:
            raise HTTPException(status_code=404, detail="Session not found")
        return {
            "session_id": session_id,
            "messages": [{"role": row.role, "content": row.content, "created_at": row.created_at.isoformat()} for row in messages],
            "workflows": [{"workflow_id": row.workflow_id, "status": row.status, "created_at": row.created_at.isoformat(), "updated_at": row.updated_at.isoformat()} for row in workflows],
        }