#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
mkdir -p "${ROOT}/artifacts/backend"

python3 - <<'PY'
import json
from pathlib import Path

root = Path.cwd()
state_service = (root / "addons" / "smart_construction_core" / "services" / "project_state_explain_service.py").read_text(encoding="utf-8")
metrics_service = (root / "addons" / "smart_construction_core" / "services" / "project_metrics_explain_service.py").read_text(encoding="utf-8")
risk_service = (root / "addons" / "smart_construction_core" / "services" / "project_risk_alert_service.py").read_text(encoding="utf-8")
handler = (root / "addons" / "smart_construction_core" / "handlers" / "project_dashboard_enter.py").read_text(encoding="utf-8")
next_actions = (root / "addons" / "smart_construction_core" / "services" / "project_dashboard_builders" / "project_next_actions_builder.py").read_text(encoding="utf-8")
risk_builder = (root / "addons" / "smart_construction_core" / "services" / "project_dashboard_builders" / "project_risk_builder.py").read_text(encoding="utf-8")
dashboard_service = (root / "addons" / "smart_construction_core" / "services" / "project_dashboard_service.py").read_text(encoding="utf-8")
view = (root / "frontend" / "apps" / "web" / "src" / "views" / "ProjectManagementDashboardView.vue").read_text(encoding="utf-8")

checks = {
    "state_explain_service": all(fragment in state_service for fragment in [
        '"stage_label"',
        '"stage_explain"',
        '"status_explain"',
    ]),
    "metrics_explain_service": all(fragment in metrics_service for fragment in [
        '"key": "progress"',
        '"key": "cost"',
        '"key": "payment"',
    ]),
    "risk_alert_service": all(fragment in risk_service for fragment in [
        '"recommended_action"',
        '"impact"',
        '"EXECUTION_COST_MISSING"',
        '"affects_action"',
    ]),
    "risk_builder_integrates_decision": all(fragment in risk_builder for fragment in [
        "ProjectRiskAlertService",
        '"source": "decision_layer_v1"',
    ]),
    "dashboard_handler_contract": 'data["metrics_explain"] = orchestrator._service.build_metrics_explain(project)' in handler,
    "dashboard_flow_completion_contract": all(fragment in handler for fragment in [
        'data["flow_map"] = orchestrator._service.build_flow_map(project)',
        'data["completion"] = orchestrator._service.build_completion(project)',
    ]) and all(fragment in dashboard_service for fragment in [
        "def build_flow_map(self, project):",
        "def build_completion(self, project):",
    ]),
    "next_action_single_recommended": all(fragment in next_actions for fragment in [
        'actions = [row for row in actions if str(row.get("state") or "") == "available"]',
        'row["recommended"] = bool(is_primary)',
        'row["decision_source"] = decision_source',
        '"decision_rule": decision_rule',
        'advances_to_stage="settlement"',
    ]),
    "frontend_consumes_metrics": all(fragment in view for fragment in [
        "metricsExplainMap",
        "metricsExplainMap.value.progress?.explain",
        "metricsExplainMap.value.cost?.explain",
        "metricsExplainMap.value.payment?.explain",
    ]),
    "frontend_consumes_state_reasoning": all(fragment in view for fragment in [
        "stateExplain.stageExplain",
        "stateExplain.milestoneExplain",
        "stateExplain.statusExplain",
    ]),
    "frontend_consumes_flow_visibility": all(fragment in view for fragment in [
        "flowMapItems",
        "completion.percent",
        "action.advancesToStage",
        "flow-map-card",
    ]),
}

failed = [name for name, ok in checks.items() if not ok]
artifact = {
    "guard": "project_dashboard_decision_guard",
    "passed": not failed,
    "checks": checks,
    "failed_checks": failed,
}

artifacts = root / "artifacts" / "backend"
artifacts.mkdir(parents=True, exist_ok=True)
(artifacts / "project_dashboard_decision_guard.json").write_text(
    json.dumps(artifact, ensure_ascii=False, indent=2),
    encoding="utf-8",
)
(artifacts / "project_dashboard_decision_guard.md").write_text(
    "# project_dashboard_decision_guard\n\n"
    + ("PASS\n" if not failed else "FAIL\n")
    + "\n".join(f"- {name}: {'PASS' if ok else 'FAIL'}" for name, ok in checks.items())
    + "\n",
    encoding="utf-8",
)

if failed:
    raise SystemExit("decision guard failed: " + ", ".join(failed))

print("[verify.product.project_dashboard_decision] PASS")
PY
