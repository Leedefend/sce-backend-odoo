"""Render SCBS decision workbooks as browser-friendly HTML review pages."""

from __future__ import annotations

import csv
import html
import json
import os
from collections import defaultdict
from pathlib import Path


def artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.extend([Path.cwd() / "artifacts/migration", Path("/mnt/artifacts/migration"), Path("/tmp")])
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return Path("artifacts/migration")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def esc(value: object) -> str:
    return html.escape("" if value is None else str(value))


def money(value: object) -> str:
    try:
        return f"{float(value):,.2f}"
    except Exception:
        return esc(value)


def render_candidate_table(candidates: list[dict[str, str]]) -> str:
    if not candidates:
        return '<p class="muted">无候选目标。需要人工在系统中查找或保持 conflict。</p>'
    rows = []
    for candidate in candidates:
        rows.append(
            "<tr>"
            f"<td>{esc(candidate.get('candidate_partner_id'))}</td>"
            f"<td>{esc(candidate.get('candidate_name'))}</td>"
            f"<td>{esc(candidate.get('candidate_vat'))}</td>"
            f"<td>{esc(candidate.get('candidate_legacy_tax_no'))}</td>"
            f"<td>{esc(candidate.get('match_reason'))}</td>"
            f"<td>{esc(candidate.get('confidence'))}</td>"
            f"<td>{esc(candidate.get('candidate_active'))}</td>"
            "</tr>"
        )
    return (
        "<table class=\"candidate\"><thead><tr>"
        "<th>候选ID</th><th>候选名称</th><th>税号</th><th>旧税号</th>"
        "<th>匹配原因</th><th>置信度</th><th>启用</th>"
        "</tr></thead><tbody>"
        + "\n".join(rows)
        + "</tbody></table>"
    )


def render_manual_partner_required(artifacts: Path) -> Path:
    workbook = read_csv(artifacts / "scbs_mapping_decision_01_manual_partner_required_v1.csv")
    candidate_rows = read_csv(artifacts / "scbs_partner_target_candidate_report_v1.csv")
    candidates_by_map: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in candidate_rows:
        if row.get("suggested_action") == "manual_partner_required":
            candidates_by_map[row.get("map_id", "")].append(row)

    cards = []
    for index, row in enumerate(workbook, start=1):
        map_id = row.get("map_id", "")
        candidates = candidates_by_map.get(map_id, [])
        cards.append(
            "<section class=\"card\">"
            f"<h2>{index}. {esc(row.get('legacy_name'))}</h2>"
            "<div class=\"meta\">"
            f"<span>映射ID: <b>{esc(map_id)}</b></span>"
            f"<span>旧税号键: <b>{esc(row.get('legacy_key'))}</b></span>"
            f"<span>事实行: <b>{esc(row.get('fact_rows'))}</b></span>"
            f"<span>金额: <b>{money(row.get('fact_amount'))}</b></span>"
            "</div>"
            "<div class=\"decision\">"
            "<b>需要业务填写：</b> decision=confirm/conflict；如 confirm，填写 decision_target_id 为下面候选ID之一。"
            "</div>"
            f"{render_candidate_table(candidates)}"
            "</section>"
        )

    output = artifacts / "scbs_review_01_manual_partner_required_v1.html"
    output.write_text(
        "<!doctype html><html><head><meta charset=\"utf-8\">"
        "<title>SCBS 税号冲突往来单位审阅</title>"
        "<style>"
        "body{font-family:Arial,'Microsoft YaHei',sans-serif;margin:24px;background:#f7f7f7;color:#222}"
        "h1{font-size:24px;margin:0 0 8px}.intro{margin:0 0 20px;color:#555}"
        ".card{background:#fff;border:1px solid #ddd;border-radius:6px;padding:16px;margin:0 0 16px}"
        "h2{font-size:18px;margin:0 0 10px}.meta{display:flex;flex-wrap:wrap;gap:12px;margin-bottom:10px;color:#444}"
        ".decision{background:#fff8e5;border:1px solid #f0d58a;padding:10px;margin:10px 0;border-radius:4px}"
        "table{border-collapse:collapse;width:100%;font-size:13px}th,td{border:1px solid #ddd;padding:7px;text-align:left;vertical-align:top}"
        "th{background:#f0f0f0}.muted{color:#777}"
        "</style></head><body>"
        "<h1>SCBS 税号冲突往来单位审阅</h1>"
        "<p class=\"intro\">本页对应 priority 1 批次：31 个 tax_code_conflict 映射。只读审阅页，不会写数据库。</p>"
        + "\n".join(cards)
        + "</body></html>",
        encoding="utf-8",
    )
    return output


def main() -> None:
    artifacts = artifact_root()
    manual_partner_html = render_manual_partner_required(artifacts)
    result = {
        "status": "PASS",
        "manual_partner_required_html": str(manual_partner_html),
    }
    result_path = artifacts / "scbs_mapping_decision_html_export_result_v1.json"
    result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("SCBS_MAPPING_DECISION_HTML_EXPORT=" + json.dumps(result, ensure_ascii=False, sort_keys=True))


main()
