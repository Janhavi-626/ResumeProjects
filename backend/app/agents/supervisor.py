"""Supervisor-facing workflow helpers; routing is implemented in LangGraph edges."""

from app.prompts.supervisor_prompt import SUPERVISOR_PROMPT


def next_stage(state: dict) -> str:
    if state.get("status") in {"blocked", "failed", "human_review_required"}:
        return state["status"]
    return state.get("current_stage", "triage")


__all__ = ["next_stage", "SUPERVISOR_PROMPT"]