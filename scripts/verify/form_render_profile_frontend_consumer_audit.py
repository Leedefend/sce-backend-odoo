#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "contract" / "form_render_profile_frontend_consumer_v1.json"


TARGET_FILES = [
    Path("frontend/apps/web/src/pages/ContractFormPage.vue"),
    Path("frontend/apps/web/src/app/pageContract.ts"),
    Path("frontend/apps/web/src/app/runtime/detailLayoutRuntime.ts"),
    Path("frontend/apps/web/src/app/pageContractActionRuntime.ts"),
]


def _read(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def run_audit() -> dict:
    rows = []
    total_profile_refs = 0
    readonly_behavior_refs = 0

    readonly_tokens = [
        "readonly",
        "isReadonly",
        "readOnly",
        "disable",
        "canEdit",
        "render_profile",
        "renderProfile",
    ]

    for rel in TARGET_FILES:
        full = ROOT / rel
        text = _read(full)
        profile_refs = text.count("render_profile") + text.count("renderProfile")
        readonly_refs = sum(text.count(token) for token in readonly_tokens)
        total_profile_refs += profile_refs
        readonly_behavior_refs += readonly_refs
        rows.append(
            {
                "file": str(rel),
                "exists": full.exists(),
                "render_profile_refs": profile_refs,
                "readonly_behavior_refs": readonly_refs,
            }
        )

    files_with_profile = [r for r in rows if r["render_profile_refs"] > 0]

    contract_form_text = _read(ROOT / Path("frontend/apps/web/src/pages/ContractFormPage.vue"))
    detail_shell_text = _read(ROOT / Path("frontend/apps/web/src/components/template/DetailShellLayout.vue"))

    consumes_node_title = "node.title || node.string || node.label" in contract_form_text
    generic_hide_overbroad = "'主体信息'" in detail_shell_text or "'项目信息'" in detail_shell_text
    consumes_form_surface_header = "formView.header_buttons" in contract_form_text
    consumes_form_surface_button_box = "formView.button_box" in contract_form_text
    consumes_form_surface_stat = "formView.stat_buttons" in contract_form_text
    has_form_surface_merge = "merged.push(...formViewSurfaceActions.value)" in contract_form_text
    has_project_field_label_override = "name: '项目名称'" in contract_form_text
    has_workbreakdown_field_label_override = "project_id: '所属项目'" in contract_form_text
    has_hardcoded_page_title_pack = "const pageTitles = ['基本信息', '结构关系', '执行映射']" in contract_form_text
    has_hardcoded_group_title_pack = "const groupTitles = ['结构定位', '节点信息', '扩展信息']" in contract_form_text
    has_tab_priority_sorting = "const tabPriority = (labelRaw: string) =>" in contract_form_text
    has_tab_priority_sort_call = ".sort((a, b) => tabPriority(a.label) - tabPriority(b.label)" in contract_form_text
    has_project_action_priority = "const projectActionPriority = (action: ContractAction) =>" in contract_form_text
    has_contract_action_top3_slice = ".slice(0, 3);" in contract_form_text

    detail_runtime_text = _read(ROOT / Path("frontend/apps/web/src/app/runtime/detailLayoutRuntime.ts"))
    has_tab_label_dedup_suffix = "（${sameCount + 1}）" in detail_runtime_text
    has_container_title_override_blank = "titleOverride: container.kind === 'page' || container.kind === 'sheet' || container.kind === 'header' ? '' : undefined" in detail_runtime_text

    detail_shell_text = _read(ROOT / Path("frontend/apps/web/src/components/template/DetailShellLayout.vue"))
    hides_generic_group_title_in_tab = "if (title === '信息分组') return ''" in detail_shell_text or "if (title === '分组') return ''" in detail_shell_text
    hides_generic_group_title_in_normalize = "const generic = new Set(['信息分组', '分组']);" in detail_shell_text
    has_native_body_class_binding = "'contract-detail-shell__body--native': nativeLike" in detail_shell_text
    has_native_body_single_column = ".contract-detail-shell__body--native" in detail_shell_text and "grid-template-columns: 1fr;" in detail_shell_text
    has_native_density_grid = ".contract-form-shell--native :deep(.template-form-section-grid)" in detail_shell_text
    has_native_density_input = ".contract-form-shell--native :deep(.input)" in detail_shell_text and "height: 36px;" in detail_shell_text
    has_native_tab_underline_mode = ".contract-detail-tabs--native .contract-detail-tabs__tab" in detail_shell_text and "border-bottom: 2px solid transparent;" in detail_shell_text
    has_native_tab_dark_fill = ".contract-detail-tabs--native .contract-detail-tabs__tab--active" in detail_shell_text and "background: #111827;" in detail_shell_text

    command_bar_text = _read(ROOT / Path("frontend/apps/web/src/components/template/DetailCommandBar.vue"))
    has_command_bar_gradient = "background: linear-gradient(180deg" in command_bar_text
    has_statusbar_round_pill = "border-radius: 999px;" in command_bar_text

    status = "PASS" if (
        len(files_with_profile) >= 2
        and readonly_behavior_refs > 0
        and consumes_node_title
        and not generic_hide_overbroad
        and consumes_form_surface_header
        and consumes_form_surface_button_box
        and consumes_form_surface_stat
        and has_form_surface_merge
        and not has_project_field_label_override
        and not has_workbreakdown_field_label_override
        and not has_hardcoded_page_title_pack
        and not has_hardcoded_group_title_pack
        and not has_tab_priority_sorting
        and not has_tab_priority_sort_call
        and not has_project_action_priority
        and not has_contract_action_top3_slice
        and not has_tab_label_dedup_suffix
        and not has_container_title_override_blank
        and not hides_generic_group_title_in_tab
        and not hides_generic_group_title_in_normalize
        and has_native_body_class_binding
        and has_native_body_single_column
        and has_native_density_grid
        and has_native_density_input
        and has_native_tab_underline_mode
        and not has_native_tab_dark_fill
        and not has_command_bar_gradient
        and not has_statusbar_round_pill
    ) else "BLOCKED"

    payload = {
        "version": "v1",
        "audit": "form_render_profile_frontend_consumer",
        "summary": {
            "status": status,
            "files_scanned": len(rows),
            "files_with_render_profile": len(files_with_profile),
            "total_render_profile_refs": total_profile_refs,
            "readonly_behavior_refs": readonly_behavior_refs,
            "consumes_node_title": consumes_node_title,
            "generic_hide_overbroad": generic_hide_overbroad,
            "consumes_form_surface_header": consumes_form_surface_header,
            "consumes_form_surface_button_box": consumes_form_surface_button_box,
            "consumes_form_surface_stat": consumes_form_surface_stat,
            "has_form_surface_merge": has_form_surface_merge,
            "has_project_field_label_override": has_project_field_label_override,
            "has_workbreakdown_field_label_override": has_workbreakdown_field_label_override,
            "has_hardcoded_page_title_pack": has_hardcoded_page_title_pack,
            "has_hardcoded_group_title_pack": has_hardcoded_group_title_pack,
            "has_tab_priority_sorting": has_tab_priority_sorting,
            "has_tab_priority_sort_call": has_tab_priority_sort_call,
            "has_project_action_priority": has_project_action_priority,
            "has_contract_action_top3_slice": has_contract_action_top3_slice,
            "has_tab_label_dedup_suffix": has_tab_label_dedup_suffix,
            "has_container_title_override_blank": has_container_title_override_blank,
            "hides_generic_group_title_in_tab": hides_generic_group_title_in_tab,
            "hides_generic_group_title_in_normalize": hides_generic_group_title_in_normalize,
            "has_native_body_class_binding": has_native_body_class_binding,
            "has_native_body_single_column": has_native_body_single_column,
            "has_native_density_grid": has_native_density_grid,
            "has_native_density_input": has_native_density_input,
            "has_native_tab_underline_mode": has_native_tab_underline_mode,
            "has_native_tab_dark_fill": has_native_tab_dark_fill,
            "has_command_bar_gradient": has_command_bar_gradient,
            "has_statusbar_round_pill": has_statusbar_round_pill,
        },
        "rows": rows,
        "missing_consumers": [r for r in rows if r["exists"] and r["render_profile_refs"] <= 0],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit frontend render_profile consumer coverage.")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    payload = run_audit()
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        summary = payload.get("summary") or {}
        print(
            "status={status} files_with_render_profile={files} readonly_refs={readonly}".format(
                status=summary.get("status"),
                files=summary.get("files_with_render_profile"),
                readonly=summary.get("readonly_behavior_refs"),
            )
        )
    if args.strict and (payload.get("summary") or {}).get("status") != "PASS":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
