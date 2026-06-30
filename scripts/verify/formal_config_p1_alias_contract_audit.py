# -*- coding: utf-8 -*-
"""Audit P1 alias fields that still appear in formal business config contracts.

This is a provenance guard for the formalization work.  It does not require an
Odoo runtime: it statically parses the published config contract XML and the
source alias label registry, then reports which visible config fields still come
from generated P1 aliases.
"""

from __future__ import annotations

import ast
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[2]
ALIAS_SOURCE = ROOT / "addons/smart_construction_core/models/support/p1_daily_business_visible_alias_fields.py"
OUT_JSON = ROOT / "artifacts/backend/formal_config_p1_alias_contract_audit.json"
OUT_CSV = ROOT / "artifacts/backend/formal_config_p1_alias_contract_audit_rows.csv"

CONFIG_CONTRACT_FILES = [
    ROOT / "addons/smart_construction_core/data/view_orchestration_contract_generated_data.xml",
    ROOT / "addons/smart_construction_core/data/view_orchestration_contract_data.xml",
    ROOT / "addons/smart_construction_core/data/view_orchestration_form_section_contract_data.xml",
    ROOT / "addons/smart_construction_core/data/p1_daily_business_form_orchestration_contract_data.xml",
]


def _alias_field_name(label: str) -> str:
    return "p1_visible_" + hashlib.sha1(label.encode("utf-8")).hexdigest()[:12]


def _literal_assignments(path: Path) -> dict[str, object]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=path.as_posix())
    values: dict[str, object] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id in {
                "P1_ALIAS_LABELS",
                "P1_ALIAS_COMPAT_LABELS",
                "LABEL_SOURCE_OVERRIDES",
                "MODEL_LABEL_SOURCE_OVERRIDES",
            }:
                values[target.id] = ast.literal_eval(node.value)
    return values


def _alias_labels_by_model() -> dict[str, dict[str, str]]:
    values = _literal_assignments(ALIAS_SOURCE)
    labels_by_model = values.get("P1_ALIAS_LABELS") or {}
    compat_by_model = values.get("P1_ALIAS_COMPAT_LABELS") or {}
    aliases: dict[str, dict[str, str]] = {}
    for model_name, labels in labels_by_model.items():
        merged = list(dict.fromkeys(list(labels) + list(compat_by_model.get(model_name, []))))
        aliases[model_name] = {_alias_field_name(label): label for label in merged}
    return aliases


def _candidate_sources() -> tuple[dict[str, list[str]], dict[str, dict[str, list[str]]]]:
    values = _literal_assignments(ALIAS_SOURCE)
    return (
        values.get("LABEL_SOURCE_OVERRIDES") or {},
        values.get("MODEL_LABEL_SOURCE_OVERRIDES") or {},
    )


def _field_text(record: ET.Element, name: str) -> str:
    for field in record.findall("field"):
        if field.get("name") == name:
            return (field.text or "").strip()
    return ""


def _field_eval(record: ET.Element, name: str) -> str:
    for field in record.findall("field"):
        if field.get("name") == name:
            return (field.get("eval") or field.text or "").strip()
    return ""


def _iter_contract_records(path: Path):
    if not path.exists():
        return
    root = ET.parse(path).getroot()
    for record in root.findall(".//record"):
        if record.get("model") != "ui.business.config.contract":
            continue
        contract_raw = _field_eval(record, "contract_json")
        if not contract_raw:
            continue
        try:
            contract_json = ast.literal_eval(contract_raw)
        except (SyntaxError, ValueError) as exc:
            raise ValueError("cannot parse contract_json in %s:%s: %s" % (path, record.get("id"), exc)) from exc
        yield {
            "path": path.relative_to(ROOT).as_posix(),
            "xml_id": record.get("id") or "",
            "name": _field_text(record, "name"),
            "model": _field_text(record, "model"),
            "view_type": _field_text(record, "view_type"),
            "contract_json": contract_json,
        }


