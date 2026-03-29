#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


BACKEND_METADATA_SPECS: dict[str, tuple[str, ...]] = {
    "head.access_policy": ("head", "access_policy"),
    "views.form.layout": ("views", "form", "layout"),
    "views.form.statusbar.field": ("views", "form", "statusbar", "field"),
    "views.form.field_modifiers": ("views", "form", "field_modifiers"),
    "buttons": ("buttons",),
    "permissions.effective.rights": ("permissions", "effective", "rights"),
    "permissions.field_groups": ("permissions", "field_groups"),
    "field_policies": ("field_policies",),
    "field_semantics": ("field_semantics",),
    "visible_fields": ("visible_fields",),
    "workflow": ("workflow",),
    "validator": ("validator",),
}


FRONTEND_CONSUMER_SPECS: dict[str, tuple[str, ...]] = {
    "title_identity": (
        "const pageTitle = computed(() => {",
        "const pageDisplayTitle = computed(() => {",
    ),
    "runtime_permissions": (
        "const sceneContractPermissions = computed<Record<string, unknown>>",
        "const sceneWriteDisabledReason = computed(() => {",
        "const canPersistBySceneRuntime = computed(() => {",
    ),
    "statusbar_strip": (
        "const statusbarFieldName = computed(() =>",
        "const statusbarSteps = computed<StatusbarStep[]>(() => {",
        "page-statusbar-strip",
    ),
    "top_action_strip": (
        "const contractActionStrip = computed(() =>",
        "page-action-strip",
    ),
    "layout_walk": (
        "const layoutNodes = computed<LayoutNode[]>(() => {",
        "function walkLayout(nodeRaw: unknown, parentKey: string) {",
    ),
    "section_mapping": (
        "const layoutSections = computed<LayoutSection[]>(() => {",
        "const templateSections = computed<TemplateSectionView[]>(() =>",
    ),
    "section_shells": (
        "contract-form-shell",
        "resolveSectionShellClass",
        "resolveSectionEyebrow",
    ),
    "readonly_projection": (
        "readonly: Boolean(",
        "|| !canPersistBySceneRuntime.value",
    ),
}


def _descend(value: object, path: tuple[str, ...]) -> object | None:
    current = value
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
        if current is None:
            return None
    return current


def _is_present(value: object | None) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict, tuple, set)):
        return len(value) > 0
    return True


def evaluate_backend(snapshot_path: Path) -> dict[str, object]:
    payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
    contract = payload.get("ui_contract_raw")
    if not isinstance(contract, dict):
      raise ValueError("snapshot does not contain ui_contract_raw object")

    targets: list[dict[str, object]] = []
    for label, path in BACKEND_METADATA_SPECS.items():
        value = _descend(contract, path)
        targets.append({
            "label": label,
            "path": ".".join(path),
            "present": _is_present(value),
        })

    missing = [item for item in targets if not item["present"]]
    return {
        "target_count": len(targets),
        "present_count": len(targets) - len(missing),
        "targets": targets,
        "missing_targets": missing,
    }


def evaluate_frontend(frontend_file: Path) -> dict[str, object]:
    content = frontend_file.read_text(encoding="utf-8")
    targets: list[dict[str, object]] = []
    for label, tokens in FRONTEND_CONSUMER_SPECS.items():
        missing_tokens = [token for token in tokens if token not in content]
        targets.append({
            "label": label,
            "covered": not missing_tokens,
            "missing_tokens": missing_tokens,
        })

    uncovered = [item for item in targets if not item["covered"]]
    return {
        "target_count": len(targets),
        "covered_count": len(targets) - len(uncovered),
        "targets": targets,
        "uncovered_targets": uncovered,
    }


def build_gap_summary(backend: dict[str, object], frontend: dict[str, object]) -> list[str]:
    missing_backend = [str(item["label"]) for item in backend["missing_targets"]]  # type: ignore[index]
    missing_frontend = [str(item["label"]) for item in frontend["uncovered_targets"]]  # type: ignore[index]
    lines: list[str] = []
    if missing_backend:
        lines.append(f"backend_missing={', '.join(missing_backend)}")
    if missing_frontend:
        lines.append(f"frontend_uncovered={', '.join(missing_frontend)}")
    if not lines:
        lines.append("no_gap_detected_for_current_audit_scope")
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit backend metadata completeness and frontend consumption coverage for a contract-driven page.")
    parser.add_argument("--snapshot", required=True, help="Snapshot JSON containing ui_contract_raw.")
    parser.add_argument("--frontend-file", required=True, help="Frontend consumer file to inspect.")
    parser.add_argument("--expect-status", choices=["PASS", "FAIL"], help="Assert expected script status.")
    args = parser.parse_args()

    snapshot_path = Path(args.snapshot).resolve()
    frontend_file = Path(args.frontend_file).resolve()

    backend = evaluate_backend(snapshot_path)
    frontend = evaluate_frontend(frontend_file)
    gap_summary = build_gap_summary(backend, frontend)

    payload = {
        "status": "PASS",
        "snapshot": str(snapshot_path),
        "frontend_file": str(frontend_file),
        "backend": backend,
        "frontend": frontend,
        "parity_status": "READY" if gap_summary == ["no_gap_detected_for_current_audit_scope"] else "GAP",
        "gap_summary": gap_summary,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))

    if args.expect_status and payload["status"] != args.expect_status:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
