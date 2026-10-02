from app.rag.retriever import retrieve_policies


def retrieve_policy_context(query: str, category: str) -> list[dict]:
    return retrieve_policies(f"{query} {category} return refund shipment customer support", limit=5)