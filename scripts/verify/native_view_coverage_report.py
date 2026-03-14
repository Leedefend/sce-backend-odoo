#!/usr/bin/env python3
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT_DIR = ROOT / "docs" / "contract" / "snapshots" / "native_view"
OUT_JSON = ROOT / "artifacts" / "backend" / "native_view_coverage_report.json"
OUT_MD = ROOT / "artifacts" / "backend" / "native_view_coverage_report.md"


def _load(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def main() -> int:
    files = sorted(SNAPSHOT_DIR.glob("*.json"))
    by_view_type = {"form": 0, "tree": 0, "kanban": 0, "search": 0, "other": 0}
    metrics = {
        "with_permission_verdicts": 0,
        "with_action_gating": 0,
        "with_search_semantics": 0,
        "with_kanban_semantics": 0,
        "with_actions_semantics": 0,
        "with_relation_items": 0,
    }

    rows = []
    for file in files:
        payload = _load(file)
        sp = payload.get("semantic_page") if isinstance(payload, dict) else {}
        if not isinstance(sp, dict):
            continue
        view_type = str(sp.get("view_type") or "other")
        if view_type not in by_view_type:
            view_type = "other"
        by_view_type[view_type] += 1

        has_permission_verdicts = isinstance(sp.get("permission_verdicts"), dict)
        has_action_gating = isinstance(sp.get("action_gating"), dict)
        has_search_semantics = isinstance(sp.get("search_semantics"), dict)
        has_kanban_semantics = isinstance(sp.get("kanban_semantics"), dict)
        has_actions_semantics = isinstance(sp.get("actions"), dict)

        has_relation_items = False
        zones = sp.get("zones") if isinstance(sp.get("zones"), list) else []
        for zone in zones:
            if not isinstance(zone, dict):
                continue
            blocks = zone.get("blocks") if isinstance(zone.get("blocks"), list) else []
            for block in blocks:
                if not isinstance(block, dict):
                    continue
                data = block.get("data") if isinstance(block.get("data"), dict) else {}
                items = data.get("items") if isinstance(data.get("items"), list) else []
                if items:
                    has_relation_items = True
                    break
            if has_relation_items:
                break

        metrics["with_permission_verdicts"] += 1 if has_permission_verdicts else 0
        metrics["with_action_gating"] += 1 if has_action_gating else 0
        metrics["with_search_semantics"] += 1 if has_search_semantics else 0
        metrics["with_kanban_semantics"] += 1 if has_kanban_semantics else 0
        metrics["with_actions_semantics"] += 1 if has_actions_semantics else 0
        metrics["with_relation_items"] += 1 if has_relation_items else 0

        rows.append(
            {
                "snapshot": file.name,
                "view_type": view_type,
                "has_permission_verdicts": has_permission_verdicts,
                "has_action_gating": has_action_gating,
                "has_search_semantics": has_search_semantics,
                "has_kanban_semantics": has_kanban_semantics,
                "has_actions_semantics": has_actions_semantics,
                "has_relation_items": has_relation_items,
            }
        )

    total = len(rows)
    coverage_ratio = {k: (round(v / total, 4) if total else 0.0) for k, v in metrics.items()}
    report = {
        "ok": total > 0,
        "summary": {
            "snapshot_count": total,
            "by_view_type": by_view_type,
            "metrics": metrics,
            "coverage_ratio": coverage_ratio,
        },
        "rows": rows,
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Native View Coverage Report",
        "",
        f"- ok: {report['ok']}",
        f"- snapshot_count: {total}",
        f"- by_view_type: {json.dumps(by_view_type, ensure_ascii=False)}",
        f"- metrics: {json.dumps(metrics, ensure_ascii=False)}",
        f"- coverage_ratio: {json.dumps(coverage_ratio, ensure_ascii=False)}",
        "",
        "## Rows",
    ]
    for row in rows:
        lines.append(
            "- "
            + f"{row['snapshot']} [{row['view_type']}] "
            + f"perm={row['has_permission_verdicts']} gate={row['has_action_gating']} "
            + f"search={row['has_search_semantics']} kanban={row['has_kanban_semantics']} "
            + f"actions={row['has_actions_semantics']} relation_items={row['has_relation_items']}"
        )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(OUT_JSON))
    print(str(OUT_MD))
    print("[native_view_coverage_report] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

