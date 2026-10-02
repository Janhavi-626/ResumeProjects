from pathlib import Path


def write_report(metrics: dict, rows: list[dict], destination: str | Path) -> None:
    content = ["# Returns Assistant Evaluation", "", f"Cases evaluated: {metrics['case_count']}", "", "## Metrics", ""]
    content.extend(f"- {key.replace('_', ' ').title()}: {value:.3f}" if isinstance(value, float) else f"- {key.replace('_', ' ').title()}: {value}" for key, value in metrics.items())
    content.extend(["", "## Case Results", "", "| Case | Group | Expected class | Actual class | Status | Citations | Latency (ms) |", "|---|---|---|---|---|---:|---:|"])
    content.extend(f"| {row['case_id']} | {row['group']} | {row.get('expected_classification') or '-'} | {row.get('classification', '-')} | {row.get('status', 'error')} | {row.get('citation_count', 0)} | {row.get('latency_ms', 0):.1f} |" for row in rows)
    Path(destination).write_text("\n".join(content) + "\n", encoding="utf-8")