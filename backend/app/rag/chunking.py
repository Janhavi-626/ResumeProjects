import hashlib


def chunk_documents(documents: list[dict], max_chars: int = 900) -> list[dict]:
    chunks = []
    for document in documents:
        text = document["text"]
        paragraphs = [part.strip() for part in text.split("\n\n") if part.strip()]
        current = ""
        pieces = []
        for paragraph in paragraphs:
            if current and len(current) + len(paragraph) > max_chars:
                pieces.append(current)
                current = ""
            current = f"{current}\n\n{paragraph}".strip()
        if current:
            pieces.append(current)
        for index, piece in enumerate(pieces, start=1):
            identity = f"{document['document_id']}|{document['version']}|{document['section']}|{index}|{piece}"
            digest = hashlib.sha1(identity.encode()).hexdigest()[:12]
            chunks.append({**{key: value for key, value in document.items() if key != "text"}, "chunk_id": f"{document['document_id']}-{digest}", "chunk_index": index, "text": piece})
    return chunks