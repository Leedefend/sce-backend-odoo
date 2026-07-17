#!/usr/bin/env python3
"""Guard the single generic page-width contract and its formal consumers."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "frontend/apps/web/src"
REPORT = ROOT / "artifacts/frontend-professional/fe-pro-04w/nested-width-inventory.json"

FILES = {
    "contract": WEB / "components/design-system/pageWidth.ts",
    "page": WEB / "components/design-system/ScPage.vue",
    "layout": WEB / "components/template/LayoutShell.vue",
    "patterns": WEB / "styles/product-patterns.css",
    "tokens": WEB / "styles/design-system.css",
    "list": WEB / "pages/ListPage.css",
    "action": WEB / "views/ActionView.vue",
    "form": WEB / "pages/ContractFormPage.vue",
    "form_css": WEB / "pages/contractForm/ContractFormPage.css",
    "renderer": WEB / "components/page/PageRenderer.vue",
    "my_work": WEB / "views/MyWorkView.vue",
}

FORMAL_LAYOUT_FILES = [
    FILES["page"],
    FILES["layout"],
    FILES["list"],
    FILES["action"],
    FILES["form"],
    FILES["form_css"],
    FILES["renderer"],
    FILES["my_work"],
]


def fail(message: str) -> None:
    raise SystemExit(f"[frontend_page_width_contract_guard] FAIL {message}")


def read(key: str) -> str:
    path = FILES[key]
    if not path.exists():
        fail(f"missing {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def require(text: str, token: str, label: str) -> None:
    if token not in text:
        fail(f"{label}: missing {token}")


contract = read("contract")
page = read("page")
layout = read("layout")
patterns = read("patterns")
tokens = read("tokens")
list_css = read("list")
action = read("action")
form = read("form")
form_css = read("form_css")
renderer = read("renderer")
my_work = read("my_work")

for mode in ("data", "standard", "focused", "fluid"):
    require(contract, f"'{mode}'", "PageWidthMode")
    require(patterns, f".sc-page-frame--{mode}", "page frame CSS")

require(contract, "contractWidthMode", "contract priority")
require(contract, "PAGE_KIND_WIDTH_MODE", "page-kind mapping")
require(contract, "return PAGE_KIND_WIDTH_MODE[options.pageKind || 'unknown'] || 'standard'", "safe fallback")
for token in (
    "--sc-page-width-data: 1920px",
    "--sc-page-width-standard: 1440px",
    "--sc-page-width-focused: 1080px",
    "--sc-page-padding-wide: 32px",
    "--sc-page-padding-compact: 24px",
    "--sc-page-padding-mobile: 16px",
):
    require(tokens, token, "page width tokens")

for source, label in ((page, "ScPage"), (layout, "LayoutShell")):
    require(source, "pageWidthModeClass", label)
    require(source, "data-page-width-mode", label)

if re.search(r"max-width\s*:", layout):
    fail("LayoutShell owns a second max-width")
if "overflow-x: scroll" in list_css:
    fail("ListPage restored unconditional horizontal scrolling")
require(list_css, "overflow-x: auto", "ListPage local overflow")
if "overflow-x: hidden" in list_css:
    fail("ListPage hides horizontal overflow")

for source, label, page_kind in (
    (action, "ActionView", "'list'"),
    (form, "ContractFormPage", "'create'"),
    (my_work, "MyWorkView", "'workbench'"),
):
    require(source, "resolvePageWidthMode", label)
    require(source, "contractPageWidthMode", label)
    require(source, page_kind, label)

for forbidden in (
    r"model\s*===?.{0,100}(?:widthMode|width_mode)",
    r"(?:widthMode|width_mode).{0,100}model\s*===?",
    r"role.{0,100}(?:widthMode|width_mode)",
    r"(?:widthMode|width_mode).{0,100}role",
    r"xml.?id.{0,100}(?:widthMode|width_mode)",
):
    for path in FORMAL_LAYOUT_FILES + [FILES["contract"]]:
        if re.search(forbidden, path.read_text(encoding="utf-8"), re.IGNORECASE | re.DOTALL):
            fail(f"business-specific width inference in {path.relative_to(ROOT)}")

legacy_selectors = {
    FILES["form_css"]: (".page--flow",),
    FILES["renderer"]: (".page-renderer",),
    FILES["action"]: (".page",),
    FILES["list"]: (".page",),
}
inventory: list[dict[str, object]] = []
property_pattern = re.compile(r"(?:max-width\s*:|width\s*:\s*min\(|margin(?:-inline)?\s*:\s*0\s+auto)")
for path in FORMAL_LAYOUT_FILES + [FILES["patterns"]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    selector = ""
    for number, line in enumerate(lines, 1):
        stripped = line.strip()
        if "{" in stripped:
            selector = stripped.split("{", 1)[0].strip()
        if stripped.endswith("{"):
            selector = stripped[:-1].strip()
        if not property_pattern.search(stripped):
            continue
        category = "COMPONENT_INTERNAL_WIDTH"
        if path == FILES["patterns"] and "sc-page-frame" in selector:
            category = "PAGE_FRAME"
        elif selector in legacy_selectors.get(path, ()):
            category = "LEGACY_OVERRIDE"
        elif path == FILES["renderer"] and selector == ".page-renderer":
            category = "LEGACY_OVERRIDE"
        inventory.append({
            "file": str(path.relative_to(ROOT)),
            "line": number,
            "selector": selector,
            "declaration": stripped,
            "category": category,
        })

legacy = [row for row in inventory if row["category"] == "LEGACY_OVERRIDE"]
if legacy:
    fail(f"legacy page-width overrides remain: {legacy}")
if not any(row["category"] == "PAGE_FRAME" for row in inventory):
    fail("page-frame authority inventory is empty")

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "schema_version": "frontend_page_width_nested_inventory.v1",
    "authority": "styles/product-patterns.css:.sc-page-frame",
    "entries": inventory,
    "counts": {
        category: sum(1 for row in inventory if row["category"] == category)
        for category in ("PAGE_FRAME", "CONTENT_READING_WIDTH", "COMPONENT_INTERNAL_WIDTH", "LEGACY_OVERRIDE", "UNRESOLVED")
    },
}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

print(f"[frontend_page_width_contract_guard] PASS entries={len(inventory)} report={REPORT.relative_to(ROOT)}")
