#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "frontend/apps/web/src"
OUT = ROOT / "artifacts/frontend-delivery-hardening/ui-inventory.json"

PATTERNS = {
    "layout": r"LayoutShell|AppShell|sc-page",
    "page_identity": r"PageIdentity|headline|breadcrumb",
    "button": r"<button\b|sc-btn",
    "table": r"<table\b|sc-table",
    "form_field": r"<(?:input|select|textarea)\b|sc-form-label",
    "money": r"MoneyFact|currency|amount",
    "status": r"StatusBadge|sc-badge|role=\"status\"",
    "relationship": r"RelationshipSection|RelatedRecordLink|relationship",
    "dialog": r"<dialog\b|role=\"dialog\"|sc-dialog",
    "loading": r"loading|skeleton|aria-busy",
    "empty": r"sc-empty|暂无|empty",
    "permission_denied": r"AccessDenied|无权访问",
    "not_found": r"NotFound|记录不存在",
    "inline_error": r"role=\"alert\"|sc-alert|validation-error",
    "toast": r"toast|notification|role=\"status\"",
    "responsive_breakpoint": r"@media\s*\(",
    "token_reference": r"var\(--sc-",
    "inline_style": r"\sstyle=\"",
}
COLOR = re.compile(r"#[0-9a-fA-F]{3,8}\b|rgba?\(")
PIXEL = re.compile(r"(?<![-\w])(?:font-size|padding|margin|gap|border-radius)\s*:\s*[^;{}]*\b\d+(?:\.\d+)?px")
MODEL_CSS = re.compile(r"\.(?:project|contract|settlement|payment)[-_][\w-]+\s*\{")


def main() -> None:
    files = [p for p in SRC.rglob("*") if p.suffix in {".vue", ".ts", ".css"}]
    totals: Counter[str] = Counter()
    per_file: dict[str, dict[str, int]] = {}
    direct_colors: list[dict[str, object]] = []
    direct_dimensions: list[dict[str, object]] = []
    model_css: list[dict[str, object]] = []
    for path in sorted(files):
        text = path.read_text(encoding="utf-8", errors="ignore")
        rel = path.relative_to(ROOT).as_posix()
        counts = {name: len(re.findall(pattern, text, re.I)) for name, pattern in PATTERNS.items()}
        if any(counts.values()):
            per_file[rel] = {key: value for key, value in counts.items() if value}
            totals.update(counts)
        for label, regex, bucket in (
            ("color", COLOR, direct_colors),
            ("dimension", PIXEL, direct_dimensions),
            ("model_css", MODEL_CSS, model_css),
        ):
            for match in regex.finditer(text):
                bucket.append({"file": rel, "line": text.count("\n", 0, match.start()) + 1, "value": match.group(0), "kind": label})
    payload = {
        "schema_version": 1,
        "source_files": len(files),
        "pattern_totals": dict(sorted(totals.items())),
        "direct_color_references": direct_colors,
        "direct_spacing_or_type_references": direct_dimensions,
        "model_specific_css": model_css,
        "files": per_file,
        "classification": {
            "fixed_in_fe_b06": ["recoverable status surface", "focus visibility", "responsive overflow containment", "session/company request isolation"],
            "retained_debt": ["legacy configuration and low-code surfaces retain local presentation CSS"],
            "outside_first_delivery": ["notification center visual redesign", "non-authoritative configuration surfaces"],
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[frontend_delivery_ui_inventory] PASS files={len(files)} output={OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
