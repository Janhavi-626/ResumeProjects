from fastapi import APIRouter

from app.api.routes_chat import chat
from app.models.schemas import ChatRequest

router = APIRouter()


@router.post("/agent/run")
async def run_agent(request: ChatRequest):
    return await chat(request)