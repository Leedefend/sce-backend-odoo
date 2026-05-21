#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate a static HTML review page for user project reconciliation."""

from __future__ import annotations

import argparse
import csv
import html
import json
from collections import defaultdict
from pathlib import Path


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def esc(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def evidence_label(value: str) -> str:
    if not value:
        return "无"
    parts = value.split(";")
    return "；".join(parts[:4]) + ("；..." if len(parts) > 4 else "")


def render_badge(text: str, kind: str = "") -> str:
    return f'<span class="badge {esc(kind)}">{esc(text)}</span>'


def render_summary(summary: dict) -> str:
    status = summary.get("status_counts") or {}
    actions = summary.get("action_counts") or {}
    cards = [
        ("用户清单", summary.get("source_rows", ""), "734 条项目名称与经营方式"),
        ("已确认", status.get("exact_with_business_evidence", 0), "名称命中且有业务依据"),
        ("重复待确认", status.get("duplicate_with_canonical_candidate", 0), "需要确认事实承载项目"),
        ("未命中", status.get("missing_no_business_evidence", 0) + status.get("missing_with_text_evidence", 0), "新项目或别名待判断"),
        ("无业务依据", status.get("exact_without_business_evidence", 0), "命中项目但未发现强业务事实"),
    ]
    html_cards = []
    for title, count, note in cards:
        html_cards.append(
            f'<div class="metric"><div class="metric-title">{esc(title)}</div>'
            f'<div class="metric-count">{esc(count)}</div><div class="metric-note">{esc(note)}</div></div>'
        )
    action_rows = "".join(
        f"<tr><td>{esc(key)}</td><td>{esc(value)}</td></tr>" for key, value in sorted(actions.items())
    )
    return (
        '<section class="summary"><div class="metrics">'
        + "".join(html_cards)
        + "</div>"
        + '<table class="compact"><thead><tr><th>建议动作</th><th>数量</th></tr></thead><tbody>'
        + action_rows
        + "</tbody></table></section>"
    )


def render_missing(rows: list[dict[str, str]]) -> str:
    body = []
    for idx, row in enumerate(rows, 1):
        text_evidence = row.get("text_evidence_tables") or ""
        status = row.get("status") or ""
        body.append(
            "<tr>"
            f"<td>{idx}</td>"
            f"<td class='name'>{esc(row.get('source_project_name'))}</td>"
            f"<td>{render_badge(row.get('operation_strategy'), row.get('operation_strategy'))}</td>"
            f"<td>{render_badge('有文本依据' if text_evidence else '无业务依据', 'warn' if text_evidence else 'muted')}</td>"
            f"<td>{esc(text_evidence or '未在核心历史事实表中找到 exact 文本命中')}</td>"
            "<td class='decision'>□ 新建项目　□ 作为别名　□ 暂不纳入　□ 需补资料</td>"
            "<td class='memo'></td>"
            "</tr>"
        )
    return render_section(
        "未命中项目确认",
        "用户清单中有名称，但当前 project.project 没有 exact match。不能按名称自动挂业务，需要用户确认是新项目、别名还是暂不纳入。",
        ["#", "项目名称", "经营方式", "依据状态", "已找到依据", "用户确认", "备注"],
        body,
        "missing",
    )


def render_no_evidence(rows: list[dict[str, str]]) -> str:
    body = []
    for idx, row in enumerate(rows, 1):
        body.append(
            "<tr>"
            f"<td>{idx}</td>"
            f"<td class='name'>{esc(row.get('source_project_name'))}</td>"
            f"<td>{render_badge(row.get('operation_strategy'), row.get('operation_strategy'))}</td>"
            f"<td>{esc(row.get('canonical_project_id'))}</td>"
            f"<td>{esc(row.get('legacy_project_id'))}</td>"
            f"<td>{render_badge('active' if row.get('active') == 'True' else 'inactive', 'ok' if row.get('active') == 'True' else 'muted')}</td>"
            "<td class='decision'>□ 保留　□ 暂不纳入　□ 需补业务依据</td>"
            "<td class='memo'></td>"
            "</tr>"
        )
    return render_section(
        "无强业务依据项目确认",
        "这些名称已命中项目主数据，但在本轮核心合同、收付款、材料、投标、SCBS 等事实表里未找到强业务依据。",
        ["#", "项目名称", "经营方式", "项目ID", "旧项目ID", "状态", "用户确认", "备注"],
        body,
        "no-evidence",
    )


def render_duplicates(rows: list[dict[str, str]]) -> str:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row.get("source_project_name", "")].append(row)
    body = []
    idx = 0
    for name, candidates in grouped.items():
        idx += 1
        first = True
        for row in candidates:
            recommended = row.get("recommended") == "True"
            body.append(
                "<tr>"
                f"<td>{idx if first else ''}</td>"
                f"<td class='name'>{esc(name) if first else ''}</td>"
                f"<td>{render_badge(row.get('operation_strategy'), row.get('operation_strategy')) if first else ''}</td>"
                f"<td>{esc(row.get('candidate_project_id'))}</td>"
                f"<td class='name'>{esc(row.get('candidate_project_name'))}</td>"
                f"<td>{render_badge('active' if row.get('candidate_active') == 'True' else 'inactive', 'ok' if row.get('candidate_active') == 'True' else 'muted')}</td>"
                f"<td class='num'>{esc(row.get('candidate_evidence_total'))}</td>"
                f"<td>{render_badge('推荐' if recommended else '候选', 'ok' if recommended else 'muted')}</td>"
                f"<td>{esc(evidence_label(row.get('candidate_evidence_tables', '')))}</td>"
                "<td class='decision'>□ 确认为承载项目　□ 非承载项目　□ 需人工判断</td>"
                "</tr>"
            )
            first = False
    return render_section(
        "重复名称 canonical 确认",
        "同一个用户项目名称命中多个 project.project。推荐项按业务事实量优先，但仍需要用户确认，不能自动合并或重挂业务。",
        ["#", "用户项目名称", "经营方式", "候选项目ID", "候选项目名", "状态", "事实数", "推荐", "事实来源", "用户确认"],
        body,
        "duplicates",
    )


