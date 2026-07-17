#!/usr/bin/env python3
"""Guard the LC-PRO-01 workbench product and safe-open contract."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SURFACE_ROOT = ROOT / "frontend/apps/web/src/views/businessConfigSurface"
ROOT_VIEW = ROOT / "frontend/apps/web/src/views/BusinessConfigSurfaceView.vue"
FILES = [ROOT_VIEW, *sorted(SURFACE_ROOT.glob("*.vue")), *sorted(SURFACE_ROOT.glob("*.ts"))]
FORBIDDEN_DEFAULT_LANGUAGE = ("保存并预览", "预览页面")
REQUIRED_TOKENS = (
    "openCurrentEffectivePage",
    "inspectListSearchDraft",
    "inspectAnalysisDraft",
    "当前版本不支持未发布效果预览",
    "BusinessConfigContextBar",
    "BusinessConfigImpactDialog",
    "ScButton",
    "ScStatusBadge",
)
LAST_AST_REPORT: dict = {}


def validate(sources: dict[Path, str]) -> list[str]:
    global LAST_AST_REPORT
    errors: list[str] = []
    combined = "\n".join(sources.values())
    for phrase in FORBIDDEN_DEFAULT_LANGUAGE:
        if phrase in combined:
            errors.append(f"default workbench still exposes unsafe preview wording: {phrase}")
    for token in REQUIRED_TOKENS:
        if token not in combined:
            errors.append(f"workbench product contract missing token: {token}")
    ast_guard = subprocess.run(
        ["node", str(ROOT / "scripts/verify/low_code_publish_boundary_guard.mjs")],
        cwd=ROOT, text=True, capture_output=True, check=False,
    )
    ast_report = json.loads((ast_guard.stdout or "{}").splitlines()[-1])
    LAST_AST_REPORT = ast_report
    errors.extend(str(item) for item in (ast_report.get("errors") or []))
    if ast_guard.returncode:
        errors.append("AST publish boundary guard failed")
    sc_usage = len(re.findall(r"<Sc[A-Z][A-Za-z0-9]*\b", combined))
    if sc_usage < 20:
        errors.append(f"design-system usage regressed below LC-PRO-01 floor: {sc_usage} < 20")
    if ROOT_VIEW in sources and len(sources[ROOT_VIEW].splitlines()) > 600:
        errors.append("BusinessConfigSurfaceView.vue exceeds route assembly limit (600 lines)")
    return errors


def main() -> int:
    sources = {path: path.read_text(encoding="utf-8") for path in FILES if path.is_file()}
    errors = validate(sources)
    negative_sources = dict(sources)
    negative_sources[ROOT_VIEW] = negative_sources.get(ROOT_VIEW, "") + "\n保存并预览\n"
    negative_self_test = bool(validate(negative_sources))
    if not negative_self_test:
        errors.append("negative self-test accepted deliberately unsafe preview wording")
    combined = "\n".join(sources.values())
    report = {
        "guard": "low_code_workbench_product_guard",
        "scanned_files": len(sources),
        "component_files": sum(path.suffix == ".vue" for path in sources),
        "design_system_usages": len(re.findall(r"<Sc[A-Z][A-Za-z0-9]*\b", combined)),
        "raw_controls": len(re.findall(r"<(?:button|input|select|textarea)\b", combined)),
        "assertions": len(FORBIDDEN_DEFAULT_LANGUAGE) + len(REQUIRED_TOKENS) + 3,
        "negative_self_test": "pass" if negative_self_test else "fail",
        "publish_boundary": LAST_AST_REPORT,
        "errors": errors,
    }
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    print(f"[low_code_workbench_product_guard] {'FAIL' if errors else 'PASS'}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
