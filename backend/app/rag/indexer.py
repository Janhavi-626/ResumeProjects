from app.models.database import DocumentChunk, DocumentRecord, SessionLocal
from app.rag.chunking import chunk_documents
from app.rag.vector_store import upsert_chunks


def index_documents(documents: list[dict]) -> dict:
    chunks = chunk_documents(documents)
    vector_count = upsert_chunks(chunks)
    with SessionLocal() as db:
        document_records = {}
        for chunk in chunks:
            record = document_records.get(chunk["document_id"])
            if record is None:
                record = db.get(DocumentRecord, chunk["document_id"])
            if record is None:
                record = DocumentRecord(document_id=chunk["document_id"], title=chunk["title"], source=chunk["source"], category=chunk["category"], version=chunk["version"])
                db.add(record)
            else:
                record.title = chunk["title"]
                record.source = chunk["source"]
                record.category = chunk["category"]
                record.version = chunk["version"]
            document_records[chunk["document_id"]] = record
            chunk_record = db.get(DocumentChunk, chunk["chunk_id"])
            if chunk_record is None:
                db.add(DocumentChunk(chunk_id=chunk["chunk_id"], document_id=chunk["document_id"], section=chunk["section"], page=chunk["page"], content=chunk["text"]))
            else:
                chunk_record.content = chunk["text"]
                chunk_record.section = chunk["section"]
                chunk_record.page = chunk["page"]
        db.commit()
    return {"document_count": len({chunk["document_id"] for chunk in chunks}), "chunk_count": len(chunks), "vector_count": vector_count}