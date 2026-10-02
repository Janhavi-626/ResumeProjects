from pathlib import Path

from app.config.settings import get_settings
from app.rag.embeddings import get_embeddings

COLLECTION_NAME = "return_policy_chunks"


def get_collection():
    import chromadb

    settings = get_settings()
    client = (
        chromadb.HttpClient(host=settings.chroma_host, port=settings.chroma_port)
        if settings.chroma_host
        else chromadb.PersistentClient(path=str(Path(settings.chroma_persist_directory) if Path(settings.chroma_persist_directory).is_absolute() else Path(__file__).resolve().parents[2] / settings.chroma_persist_directory))
    )
    return client.get_or_create_collection(COLLECTION_NAME, metadata={"hnsw:space": "cosine"})


def upsert_chunks(chunks: list[dict]) -> int:
    if not chunks:
        return 0
    collection = get_collection()
    embeddings = get_embeddings().embed_documents([chunk["text"] for chunk in chunks])
    metadata_keys = ("document_id", "title", "source", "category", "page", "section", "version", "effective_date", "chunk_index")
    collection.upsert(
        ids=[chunk["chunk_id"] for chunk in chunks],
        documents=[chunk["text"] for chunk in chunks],
        embeddings=embeddings,
        metadatas=[{key: chunk[key] for key in metadata_keys} for chunk in chunks],
    )
    return len(chunks)