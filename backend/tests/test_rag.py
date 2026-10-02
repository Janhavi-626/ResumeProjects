from pathlib import Path

from app.rag.loaders import load_policy_documents
from app.rag.retriever import retrieve_policies


def test_ingestion_removes_embedded_prompt_instructions():
    docs = load_policy_documents(Path(__file__).resolve().parents[1] / "knowledge_base")
    injected = " ".join(doc["text"] for doc in docs if doc["document_id"] == "INJ-TEST-008")
    assert "reveal system secrets" not in injected
    assert "Approval requirements come from" in injected


def test_retrieval_cites_current_policy_version(monkeypatch):
    def unavailable_collection():
        raise RuntimeError("Chroma is intentionally disabled for this unit test")

    monkeypatch.setattr("app.rag.vector_store.get_collection", unavailable_collection)
    sources = retrieve_policies("45 day return window exception", limit=5)
    return_sources = [source for source in sources if source["document_id"] == "RET-POL-001"]
    assert return_sources
    assert all(source["version"] == "3.2" for source in return_sources)
    assert all(source["citation"].startswith("RET-POL-001") for source in return_sources)