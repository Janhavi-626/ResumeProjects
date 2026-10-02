from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile
from starlette.concurrency import run_in_threadpool

from app.config.settings import get_settings
from app.rag.indexer import index_documents
from app.rag.loaders import load_policy_documents

router = APIRouter()
ALLOWED_SUFFIXES = {".md", ".txt"}


@router.post("/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(status_code=415, detail="Only Markdown and plain-text policy files are accepted.")
    content = await file.read(get_settings().max_upload_bytes + 1)
    if len(content) > get_settings().max_upload_bytes:
        raise HTTPException(status_code=413, detail="Document exceeds the configured upload limit.")
    if b"\x00" in content:
        raise HTTPException(status_code=400, detail="Binary content is not accepted.")
    upload_dir = Path(__file__).resolve().parents[2] / "data" / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    path = upload_dir / f"{uuid4().hex}{suffix}"
    path.write_bytes(content)
    return {"success": True, "document_id": path.stem, "filename": Path(file.filename or "policy").name, "status": "uploaded_not_ingested"}


@router.post("/documents/ingest")
async def ingest_documents():
    root = Path(__file__).resolve().parents[2] / "knowledge_base"
    upload_dir = Path(__file__).resolve().parents[2] / "data" / "uploads"
    documents = load_policy_documents(root)
    if upload_dir.exists():
        documents.extend(load_policy_documents(upload_dir))
    try:
        result = await run_in_threadpool(index_documents, documents)
        return {"success": True, **result}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Document ingestion unavailable: {type(exc).__name__}") from exc