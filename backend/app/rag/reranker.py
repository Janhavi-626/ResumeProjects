import re


def rerank(query: str, results: list[dict]) -> list[dict]:
    terms = set(re.findall(r"[a-z0-9]+", query.lower()))

    def score(result):
        text = f"{result.get('title', '')} {result.get('section', '')} {result.get('text', '')}".lower()
        return sum(1 for term in terms if term in text), result.get("score", 0)

    return sorted(results, key=score, reverse=True)