def _walk_fields(value):
    if isinstance(value, dict):
        name = value.get("name")
        if isinstance(name, str) and name.startswith("p1_visible_"):
            yield value
        for child in value.values():
            yield from _walk_fields(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_fields(child)


def _scan():
    labels_by_model = _alias_labels_by_model()
    generic_candidates, model_candidates = _candidate_sources()
    rows = []
    for path in CONFIG_CONTRACT_FILES:
        for record in _iter_contract_records(path):
            model_aliases = labels_by_model.get(record["model"], {})
            for field in _walk_fields(record["contract_json"]):
                field_name = field["name"]
                label = model_aliases.get(field_name, "")
                candidates = list(
                    dict.fromkeys(
                        list(model_candidates.get(record["model"], {}).get(label, []))
                        + list(generic_candidates.get(label, []))
                    )
                )
                visible = field.get("visible", True) is not False
                rows.append({
                    "path": record["path"],
                    "xml_id": record["xml_id"],
                    "contract_name": record["name"],
                    "model": record["model"],
                    "view_type": record["view_type"],
                    "field": field_name,
                    "label": label,
                    "formal_candidates": candidates,
                    "candidate_count": len(candidates),
                    "sequence": field.get("sequence", ""),
                    "visible": visible,
                    "readonly": field.get("readonly", ""),
                })
    return rows


def _summary(rows):
    return {
        "total_hits": len(rows),
        "visible_hits": sum(1 for row in rows if row["visible"]),
        "hidden_hits": sum(1 for row in rows if not row["visible"]),
        "unknown_label_hits": sum(1 for row in rows if not row["label"]),
        "with_formal_candidate_hits": sum(1 for row in rows if row["formal_candidates"]),
        "without_formal_candidate_hits": sum(1 for row in rows if not row["formal_candidates"]),
        "by_model": dict(sorted(Counter(row["model"] for row in rows).items())),
        "with_formal_candidate_by_model": dict(sorted(Counter(row["model"] for row in rows if row["formal_candidates"]).items())),
        "by_file": dict(sorted(Counter(row["path"] for row in rows).items())),
    }


def _write_csv(rows):
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "path",
                "xml_id",
                "contract_name",
                "model",
                "view_type",
                "field",
                "label",
                "formal_candidates",
                "candidate_count",
                "sequence",
                "visible",
                "readonly",
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({
                **row,
                "formal_candidates": json.dumps(row["formal_candidates"], ensure_ascii=False),
            })


def _failures(rows):
    failures = []
    hidden = [row for row in rows if not row["visible"]]
    unknown = [row for row in rows if not row["label"]]
    if hidden:
        failures.append({
            "kind": "hidden_p1_alias_in_formal_config_contract",
            "count": len(hidden),
            "sample": hidden[:20],
        })
    if unknown:
        failures.append({
            "kind": "unknown_p1_alias_label",
            "count": len(unknown),
            "sample": unknown[:20],
        })
    return failures


def main():
    rows = _scan()
    report = {
        "mode": "formal_config_p1_alias_contract_audit",
        "boundary": {
            "alias_source": ALIAS_SOURCE.relative_to(ROOT).as_posix(),
            "config_contract_files": [path.relative_to(ROOT).as_posix() for path in CONFIG_CONTRACT_FILES],
            "policy": "formal config contracts must not contain hidden p1 aliases, and every remaining visible p1 alias must resolve to a known source label before it can be promoted to a formal field",
        },
        "summary": _summary(rows),
        "failures": _failures(rows),
        "rows": rows,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _write_csv(rows)
    status = "FAIL" if report["failures"] else "PASS"
    print(
        "[formal_config_p1_alias_contract_audit] %s total=%s visible=%s hidden=%s unknown_labels=%s"
        % (
            status,
            report["summary"]["total_hits"],
            report["summary"]["visible_hits"],
            report["summary"]["hidden_hits"],
            report["summary"]["unknown_label_hits"],
        )
    )
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    if report["failures"]:
        print(json.dumps({"failures": report["failures"]}, ensure_ascii=False, indent=2))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
