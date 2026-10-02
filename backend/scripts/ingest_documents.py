from app.rag.indexer import index_documents
from app.rag.loaders import load_policy_documents


def main() -> None:
    from pathlib import Path

    root = Path(__file__).resolve().parents[1] / "knowledge_base"
    documents = load_policy_documents(root)
    result = index_documents(documents)
    print(f"Loaded {len(documents)} policy sections; stored {result['chunk_count']} SQL chunks and {result['vector_count']} Chroma vectors.")


if __name__ == "__main__":
    main()