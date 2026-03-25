#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${ROOT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
export ROOT_DIR

source "$ROOT_DIR/scripts/common/env.sh"
source "$ROOT_DIR/scripts/common/guard_prod.sh"
source "$ROOT_DIR/scripts/_lib/common.sh"

guard_prod_forbid

: "${DB_NAME:?DB_NAME required}"

mkdir -p "$ROOT_DIR/artifacts/backend"

python3 - <<'PY'
import json
from pathlib import Path

ROOT = Path.cwd()
report = {
    "status": "PASS",
    "frontend": {},
    "backend": {},
}

def ensure_contains(path_str: str, needle: str, key: str) -> None:
    text = (ROOT / path_str).read_text(encoding="utf-8")
    if needle not in text:
        raise RuntimeError(f"{path_str} missing `{needle}`")
    report["frontend" if path_str.startswith("frontend/") else "backend"][key] = "ok"

try:
    ensure_contains(
        "frontend/apps/web/src/views/LoginView.vue",
        "resolvePrimaryEntryPath('/my-work')",
        "login_primary_entry",
    )
    ensure_contains(
        "frontend/apps/web/src/views/HomeView.vue",
        "resolvePrimaryEntryPath('/my-work')",
        "home_primary_entry",
    )
    ensure_contains(
        "frontend/apps/web/src/views/ProjectManagementDashboardView.vue",
        "state-explain-card",
        "dashboard_state_explain",
    )
    ensure_contains(
        "frontend/apps/web/src/views/ProjectManagementDashboardView.vue",
        "recommended-badge",
        "dashboard_recommended_action",
    )
    ensure_contains(
        "addons/smart_construction_core/core_extension.py",
        "project.entry.context.resolve",
        "entry_context_intent_registered",
    )
    ensure_contains(
        "addons/smart_construction_core/services/project_entry_context_service.py",
        '"/my-work"',
        "workspace_fallback_defined",
    )
except Exception as exc:
    report["status"] = "FAIL"
    report["error"] = str(exc)

out_json = ROOT / "artifacts/backend/main_entry_convergence_guard.json"
out_md = ROOT / "artifacts/backend/main_entry_convergence_guard.md"
out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
out_md.write_text(
    "# Main Entry Convergence Guard\n\n"
    f"- status: `{report['status']}`\n"
    + (f"- error: `{report['error']}`\n" if report.get("error") else ""),
    encoding="utf-8",
)
if report["status"] != "PASS":
    raise SystemExit(1)
PY
