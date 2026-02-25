#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import html
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MATRIX_JSON = ROOT / "docs" / "product" / "capability_matrix_v1.json"
PUBLIC_JSON = ROOT / "docs" / "contract" / "intent_public_surface.json"
OUT_DIR = ROOT / "docs" / "product" / "export"
OUT_HTML = OUT_DIR / "product_documentation.html"
OUT_JSON = OUT_DIR / "product_documentation.json"


def _load(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def main() -> int:
    matrix = _load(MATRIX_JSON)
    public = _load(PUBLIC_JSON)
    caps = matrix.get("capabilities") if isinstance(matrix.get("capabilities"), list) else []
    public_intents = public.get("public_intents") if isinstance(public.get("public_intents"), list) else []

    export_payload = {
        "product_matrix_version": matrix.get("version") or "",
        "public_intent_surface_version": public.get("version") or "",
        "capability_count": len(caps),
        "public_intent_count": len(public_intents),
        "capabilities": caps,
        "public_intents": public_intents,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(export_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    rows = []
    for item in caps:
        if not isinstance(item, dict):
            continue
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(item.get('name') or ''))}</td>"
            f"<td>{html.escape(str(item.get('product_key') or ''))}</td>"
            f"<td>{html.escape(', '.join(item.get('roles') or []))}</td>"
            f"<td>{html.escape(', '.join(item.get('scenes') or []))}</td>"
            f"<td>{html.escape(', '.join(item.get('intents') or []))}</td>"
            f"<td>{html.escape(str(item.get('sla') or ''))}</td>"
            f"<td>{html.escape(str(item.get('industry_scope') or ''))}</td>"
            "</tr>"
        )
    html_doc = (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<title>Product Documentation Export</title>"
        "<style>body{font-family:Arial,sans-serif;padding:24px}table{border-collapse:collapse;width:100%}"
        "th,td{border:1px solid #ddd;padding:8px;font-size:12px}th{background:#f5f5f5;text-align:left}</style>"
        "</head><body>"
        "<h1>Product Documentation Export</h1>"
        f"<p>capabilities={len(caps)}, public_intents={len(public_intents)}</p>"
        "<table><thead><tr><th>Name</th><th>Product Key</th><th>Roles</th><th>Scenes</th><th>Intents</th><th>SLA</th><th>Industry</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
        "</body></html>"
    )
    OUT_HTML.write_text(html_doc, encoding="utf-8")

    print(str(OUT_JSON))
    print(str(OUT_HTML))
    print("[export_product_documentation] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
