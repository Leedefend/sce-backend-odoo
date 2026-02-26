#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ROLE_FLOOR_JSON = ROOT / "artifacts" / "backend" / "role_capability_floor_prod_like.json"
RELEASE_CAP_JSON = ROOT / "artifacts" / "backend" / "release_capability_report.json"

REPORT_JSON = ROOT / "artifacts" / "backend" / "role_capability_diff_report.json"
REPORT_MD = ROOT / "docs" / "ops" / "audit" / "role_capability_diff_report.md"


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _build_archetype_capabilities(payload: dict) -> dict[str, set[str]]:
    rows = (
        ((payload.get("runtime_capability_matrix") or {}).get("rows"))
        if isinstance((payload.get("runtime_capability_matrix") or {}).get("rows"), list)
        else []
    )
    out: dict[str, set[str]] = {"pm": set(), "finance": set(), "executive": set()}
    for row in rows:
        if not isinstance(row, dict):
            continue
        cap = str(row.get("capability_key") or "").strip()
        roles = row.get("roles") if isinstance(row.get("roles"), dict) else {}
        if not cap:
            continue
        for archetype in ("pm", "finance", "executive"):
            state = roles.get(archetype) if isinstance(roles.get(archetype), dict) else {}
            if str(state.get("state") or "").strip().upper() == "READY":
                out.setdefault(archetype, set()).add(cap)
    return out


