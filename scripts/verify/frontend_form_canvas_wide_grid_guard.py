#!/usr/bin/env python3
"""Guard the full-width business form canvas and contract-driven responsive grid."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "frontend/apps/web/src"


def read(path: str) -> str:
    return (WEB / path).read_text(encoding="utf-8")


def fail(message: str) -> None:
    raise SystemExit(f"[frontend_form_canvas_wide_grid_guard] FAIL {message}")


tokens = read("styles/design-system.css")
patterns = read("styles/product-patterns.css")
form_css = read("pages/contractForm/ContractFormPage.css")
section = read("components/template/FormSection.vue")
mapper = read("components/template/fieldSpan.mapper.ts")
schema_builder = read("pages/contractForm/useRecordFormFieldSchemas.ts")

combined = "\n".join((tokens, patterns, form_css))
for forbidden in ("--sc-content-focused-form-max", "--sc-form-field-content-max"):
    if forbidden in combined:
        fail(f"canvas-level focused limit remains: {forbidden}")
if "max-width: none" not in form_css or ".contract-form-canvas-shell" not in form_css:
    fail("form canvas does not explicitly own full available width")
for required in (
    "container-type: inline-size",
    "@container (min-width: 680px)",
    "@container (min-width: 1240px)",
    "template-form-section-grid--columns-${columns}",
    "field--compact",
    "field--normal",
    "field--wide",
    "field--full",
):
    if required not in section:
        fail(f"responsive field grid contract missing: {required}")
for forbidden in ("fieldName", "description", "remark", "address", "location"):
    if forbidden in mapper:
        fail(f"field span guesses from business name/label: {forbidden}")
if "resolveFieldSpanClass({fieldType:" not in schema_builder:
    fail("schema builder does not use type-only safe span fallback")
for forbidden in ("model ===", "role ===", "overflow-x: hidden", "overflow-x: clip"):
    if forbidden in section or forbidden in form_css:
        fail(f"forbidden form-layout inference or overflow masking: {forbidden}")

print("[frontend_form_canvas_wide_grid_guard] PASS")
