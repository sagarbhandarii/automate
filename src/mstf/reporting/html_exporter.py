"""HTML dashboard exporter for run reports."""

from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Any


class HTMLDashboardExporter:
    """Converts structured report payloads into a visual HTML dashboard."""

    def render(self, report: dict[str, Any]) -> str:
        """Render a complete HTML dashboard string for a run report."""
        summary = report.get("summary", {})
        device_info = report.get("device_info", {})
        test_results = report.get("test_results", [])
        logs = report.get("logs", [])
        metrics = report.get("performance_metrics", {})

        summary_cards = "".join(
            self._summary_card(label, summary.get(key, 0), class_name)
            for key, label, class_name in [
                ("total", "Total", "neutral"),
                ("passed", "Passed", "pass"),
                ("failed", "Failed", "fail"),
                ("skipped", "Skipped", "neutral"),
            ]
        )

        device_rows = "".join(
            f"<tr><th>{escape(str(key))}</th><td>{escape(str(value))}</td></tr>"
            for key, value in sorted(device_info.items())
        )

        result_rows = "".join(
            "<tr>"
            f"<td>{escape(str(item.get('suite_id', 'unknown')))}</td>"
            f"<td class='status {escape(str(item.get('status', 'unknown')).lower())}'>{escape(str(item.get('status', 'unknown')))}</td>"
            f"<td>{escape(str(item.get('device_serial', '-')))}</td>"
            f"<td>{escape(str(item.get('duration_seconds', '-')))}</td>"
            "</tr>"
            for item in test_results
        )

        metrics_block = self._render_metrics(metrics)
        logs_block = "\n".join(escape(entry) for entry in logs)

        return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Run Report: {escape(str(report.get('run_id', 'unknown')))}</title>
  <style>
    :root {{ --bg:#0f172a; --card:#111827; --text:#e5e7eb; --muted:#94a3b8; --pass:#16a34a; --fail:#dc2626; --neutral:#0ea5e9; --border:#1f2937; }}
    body {{ margin:0; font-family: Inter, Segoe UI, Roboto, Arial, sans-serif; background:var(--bg); color:var(--text); }}
    .container {{ max-width: 1200px; margin: 0 auto; padding: 24px; }}
    h1, h2 {{ margin: 0 0 12px; }}
    .grid {{ display:grid; grid-template-columns: repeat(auto-fit,minmax(160px,1fr)); gap: 12px; margin-bottom: 18px; }}
    .card {{ background:var(--card); border:1px solid var(--border); border-radius: 10px; padding: 14px; }}
    .card .label {{ color:var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: .08em; }}
    .card .value {{ font-size: 28px; font-weight: 700; margin-top: 8px; }}
    .pass {{ color:var(--pass); }} .fail {{ color:var(--fail); }} .neutral {{ color:var(--neutral); }}
    .section {{ background:var(--card); border:1px solid var(--border); border-radius:10px; padding:14px; margin-bottom:14px; }}
    table {{ width:100%; border-collapse: collapse; }}
    th, td {{ text-align:left; border-bottom:1px solid var(--border); padding:8px 6px; font-size: 14px; }}
    th {{ color: var(--muted); font-weight: 600; }}
    pre {{ background:#020617; border-radius:8px; padding:12px; max-height: 300px; overflow:auto; white-space: pre-wrap; }}
    .status.passed {{ color:var(--pass); font-weight:700; }}
    .status.failed {{ color:var(--fail); font-weight:700; }}
    .status.skipped {{ color:var(--neutral); font-weight:700; }}
  </style>
</head>
<body>
  <div class="container">
    <h1>Execution Report</h1>
    <p>Run ID: <strong>{escape(str(report.get('run_id', 'unknown')))}</strong></p>

    <div class="grid">{summary_cards}</div>

    <div class="section">
      <h2>Device Info</h2>
      <table>{device_rows}</table>
    </div>

    <div class="section">
      <h2>Test Results</h2>
      <table>
        <thead><tr><th>Suite</th><th>Status</th><th>Device</th><th>Duration (s)</th></tr></thead>
        <tbody>{result_rows}</tbody>
      </table>
    </div>

    <div class="section">
      <h2>Performance Metrics</h2>
      {metrics_block}
    </div>

    <div class="section">
      <h2>Logs</h2>
      <pre>{logs_block}</pre>
    </div>
  </div>
</body>
</html>
"""

    def write(self, report: dict[str, Any], output_path: str | Path) -> Path:
        """Write rendered dashboard HTML to disk."""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.render(report), encoding="utf-8")
        return path

    def _summary_card(self, label: str, value: Any, class_name: str) -> str:
        return (
            "<div class='card'>"
            f"<div class='label'>{escape(label)}</div>"
            f"<div class='value {escape(class_name)}'>{escape(str(value))}</div>"
            "</div>"
        )

    def _render_metrics(self, metrics: dict[str, Any] | list[dict[str, Any]]) -> str:
        if isinstance(metrics, dict):
            rows = "".join(
                f"<tr><th>{escape(str(name))}</th><td>{escape(str(value))}</td></tr>"
                for name, value in metrics.items()
            )
            return f"<table>{rows}</table>"

        rows = "".join(
            "<tr>"
            f"<td>{escape(str(item.get('name', 'metric')))}</td>"
            f"<td>{escape(str(item.get('value', '-')))}</td>"
            f"<td>{escape(str(item.get('unit', '')))}</td>"
            f"<td>{escape(str(item.get('threshold', '-')))}</td>"
            "</tr>"
            for item in metrics
        )
        return (
            "<table>"
            "<thead><tr><th>Name</th><th>Value</th><th>Unit</th><th>Threshold</th></tr></thead>"
            f"<tbody>{rows}</tbody>"
            "</table>"
        )