def _pair_overlap(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    base = len(a | b)
    if base == 0:
        return 1.0
    return round(len(a & b) / base, 4)


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    role_floor = _load_json(ROLE_FLOOR_JSON)
    release = _load_json(RELEASE_CAP_JSON)
    role_rows = role_floor.get("roles") if isinstance(role_floor.get("roles"), list) else []
    role_floor_by_role = {
        str(item.get("role") or "").strip(): item
        for item in role_rows
        if isinstance(item, dict) and str(item.get("role") or "").strip()
    }
    archetype_caps = _build_archetype_capabilities(release)

    if not archetype_caps.get("executive"):
        errors.append("missing archetype capability set: executive")

    profiles = [
        {
            "profile_key": "finance_director",
            "profile_name": "财务主管",
            "mapped_archetype": "finance",
            "source_login": "sc_fx_finance",
            "business_explanation": "负责付款申请、资金台账、经营指标与审批中心。",
        },
        {
            "profile_key": "procurement_manager",
            "profile_name": "采购经理",
            "mapped_archetype": "pm",
            "source_login": "sc_fx_pm",
            "business_explanation": "关注项目执行与采购协同，强调项目台账与任务推进。",
        },
        {
            "profile_key": "owner_representative",
            "profile_name": "业主代表",
            "mapped_archetype": "pm",
            "source_login": "sc_fx_pm",
            "business_explanation": "关注项目状态、里程碑与交付验收链路。",
        },
        {
            "profile_key": "subcontract_lead",
            "profile_name": "分包负责人",
            "mapped_archetype": "material_user",
            "source_login": "sc_fx_material_user",
            "business_explanation": "聚焦物资与执行协同，面向成本与进度联动场景。",
        },
        {
            "profile_key": "risk_officer",
            "profile_name": "风控专员",
            "mapped_archetype": "cost_user",
            "source_login": "sc_fx_cost_user",
            "business_explanation": "关注成本、风险与异常监测，不承担治理级变更动作。",
        },
        {
            "profile_key": "executive_management",
            "profile_name": "高层管理",
            "mapped_archetype": "executive",
            "source_login": "sc_fx_executive",
            "business_explanation": "覆盖经营分析、治理审计与跨域决策能力。",
        },
        {
            "profile_key": "schedule_engineer",
            "profile_name": "计划工程师",
            "mapped_archetype": "pm",
            "source_login": "sc_fx_pm",
            "business_explanation": "聚焦进度编排、任务推进和项目生命周期节奏控制。",
        },
        {
            "profile_key": "quality_supervisor",
            "profile_name": "质量主管",
            "mapped_archetype": "cost_user",
            "source_login": "sc_fx_cost_user",
            "business_explanation": "关注质量风险、过程审计与问题整改闭环。",
        },
    ]

    profile_rows: list[dict] = []
    executive_caps = archetype_caps.get("executive", set())
    sensitive_caps = {"governance.runtime.audit", "governance.scene.openability", "analytics.dashboard.executive"}
    over_authorized_profiles: list[str] = []

    for profile in profiles:
        archetype = profile["mapped_archetype"]
        floor = role_floor_by_role.get(archetype, {})
        if not floor and archetype in {"material_user", "cost_user"}:
            floor = role_floor_by_role.get(archetype, {})
        cap_set = archetype_caps.get(archetype, set())
        if not cap_set and archetype in {"material_user", "cost_user"}:
            # For material/cost profiles, fallback to pm low-privilege archetype capability view.
            cap_set = archetype_caps.get("pm", set())
        if not cap_set:
            errors.append(f"missing capability sample for archetype={archetype}")

        journey = floor.get("journey") if isinstance(floor.get("journey"), list) else []
        system_init_ok = any(
            isinstance(item, dict)
            and str(item.get("intent") or "").strip() == "system.init"
            and bool(item.get("ok"))
            for item in journey
        )
        ui_contract_ok = any(
            isinstance(item, dict)
            and str(item.get("intent") or "").strip() == "ui.contract"
            and bool(item.get("ok"))
            for item in journey
        )

        if not system_init_ok or not ui_contract_ok:
            errors.append(f"{profile['profile_key']}: missing successful system.init/ui.contract evidence")

        non_exec = profile["profile_key"] != "executive_management"
        if non_exec and (cap_set & sensitive_caps):
            over_authorized_profiles.append(profile["profile_key"])

        full_caps_sorted = sorted(cap_set)
        profile_rows.append(
            {
                **profile,
                "system_init_ok": system_init_ok,
                "ui_contract_ok": ui_contract_ok,
                "capability_count": len(cap_set),
                "capability_sample": full_caps_sorted[:12],
                "capability_keys": full_caps_sorted,
                "source_archetype_capability_count": len(cap_set),
                "source_role_record": {
                    "role": str(floor.get("role") or ""),
                    "login": str(floor.get("login") or profile["source_login"]),
                    "ok": bool(floor.get("ok")) if isinstance(floor, dict) else False,
                },
            }
        )

    if over_authorized_profiles:
        errors.append(f"over_authorized_profile_count={len(over_authorized_profiles)}")

    diff_rows = []
    for idx, left in enumerate(profile_rows):
        left_caps = set(left.get("capability_keys") or [])
        left_key = left["profile_key"]
        for right in profile_rows[idx + 1 :]:
            right_caps = set(right.get("capability_keys") or [])
            overlap_ratio = _pair_overlap(left_caps, right_caps)
            diff_rows.append(
                {
                    "left_profile": left_key,
                    "right_profile": right["profile_key"],
                    "overlap_ratio": overlap_ratio,
                    "left_capability_count": len(left_caps),
                    "right_capability_count": len(right_caps),
                }
            )

    source_mtime = max(
        ROLE_FLOOR_JSON.stat().st_mtime if ROLE_FLOOR_JSON.exists() else 0,
        RELEASE_CAP_JSON.stat().st_mtime if RELEASE_CAP_JSON.exists() else 0,
    )
    generated_at = datetime.fromtimestamp(source_mtime).isoformat(timespec="seconds") if source_mtime else "unknown"
    payload = {
        "ok": len(errors) == 0,
        "generated_at": generated_at,
        "source": {
            "role_floor_report": ROLE_FLOOR_JSON.relative_to(ROOT).as_posix(),
            "release_capability_report": RELEASE_CAP_JSON.relative_to(ROOT).as_posix(),
            "evidence_mode": "artifact_reuse",
        },
        "summary": {
            "profile_count": len(profile_rows),
            "role_sample_count": len(profile_rows),
            "system_init_ok_count": sum(1 for x in profile_rows if x["system_init_ok"]),
            "ui_contract_ok_count": sum(1 for x in profile_rows if x["ui_contract_ok"]),
            "over_authorized_profile_count": len(over_authorized_profiles),
            "error_count": len(errors),
            "warning_count": len(warnings),
        },
        "profiles": profile_rows,
        "role_diff_matrix": diff_rows,
        "over_authorized_profiles": over_authorized_profiles,
        "errors": errors,
        "warnings": warnings,
    }

    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Role Capability Diff Report",
        "",
        f"- generated_at: {generated_at}",
        "- evidence_mode: artifact_reuse (system.init/ui.contract verified from prod_like audit artifact)",
        f"- profile_count: {len(profile_rows)}",
        f"- system_init_ok_count: {sum(1 for x in profile_rows if x['system_init_ok'])}",
        f"- ui_contract_ok_count: {sum(1 for x in profile_rows if x['ui_contract_ok'])}",
        f"- over_authorized_profile_count: {len(over_authorized_profiles)}",
        f"- error_count: {len(errors)}",
        "",
        "## Profiles",
        "",
        "| profile | source_login | mapped_archetype | capability_count | system.init | ui.contract | business_explanation |",
        "|---|---|---|---:|---|---|---|",
    ]
    for row in profile_rows:
        lines.append(
            f"| {row['profile_name']} | {row['source_login']} | {row['mapped_archetype']} | "
            f"{row['capability_count']} | {'PASS' if row['system_init_ok'] else 'FAIL'} | "
            f"{'PASS' if row['ui_contract_ok'] else 'FAIL'} | {row['business_explanation']} |"
        )
    lines.extend(["", "## Over Authorization", ""])
    if over_authorized_profiles:
        for key in over_authorized_profiles:
            lines.append(f"- {key}")
    else:
        lines.append("- none")

    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(REPORT_MD))
    print(str(REPORT_JSON))
    if errors:
        print("[role_capability_diff_report] FAIL")
        return 2
    print("[role_capability_diff_report] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
