from pathlib import Path

from app.config.settings import get_settings
from app.rag.chunking import chunk_documents
from app.rag.embeddings import get_embeddings
from app.rag.loaders import load_policy_documents
from app.rag.reranker import rerank

_CACHE: list[dict] | None = None


def _local_chunks() -> list[dict]:
    global _CACHE
    if _CACHE is None:
        root = Path(__file__).resolve().parents[2] / "knowledge_base"
        _CACHE = chunk_documents(load_policy_documents(root))
    return _CACHE


def _version_key(value: str) -> tuple[int, ...]:
    try:
        return tuple(int(part) for part in value.split(".") if part.isdigit())
    except ValueError:
        return (0,)


def _current_versions() -> dict[str, str]:
    versions: dict[str, str] = {}
    for chunk in _local_chunks():
        document_id = chunk["document_id"]
        if document_id not in versions or _version_key(chunk["version"]) > _version_key(versions[document_id]):
            versions[document_id] = chunk["version"]
    return versions


def retrieve_policies(query: str, limit: int = 5) -> list[dict]:
    if not query.strip():
        return []
    try:
        from app.rag.vector_store import get_collection

        collection = get_collection()
        if collection.count() > 0:
            vector = get_embeddings().embed_query(query)
            matches = collection.query(query_embeddings=[vector], n_results=min(max(limit * 5, 20), collection.count()), include=["documents", "metadatas", "distances"])
            results = []
            for index, text in enumerate(matches["documents"][0]):
                metadata = matches["metadatas"][0][index]
                if metadata.get("version") != _current_versions().get(metadata.get("document_id")):
                    continue
                results.append({**metadata, "text": text, "score": 1 - matches["distances"][0][index], "citation": f"{metadata['document_id']} {metadata['section']}"})
            return rerank(query, results)[:limit]
    except Exception:
        pass

    terms = set(query.lower().split())
    results = []
    for chunk in _local_chunks():
        text = chunk["text"].lower()
        title = chunk["title"].lower()
        score = sum(1 for term in terms if term in text or term in title) / max(len(terms), 1)
        if score > 0:
            results.append({**chunk, "score": score, "citation": f"{chunk['document_id']} {chunk['section']}"})
    current = _current_versions()
    results = [result for result in results if result.get("version") == current.get(result.get("document_id"))]
    return rerank(query, results)[:limit]
