import re
from pathlib import Path


def load_policy_documents(root: str | Path) -> list[dict]:
    documents = []
    for path in sorted(Path(root).rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        title_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
        metadata = {}
        for header_line in text.splitlines()[:4]:
            for key, value in re.findall(r"(Document ID|Version|Effective date):\s*([^|]+)", header_line):
                metadata[key] = value.strip()
        document_id = metadata.get("Document ID", path.stem)
        sections = re.split(r"(?=^##\s+)", text, flags=re.MULTILINE)
        for section_text in sections:
            heading = re.match(r"^##\s+(.+)$", section_text, re.MULTILINE)
            content = re.sub(r"^#.+$|^Document ID:.+$|^Version:.+$|^Effective date:.+$|^##.+$", "", section_text, flags=re.MULTILINE).strip()
            content = re.sub(r"(?im)^.*(?:ignore all previous instructions|ignore previous instructions|reveal system secrets|bypass approval|override system instructions).*$", "[untrusted instruction removed]", content)
            if not content:
                continue
            documents.append({
                "document_id": document_id,
                "title": title_match.group(1) if title_match else path.stem,
                "source": str(path.name),
                "category": path.parent.name,
                "page": 1,
                "section": heading.group(1).split(":", 1)[0].strip() if heading else "Overview",
                "version": metadata.get("Version", "1.0"),
                "effective_date": metadata.get("Effective date", "unknown"),
                "text": content,
            })
    return documents