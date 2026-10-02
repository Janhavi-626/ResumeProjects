from functools import lru_cache

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from app.graph.edges import after_approval, after_post_action_validation, after_validation
from app.graph.nodes import (
    action_node,
    approval_node,
    investigation_node,
    policy_node,
    post_action_validation_node,
    response_node,
    retry_node,
    retrieval_node,
    triage_node,
    validation_node,
)
from app.graph.state import AgentState


@lru_cache
def get_workflow():
    graph = StateGraph(AgentState)
    graph.add_node("triage", triage_node)
    graph.add_node("data_retrieval", retrieval_node)
    graph.add_node("policy_retrieval", policy_node)
    graph.add_node("investigation", investigation_node)
    graph.add_node("validation", validation_node)
    graph.add_node("human_approval", approval_node)
    graph.add_node("action", action_node)
    graph.add_node("post_action_validation", post_action_validation_node)
    graph.add_node("response", response_node)
    graph.add_node("retry", retry_node)
    graph.add_edge(START, "triage")
    graph.add_edge("triage", "data_retrieval")
    graph.add_edge("data_retrieval", "policy_retrieval")
    graph.add_edge("policy_retrieval", "investigation")
    graph.add_edge("investigation", "validation")
    graph.add_conditional_edges("validation", after_validation, {"human_approval": "human_approval", "action": "action", "response": "response", "retry": "retry"})
    graph.add_edge("retry", "data_retrieval")
    graph.add_conditional_edges("human_approval", after_approval, {"action": "action", "response": "response"})
    graph.add_edge("action", "post_action_validation")
    graph.add_conditional_edges("post_action_validation", after_post_action_validation, {"response": "response"})
    graph.add_edge("response", END)
    return graph.compile(checkpointer=MemorySaver())
