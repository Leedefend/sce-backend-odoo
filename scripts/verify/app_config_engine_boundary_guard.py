#!/usr/bin/env python3
"""Guard app_config_engine as runtime contract plumbing, not product authority."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
APP_ENGINE = ROOT / "addons" / "smart_core" / "app_config_engine"
DOC = APP_ENGINE / "docs" / "app_config_engine.md"
DOCS_DIR = APP_ENGINE / "docs"
CONTROLLER = APP_ENGINE / "controllers" / "contract_api.py"
SERVICE = APP_ENGINE / "services" / "contract_service.py"
NATIVE_PARSE = APP_ENGINE / "services" / "native_parse_service.py"
PAGE_ASSEMBLER = APP_ENGINE / "services" / "assemblers" / "page_assembler.py"
APP_VIEW_CONFIG = APP_ENGINE / "models" / "app_view_config.py"
ODOO_VIEW_PARSER = APP_ENGINE / "services" / "view_Parser" / "contract_Parser.py"
VIEW_PARSER_DOC = APP_ENGINE / "services" / "view_Parser" / "readme — Contract 2.md"

def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def _industry_refs(source: str) -> set[str]:
    refs: set[str] = set()
    marker = "smart_construction_core."
    start = 0
    while True:
        idx = source.find(marker, start)
        if idx < 0:
            break
        end = idx
        while end < len(source) and (source[end].isalnum() or source[end] in "._"):
            end += 1
        refs.add(source[idx:end])
        start = end
    return refs


def _industry_doc_tokens(source: str) -> set[str]:
    tokens = {
        "实付登记",
        "智慧施工",
        "施工",
        "付款",
        "发票",
        "材料",
        "劳务",
    }
    return {token for token in tokens if token in source}


def main() -> int:
    errors: list[str] = []
    doc = _read(DOC)
    controller = _read(CONTROLLER)
    service = _read(SERVICE)
    native_parse = _read(NATIVE_PARSE)
    page_assembler = _read(PAGE_ASSEMBLER)
    app_view_config = _read(APP_VIEW_CONFIG)
    odoo_view_parser = _read(ODOO_VIEW_PARSER)
    view_parser_doc = _read(VIEW_PARSER_DOC)

    for token in (
        "Runtime Contract Plumbing",
        "No Business Fact Authority",
        "Native Odoo Parse Boundary",
        "View Orchestration Boundary",
        "Compatibility Models",
        "No Industry Defaults",
        "`ui.business.config.contract`",
        "`ViewOrchestrator`",
        "`UiContractV2Handler`",
        "`make verify.app_config_engine.boundary_guard`",
    ):
        _require(errors, token in doc, f"docs/app_config_engine.md missing boundary token: {token}")
    doc_industry_tokens = sorted(_industry_doc_tokens(doc))
    _require(
        errors,
        not doc_industry_tokens,
        "app_config_engine boundary doc must use platform-neutral examples, not industry terms: %s"
        % ", ".join(doc_industry_tokens),
    )

    scratch_docs = sorted(
        path.relative_to(ROOT).as_posix()
        for path in DOCS_DIR.glob("test*.json")
        if path.name.startswith("test")
    )
    _require(
        errors,
        not scratch_docs,
        "app_config_engine docs must not contain scratch test JSON files: %s" % ", ".join(scratch_docs),
    )

    _require(errors, "NO_BUSINESS_FACT_AUTHORITY = True" in controller, "controller must declare no business fact authority")
    _require(errors, "ContractService(request_env=request.env)" in controller, "controller must delegate to ContractService")
    _require(errors, "svc.handle_request()" in controller, "controller must keep request handling in ContractService")

    _require(errors, "NO_BUSINESS_FACT_AUTHORITY = True" in service, "ContractService must declare no business fact authority")
    _require(errors, "apply_contract_governance" in service, "ContractService must keep runtime governance filtering")
    _require(errors, '"runtime_carrier": "app_config_engine.contract_service"' in service, "ContractService source authority carrier missing")

    _require(errors, "NO_BUSINESS_FACT_AUTHORITY = True" in native_parse, "NativeParseService must declare no business fact authority")
    _require(errors, "odoo_native_view_parse_coordinator" in native_parse, "NativeParseService must keep native parse authority")
    _require(errors, "parse_odoo_view" in native_parse, "NativeParseService must use native parser entry")
    _require(errors, "LEGACY_MIXIN_MODULES" in odoo_view_parser, "Odoo view parser must centralize legacy mixin module names")
    _require(errors, "_load_legacy_mixin" in odoo_view_parser, "Odoo view parser must load legacy mixins through an explicit helper")
    _require(errors, "Legacy Filesystem Boundary" in view_parser_doc, "view parser doc must declare the legacy filesystem boundary")
    _require(errors, "services/view_Parser/" in view_parser_doc, "view parser doc must describe the actual filesystem path")
    _require(errors, "不能在解析入口默认 `sudo()`" in view_parser_doc, "view parser doc must forbid default sudo parsing")

    _require(errors, "NO_BUSINESS_FACT_AUTHORITY = True" in page_assembler, "PageAssembler must declare no business fact authority")
    _require(errors, "_inject_view_orchestration_summary" in page_assembler, "PageAssembler must expose view orchestration summary")
    _require(errors, "_current_view_orchestration_config_summary" in page_assembler, "PageAssembler must expose current orchestration config summary")
    _require(errors, "ui.business.config.contract" in page_assembler, "PageAssembler must read orchestration config as external authority")
    _require(errors, "ViewOrchestrator(self.env).compose" in app_view_config, "app.view.config must delegate orchestration to ViewOrchestrator")

    found_refs: set[str] = set()
    sudo_parse_refs: list[str] = []
    for path in APP_ENGINE.rglob("*.py"):
        text = _read(path)
        found_refs.update(_industry_refs(text))
        if "sudo().parse_odoo_view" in text:
            sudo_parse_refs.append(path.relative_to(ROOT).as_posix())
    _require(
        errors,
        not found_refs,
        "app_config_engine has industry module references: %s" % ", ".join(sorted(found_refs)),
    )
    _require(
        errors,
        not sudo_parse_refs,
        "app_config_engine native parser must use request-user environment, not sudo().parse_odoo_view: %s"
        % ", ".join(sorted(sudo_parse_refs)),
    )

    if errors:
        print("[app_config_engine_boundary_guard] FAIL")
        for error in errors:
            print(error)
        return 2
    print("[app_config_engine_boundary_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