def render_section(title: str, desc: str, headers: list[str], body_rows: list[str], section_id: str) -> str:
    header_html = "".join(f"<th>{esc(item)}</th>" for item in headers)
    body_html = "".join(body_rows) or f"<tr><td colspan='{len(headers)}'>无</td></tr>"
    return (
        f'<section id="{esc(section_id)}">'
        f"<h2>{esc(title)}</h2><p>{esc(desc)}</p>"
        f"<div class='table-wrap'><table><thead><tr>{header_html}</tr></thead><tbody>{body_html}</tbody></table></div>"
        "</section>"
    )


def render_html(summary: dict, missing: list[dict[str, str]], no_evidence: list[dict[str, str]], duplicates: list[dict[str, str]]) -> str:
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>项目主数据确认表 2026-05-20</title>
  <style>
    :root {{
      color-scheme: light;
      --text: #1f2933;
      --muted: #697386;
      --line: #d7dde6;
      --bg: #f6f8fb;
      --panel: #ffffff;
      --accent: #1769aa;
      --ok: #1f7a4d;
      --warn: #9a5b00;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font: 14px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif;
      color: var(--text);
      background: var(--bg);
    }}
    header {{
      padding: 28px 32px 18px;
      background: var(--panel);
      border-bottom: 1px solid var(--line);
    }}
    h1 {{ margin: 0 0 8px; font-size: 24px; }}
    h2 {{ margin: 0 0 8px; font-size: 18px; }}
    p {{ margin: 0 0 14px; color: var(--muted); }}
    main {{ padding: 24px 32px 48px; }}
    section {{
      margin: 0 0 24px;
      padding: 20px;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
    }}
    .metrics {{
      display: grid;
      grid-template-columns: repeat(5, minmax(120px, 1fr));
      gap: 12px;
      margin-bottom: 18px;
    }}
    .metric {{
      padding: 14px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fbfcfe;
    }}
    .metric-title {{ color: var(--muted); font-size: 12px; }}
    .metric-count {{ margin: 4px 0; font-size: 24px; font-weight: 700; }}
    .metric-note {{ color: var(--muted); font-size: 12px; }}
    .table-wrap {{ overflow-x: auto; border: 1px solid var(--line); border-radius: 6px; }}
    table {{ width: 100%; border-collapse: collapse; min-width: 1040px; background: white; }}
    .compact {{ min-width: 360px; max-width: 560px; }}
    th, td {{
      padding: 9px 10px;
      border-bottom: 1px solid var(--line);
      border-right: 1px solid var(--line);
      text-align: left;
      vertical-align: top;
      white-space: nowrap;
    }}
    th {{ position: sticky; top: 0; z-index: 1; background: #edf2f7; font-weight: 650; }}
    td.name {{ white-space: normal; min-width: 260px; }}
    td.decision {{ min-width: 260px; color: #334155; }}
    td.memo {{ min-width: 180px; }}
    td.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
    .badge {{
      display: inline-block;
      padding: 2px 7px;
      border-radius: 999px;
      background: #e8eef7;
      color: #31445f;
      font-size: 12px;
      line-height: 18px;
    }}
    .badge.direct {{ background: #e8f4ff; color: #1769aa; }}
    .badge.joint {{ background: #edf7ed; color: #1f7a4d; }}
    .badge.ok {{ background: #e4f5eb; color: var(--ok); }}
    .badge.warn {{ background: #fff1d6; color: var(--warn); }}
    .badge.muted {{ background: #eef1f5; color: var(--muted); }}
    nav {{ margin-top: 12px; display: flex; gap: 10px; flex-wrap: wrap; }}
    nav a {{ color: var(--accent); text-decoration: none; font-weight: 600; }}
    @media print {{
      body {{ background: white; }}
      main {{ padding: 0; }}
      section, header {{ border: 0; border-radius: 0; break-inside: avoid; }}
      .table-wrap {{ overflow: visible; }}
      th {{ position: static; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>项目主数据确认表</h1>
    <p>确认范围：用户导出的项目名称与经营方式。业务事实关联不按名称自动重挂；重复、缺失、无依据项需要用户确认。</p>
    <nav>
      <a href="#missing">未命中项目</a>
      <a href="#duplicates">重复名称</a>
      <a href="#no-evidence">无强业务依据</a>
    </nav>
  </header>
  <main>
    {render_summary(summary)}
    {render_missing(missing)}
    {render_duplicates(duplicates)}
    {render_no_evidence(no_evidence)}
  </main>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", default="/tmp/project_master_stabilization_host")
    parser.add_argument("--out", default="artifacts/project_master_stabilization/user_project_master_review_20260520.html")
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    summary = read_json(input_dir / "user_project_master_reconciliation_20260520_result.json")
    missing = read_csv(input_dir / "user_project_master_reconciliation_20260520_missing_review.csv")
    no_evidence = read_csv(input_dir / "user_project_master_reconciliation_20260520_no_evidence_review.csv")
    duplicates = read_csv(input_dir / "user_project_master_reconciliation_20260520_duplicate_canonical_review.csv")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_html(summary, missing, no_evidence, duplicates), encoding="utf-8")
    print(f"USER_PROJECT_REVIEW_HTML={out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
