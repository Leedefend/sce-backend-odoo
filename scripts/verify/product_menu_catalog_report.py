#!/usr/bin/env python3
"""Render the runtime product menu catalog into a human-readable product document."""

from __future__ import annotations

import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / os.getenv("PRODUCT_MENU_CATALOG_RUNTIME_JSON", "artifacts/product/product_menu_catalog_runtime_v1.json")
OUTPUT = ROOT / os.getenv("PRODUCT_MENU_CATALOG_REPORT_MD", "docs/product/product_menu_catalog_v1.md")


def _text(value: object) -> str:
    return str(value or "").strip()


def _escape(value: object) -> str:
    return _text(value).replace("|", "\\|")


def _depth(path: str) -> int:
    return max(0, len([part for part in _text(path).split(" / ") if part]) - 1)


def _action_label(row: dict) -> str:
    scene_key = _text(row.get("scene_key"))
    if scene_key:
        return f"scene:{scene_key}"
    meta = row.get("action_meta") if isinstance(row.get("action_meta"), dict) else {}
    model = _text(meta.get("res_model"))
    if model:
        return model
    if _text(row.get("action_model")):
        return _text(row.get("action_model"))
    return ""


def _render_tree(rows: list[dict]) -> list[str]:
    lines = []
    for row in rows:
        indent = "  " * _depth(_text(row.get("path")))
        label = _text(row.get("name"))
        action = _action_label(row)
        suffix = f" -> `{action}`" if action else ""
        inactive = " inactive" if not row.get("active", True) else ""
        review = " review" if row.get("needs_review") else ""
        lines.append(f"{indent}- {label} [`{row.get('layer')}`{inactive}{review}]{suffix}")
    return lines


def _rows_by_layer(rows: list[dict], layer: str) -> list[dict]:
    return [row for row in rows if row.get("layer") == layer]


def _top_business_rows(payload: dict) -> list[dict]:
    out = []
    for row in payload.get("top_level") or []:
        path = _text(row.get("path"))
        if row.get("layer") == "formal_product" and " / " in path:
            out.append(row)
    return out


def main() -> int:
    if not INPUT.is_file():
        raise SystemExit(f"missing runtime product menu catalog: {INPUT}")
    payload = json.loads(INPUT.read_text(encoding="utf-8"))
    rows = payload.get("menus") if isinstance(payload.get("menus"), list) else []
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    layer_counts = summary.get("layer_counts") if isinstance(summary.get("layer_counts"), dict) else {}
    definitions = payload.get("layer_definitions") if isinstance(payload.get("layer_definitions"), dict) else {}
    review_rows = [row for row in rows if row.get("needs_review")]

    lines = [
        "# 产品菜单台账 V1",
        "",
        "本台账由运行时 Odoo 菜单事实生成，只读取 `ir.ui.menu`、动作、权限组和 XMLID，不从用户确认历史数据反推产品菜单。",
        "",
        "## 运行时来源",
        "",
        f"- database: `{_escape(payload.get('db'))}`",
        f"- generated_at: `{_escape(payload.get('generated_at'))}`",
        f"- roots: `{_escape(', '.join(payload.get('root_xmlids') or []))}`",
        f"- visible_login_probe: `{_escape(', '.join(payload.get('visible_logins_checked') or []))}`",
        "",
        "## 总览",
        "",
        f"- menu_count: `{summary.get('menu_count', 0)}`",
        f"- active_menu_count: `{summary.get('active_menu_count', 0)}`",
        f"- inactive_menu_count: `{summary.get('inactive_menu_count', 0)}`",
        f"- action_menu_count: `{summary.get('action_menu_count', 0)}`",
        f"- needs_review_count: `{summary.get('needs_review_count', 0)}`",
        f"- internal_history_business_visible_count: `{summary.get('internal_history_business_visible_count', 0)}`",
        f"- ordinary_business_system_config_visible_count: `{summary.get('ordinary_business_system_config_visible_count', 0)}`",
        f"- business_config_legacy_count: `{summary.get('business_config_legacy_count', 0)}`",
        f"- business_config_legacy_active_count: `{summary.get('business_config_legacy_active_count', 0)}`",
        f"- runtime_user_menu_without_xmlid_count: `{summary.get('runtime_user_menu_without_xmlid_count', 0)}`",
        f"- formal_center_inactive_history_count: `{summary.get('formal_center_inactive_history_count', 0)}`",
        "",
        "## 分层定义",
        "",
    ]
    for layer in ["formal_product", "system_config", "user_config", "history_acceptance", "dev_governance"]:
        lines.append(f"- `{layer}`: {_text(definitions.get(layer))}")
    lines.extend(["", "## 分层统计", "", "| Layer | Count |", "| --- | ---: |"])
    for layer in ["formal_product", "system_config", "user_config", "history_acceptance", "dev_governance"]:
        lines.append(f"| `{layer}` | {int(layer_counts.get(layer, 0))} |")

    lines.extend(["", "## 正式产品入口概览", ""])
    business_rows = _top_business_rows(payload)
    if business_rows:
        lines.extend(["| 入口 | XMLID | 可见性探针用户 |", "| --- | --- | --- |"])
        for row in business_rows:
            visible = ", ".join(row.get("visible_logins") or [])
            lines.append(f"| {_escape(row.get('path'))} | `{_escape(row.get('xmlid'))}` | {_escape(visible)} |")
    else:
        lines.append("未检测到正式产品顶层业务入口。")

    lines.extend(["", "## 顶层菜单", "", "| Menu | Layer | Visible Probe Logins | XMLID |", "| --- | --- | --- | --- |"])
    for row in payload.get("top_level") or []:
        visible = ", ".join(row.get("visible_logins") or [])
        lines.append(
            f"| {_escape(row.get('path'))} | `{_escape(row.get('layer'))}` | {_escape(visible)} | `{_escape(row.get('xmlid'))}` |"
        )

    lines.extend(["", "## 产品菜单树", ""])
    lines.extend(_render_tree(rows))

    lines.extend(["", "## 待复核队列", ""])
    if not review_rows:
        lines.append("未检测到需要人工复核的模糊菜单。")
    else:
        lines.extend(["| Path | Layer | Reason | XMLID |", "| --- | --- | --- | --- |"])
        for row in review_rows:
            reasons = ", ".join(row.get("classification_reasons") or [])
            lines.append(
                f"| {_escape(row.get('path'))} | `{_escape(row.get('layer'))}` | {_escape(reasons)} | `{_escape(row.get('xmlid'))}` |"
            )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "input": str(INPUT), "output": str(OUTPUT), "menu_count": len(rows)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
