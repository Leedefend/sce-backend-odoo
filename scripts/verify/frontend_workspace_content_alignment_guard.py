#!/usr/bin/env python3
"""Guard the single business workspace frame and internal content-layout contract."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "frontend/apps/web/src"
REPORT = ROOT / "artifacts/frontend-professional/fe-pro-04wr/nested-width-inventory.json"
FILES = {
    "contract": WEB / "components/design-system/pageWidth.ts",
    "page": WEB / "components/design-system/ScPage.vue",
    "layout": WEB / "components/template/LayoutShell.vue",
    "patterns": WEB / "styles/product-patterns.css",
    "tokens": WEB / "styles/design-system.css",
    "list": WEB / "pages/ListPage.vue",
    "list_css": WEB / "pages/ListPage.css",
    "action": WEB / "views/ActionView.vue",
    "form": WEB / "pages/ContractFormPage.vue",
    "form_css": WEB / "pages/contractForm/ContractFormPage.css",
    "my_work": WEB / "views/MyWorkView.vue",
}


def fail(message: str) -> None:
    raise SystemExit(f"[frontend_workspace_content_alignment_guard] FAIL {message}")


def read(key: str) -> str:
    path = FILES[key]
    if not path.exists():
        fail(f"missing {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def require(text: str, token: str, label: str) -> None:
    if token not in text:
        fail(f"{label}: missing {token}")


sources = {key: read(key) for key in FILES}
contract = sources["contract"]
patterns = sources["patterns"]
tokens = sources["tokens"]
list_vue = sources["list"]
list_css = sources["list_css"]

require(contract, "type WorkspaceFrameMode = 'business'", "workspace frame type")
for mode in ("data-grid", "record-grid", "form-grid", "focused-form", "reading"):
    require(contract, f"'{mode}'", "content layout modes")
require(contract, "contractContentLayout", "formal contract priority")
require(contract, "PAGE_KIND_CONTENT_LAYOUT", "page-kind fallback")
require(contract, "content_layout_mode", "new content-layout contract field")
require(contract, "width_mode", "legacy width contract field")
require(contract, "legacy_width_mode", "legacy compatibility source")
require(contract, "mapped !== 'page-kind'", "legacy standard page-kind interpretation")
for forbidden in ("PageWidthMode", "resolvePageWidthMode", "contractPageWidthMode", "pageWidthModeClass"):
    if forbidden in contract:
        fail(f"retired outer-frame mode remains: {forbidden}")

for source_key in ("page", "layout"):
    source = sources[source_key]
    require(source, 'data-workspace-frame="business"', source_key)
    require(source, "contentLayoutModeClass", source_key)
    if "widthMode" in source or "width-mode" in source:
        fail(f"{source_key} still exposes outer width mode")
    if re.search(r"max-width\s*:", source):
        fail(f"{source_key} owns a second max-width")

require(tokens, "--sc-workspace-frame-max: 1920px", "workspace token")
require(tokens, "--sc-content-focused-form-max: 1080px", "focused content token")
require(patterns, "max-width: min(100%, var(--sc-workspace-frame-max))", "single workspace CSS authority")
require(patterns, ".sc-content-layout--focused-form", "internal focused layout")
if re.search(r"\.sc-page-frame--(?:data|standard|focused|fluid)", patterns):
    fail("outer frame mode selectors remain")
if re.search(r"\.router-host\s*\{[^}]*overflow-x\s*:\s*(?:hidden|clip)", patterns, re.DOTALL):
    fail("router-host hides or clips horizontal overflow")

for source_key, page_kind in (("action", "'list'"), ("form", "'create'"), ("my_work", "'workbench'")):
    source = sources[source_key]
    require(source, "resolveContentLayoutMode", source_key)
    require(source, "contractContentLayoutMode", source_key)
    require(source, page_kind, source_key)

for forbidden in (
    r"model\s*===?.{0,100}(?:contentLayout|content_layout)",
    r"(?:contentLayout|content_layout).{0,100}model\s*===?",
    r"role.{0,100}(?:contentLayout|content_layout)",
    r"(?:contentLayout|content_layout).{0,100}role",
    r"xml.?id.{0,100}(?:contentLayout|content_layout)",
):
    for key in ("contract", "page", "layout", "action", "form", "my_work"):
        if re.search(forbidden, sources[key], re.IGNORECASE | re.DOTALL):
            fail(f"business-specific layout inference in {FILES[key].relative_to(ROOT)}")

require(list_css, "overflow-x: auto", "table local overflow")
if "overflow-x: scroll" in list_css or "overflow-x: hidden" in list_css or "overflow-x: clip" in list_css:
    fail("ListPage uses unconditional or masking overflow")
require(list_vue, "minWidth: `max(100%, ${tableMinWidthPx.value}px)`", "table used-width algorithm")
for token in ("rowPrimary.value", "option?.cellRole", "option?.type", "columnLayoutRole"):
    require(list_vue, token, "contract-driven column layout")
require(list_css, ".column-layout-identity", "contract-driven column CSS")
long_text_body = re.search(r"function isLongTextColumn\(.*?\n\}", list_vue, re.DOTALL)
if long_text_body and ("columnLabel" in long_text_body.group(0) or "toLowerCase" in long_text_body.group(0)):
    fail("column layout still guesses semantics from field name or label")

inventory: list[dict[str, object]] = []
property_pattern = re.compile(r"(?:max-width\s*:|width\s*:\s*min\(|margin(?:-inline)?\s*:\s*0\s+auto)")
for key in ("patterns", "list_css", "form_css", "action", "form", "my_work"):
    path = FILES[key]
    selector = ""
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        stripped = line.strip()
        if "{" in stripped:
            selector = stripped.split("{", 1)[0].strip()
        if stripped.endswith("{"):
            selector = stripped[:-1].strip()
        if not property_pattern.search(stripped):
            continue
        category = "COMPONENT_INTERNAL_WIDTH"
        if key == "patterns" and "var(--sc-workspace-frame-max)" in stripped:
            category = "WORKSPACE_FRAME"
        elif "reading" in selector:
            category = "CONTENT_READING_WIDTH"
        inventory.append({"file": str(path.relative_to(ROOT)), "line": number, "selector": selector, "declaration": stripped, "category": category})

workspace_entries = [row for row in inventory if row["category"] == "WORKSPACE_FRAME"]
if len(workspace_entries) != 1:
    fail(f"expected one workspace max-width authority, got {len(workspace_entries)}")

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "schema_version": "frontend_workspace_content_width_inventory.v1",
    "authority": "styles/product-patterns.css:.sc-page-frame",
    "entries": inventory,
    "counts": {category: sum(1 for row in inventory if row["category"] == category) for category in ("WORKSPACE_FRAME", "CONTENT_READING_WIDTH", "COMPONENT_INTERNAL_WIDTH", "LEGACY_OVERRIDE", "UNRESOLVED")},
}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"[frontend_workspace_content_alignment_guard] PASS entries={len(inventory)} report={REPORT.relative_to(ROOT)}")
