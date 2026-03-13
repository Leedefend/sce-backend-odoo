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

    return errs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default="docs/contract/snapshots/native_view", help="snapshot directory")
    args = parser.parse_args()

    root = Path(args.dir)
    files = sorted(root.glob("*.json"))
    if not files:
        print(f"[verify.native_view.semantic_page.shape] FAIL: no json files in {root}")
        return 2

    all_errs: list[str] = []
    for file in files:
        all_errs.extend(validate_file(file))

    if all_errs:
        print("[verify.native_view.semantic_page.shape] FAIL")
        for err in all_errs:
            print(f" - {err}")
        return 2

    print(f"[verify.native_view.semantic_page.shape] PASS ({len(files)} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
