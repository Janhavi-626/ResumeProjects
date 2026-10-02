from fastapi import APIRouter
from starlette.concurrency import run_in_threadpool

from app.models.schemas import ChatRequest
from app.services.workflow_service import run_workflow

router = APIRouter()


@router.post("/chat")
async def chat(request: ChatRequest):
    response = await run_in_threadpool(run_workflow, request.message, request.user_id, request.session_id)
    return response.model_dump(mode="json")