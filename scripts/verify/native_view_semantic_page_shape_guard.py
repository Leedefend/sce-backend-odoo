#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

ALLOWED_ZONES = {
    "header_zone",
    "summary_zone",
    "detail_zone",
    "relation_zone",
    "action_zone",
    "collaboration_zone",
    "insight_zone",
    "attachment_zone",
}

ALLOWED_BLOCKS = {
    "title_block",
    "status_block",
    "action_bar_block",
    "field_group_block",
    "notebook_block",
    "relation_table_block",
    "relation_card_block",
    "stat_button_block",
    "chatter_block",
    "attachment_block",
    "timeline_block",
    "risk_alert_block",
    "ai_recommendation_block",
    "next_action_block",
}


def validate_file(path: Path) -> list[str]:
    errs: list[str] = []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"{path}: invalid json ({exc})"]

    sp = payload.get("semantic_page") if isinstance(payload, dict) else None
    if not isinstance(sp, dict):
        return [f"{path}: missing semantic_page object"]

    for key in ("model", "view_type", "layout", "zones"):
        if key not in sp:
            errs.append(f"{path}: semantic_page missing required key '{key}'")

    view_type = str(sp.get("view_type") or "")
    zones = sp.get("zones")
    if not isinstance(zones, list):
        errs.append(f"{path}: semantic_page.zones must be array")
        return errs

    for i, zone in enumerate(zones):
        if not isinstance(zone, dict):
            errs.append(f"{path}: zones[{i}] must be object")
            continue
        key = zone.get("key")
        if key not in ALLOWED_ZONES:
            errs.append(f"{path}: zones[{i}].key='{key}' not allowed")
        blocks = zone.get("blocks")
        if not isinstance(blocks, list):
            errs.append(f"{path}: zones[{i}].blocks must be array")
            continue
        for j, block in enumerate(blocks):
            if not isinstance(block, dict):
                errs.append(f"{path}: zones[{i}].blocks[{j}] must be object")
                continue
            btype = block.get("type")
            if btype not in ALLOWED_BLOCKS:
                errs.append(f"{path}: zones[{i}].blocks[{j}].type='{btype}' not allowed")

    actions = sp.get("actions")
    if actions is not None:
        if not isinstance(actions, dict):
            errs.append(f"{path}: semantic_page.actions must be object")
        else:
            for action_group in ("header_actions", "record_actions", "toolbar_actions"):
                action_items = actions.get(action_group)
                if action_items is None:
                    continue
                if not isinstance(action_items, list):
                    errs.append(f"{path}: semantic_page.actions.{action_group} must be array")
                    continue
                for index, action in enumerate(action_items):
                    if not isinstance(action, dict):
                        errs.append(f"{path}: semantic_page.actions.{action_group}[{index}] must be object")
                        continue
                    for key in ("key", "label", "enabled", "reason_code"):
                        if key not in action:
                            errs.append(f"{path}: semantic_page.actions.{action_group}[{index}] missing '{key}'")

    verdicts = sp.get("permission_verdicts")
    if verdicts is not None:
        if not isinstance(verdicts, dict):
            errs.append(f"{path}: semantic_page.permission_verdicts must be object")
        else:
            for perm_key in ("read", "create", "write", "unlink", "execute"):
                verdict = verdicts.get(perm_key)
                if verdict is None:
                    errs.append(f"{path}: semantic_page.permission_verdicts missing '{perm_key}'")
                    continue
                if not isinstance(verdict, dict):
                    errs.append(f"{path}: semantic_page.permission_verdicts.{perm_key} must be object")
                    continue
                for key in ("allowed", "reason_code"):
                    if key not in verdict:
                        errs.append(f"{path}: semantic_page.permission_verdicts.{perm_key} missing '{key}'")

    action_gating = sp.get("action_gating")
    if action_gating is not None:
        if not isinstance(action_gating, dict):
            errs.append(f"{path}: semantic_page.action_gating must be object")
        else:
            for key in ("record_state", "policy", "verdict"):
                if key not in action_gating:
                    errs.append(f"{path}: semantic_page.action_gating missing '{key}'")
            record_state = action_gating.get("record_state")
            if isinstance(record_state, dict):
                for key in ("field", "value", "source"):
                    if key not in record_state:
                        errs.append(f"{path}: semantic_page.action_gating.record_state missing '{key}'")
            policy = action_gating.get("policy")
            if isinstance(policy, dict):
                if "closed_states" not in policy or not isinstance(policy.get("closed_states"), list):
                    errs.append(f"{path}: semantic_page.action_gating.policy.closed_states must be array")
            verdict = action_gating.get("verdict")
            if isinstance(verdict, dict):
                if "is_closed_state" not in verdict or not isinstance(verdict.get("is_closed_state"), bool):
                    errs.append(f"{path}: semantic_page.action_gating.verdict.is_closed_state must be bool")
                if "reason_code" not in verdict:
                    errs.append(f"{path}: semantic_page.action_gating.verdict.reason_code missing")

    search_semantics = sp.get("search_semantics")
    if view_type == "search":
        if not isinstance(search_semantics, dict):
            errs.append(f"{path}: search view must include semantic_page.search_semantics object")
        else:
            for key in ("filters", "group_by", "search_fields", "search_panel", "favorites", "quick_filters"):
                if key not in search_semantics:
                    errs.append(f"{path}: semantic_page.search_semantics missing '{key}'")

            for key in ("filters", "group_by", "search_fields", "quick_filters"):
                items = search_semantics.get(key)
                if not isinstance(items, list):
                    errs.append(f"{path}: semantic_page.search_semantics.{key} must be array")
                    continue
                if key == "quick_filters" and len(items) > 4:
                    errs.append(f"{path}: semantic_page.search_semantics.quick_filters must be <= 4")
                for index, item in enumerate(items):
                    if not isinstance(item, dict):
                        errs.append(f"{path}: semantic_page.search_semantics.{key}[{index}] must be object")
                        continue
                    for required in ("key", "label"):
                        if required not in item:
                            errs.append(f"{path}: semantic_page.search_semantics.{key}[{index}] missing '{required}'")

            panel = search_semantics.get("search_panel")
            if not isinstance(panel, dict):
                errs.append(f"{path}: semantic_page.search_semantics.search_panel must be object")
            else:
                if "enabled" not in panel or not isinstance(panel.get("enabled"), bool):
                    errs.append(f"{path}: semantic_page.search_semantics.search_panel.enabled must be bool")
                if "sections" not in panel or not isinstance(panel.get("sections"), list):
                    errs.append(f"{path}: semantic_page.search_semantics.search_panel.sections must be array")

            favorites = search_semantics.get("favorites")
            if not isinstance(favorites, dict):
                errs.append(f"{path}: semantic_page.search_semantics.favorites must be object")
            else:
                if "enabled" not in favorites or not isinstance(favorites.get("enabled"), bool):
                    errs.append(f"{path}: semantic_page.search_semantics.favorites.enabled must be bool")
                items = favorites.get("items")
                if not isinstance(items, list):
                    errs.append(f"{path}: semantic_page.search_semantics.favorites.items must be array")
                else:
                    for index, item in enumerate(items):
                        if not isinstance(item, dict):
                            errs.append(f"{path}: semantic_page.search_semantics.favorites.items[{index}] must be object")
                            continue
                        for required in ("key", "label"):
                            if required not in item:
                                errs.append(f"{path}: semantic_page.search_semantics.favorites.items[{index}] missing '{required}'")

    kanban_semantics = sp.get("kanban_semantics")
    if view_type == "kanban":
        if not isinstance(kanban_semantics, dict):
            errs.append(f"{path}: kanban view must include semantic_page.kanban_semantics object")
        else:
            for key in ("title_field", "card_fields", "metric_fields"):
                if key not in kanban_semantics:
                    errs.append(f"{path}: semantic_page.kanban_semantics missing '{key}'")
            if not isinstance(kanban_semantics.get("title_field"), str):
                errs.append(f"{path}: semantic_page.kanban_semantics.title_field must be string")
            if not isinstance(kanban_semantics.get("card_fields"), list):
                errs.append(f"{path}: semantic_page.kanban_semantics.card_fields must be array")
            if not isinstance(kanban_semantics.get("metric_fields"), list):
                errs.append(f"{path}: semantic_page.kanban_semantics.metric_fields must be array")

    return errs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default="docs/contract/snapshots/native_view", help="snapshot directory")
    parser.add_argument("--output", default="", help="optional json report output path")
    args = parser.parse_args()

    root = Path(args.dir)
    files = sorted(root.glob("*.json"))
    report = {
        "ok": False,
        "check": "verify.native_view.semantic_page.shape",
        "snapshot_dir": str(root),
        "snapshot_count": 0,
        "error_count": 0,
        "errors": [],
    }

    if not files:
        message = f"no json files in {root}"
        report["errors"] = [message]
        report["error_count"] = 1
        print(f"[verify.native_view.semantic_page.shape] FAIL: {message}")
        if args.output:
            output = Path(args.output)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return 2

    report["snapshot_count"] = len(files)

    all_errs: list[str] = []
    for file in files:
        all_errs.extend(validate_file(file))

    if all_errs:
        print("[verify.native_view.semantic_page.shape] FAIL")
        for err in all_errs:
            print(f" - {err}")
        report["errors"] = all_errs
        report["error_count"] = len(all_errs)
        if args.output:
            output = Path(args.output)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return 2

    print(f"[verify.native_view.semantic_page.shape] PASS ({len(files)} files)")
    report["ok"] = True
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
