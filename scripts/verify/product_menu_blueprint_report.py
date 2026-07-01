#!/usr/bin/env python3
"""Render a product-facing menu blueprint from the runtime menu catalog."""

from __future__ import annotations

import json
import os
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / os.getenv("PRODUCT_MENU_CATALOG_RUNTIME_JSON", "artifacts/product/product_menu_catalog_runtime_v1.json")
OUTPUT = ROOT / os.getenv("PRODUCT_MENU_BLUEPRINT_REPORT_MD", "docs/product/product_menu_blueprint_v1.md")
PRODUCT_ROOT = "智慧施工管理平台"


def _text(value: object) -> str:
    return str(value or "").strip()


def _escape(value: object) -> str:
    return _text(value).replace("|", "\\|")


def _parts(row: dict) -> list[str]:
    return [part for part in _text(row.get("path")).split(" / ") if part]


def _depth(row: dict) -> int:
    parts = _parts(row)
    if parts and parts[0] == PRODUCT_ROOT:
        return max(0, len(parts) - 1)
    return max(0, len(parts) - 1)


def _action_label(row: dict) -> str:
    scene_key = _text(row.get("scene_key"))
    if scene_key:
        return f"scene:{scene_key}"
    meta = row.get("action_meta") if isinstance(row.get("action_meta"), dict) else {}
    model = _text(meta.get("res_model"))
    if model:
        return model
    return _text(row.get("action_model"))


def _under(row: dict, parent_path: str) -> bool:
    path = _text(row.get("path"))
    return path == parent_path or path.startswith(parent_path + " / ")


def _direct_children(rows: list[dict], parent_path: str, layer: str | None = None) -> list[dict]:
    parent_depth = len([part for part in parent_path.split(" / ") if part])
    out = []
    for row in rows:
        parts = _parts(row)
        if len(parts) != parent_depth + 1:
            continue
        if not _text(row.get("path")).startswith(parent_path + " / "):
            continue
        if layer and row.get("layer") != layer:
            continue
        out.append(row)
    return sorted(out, key=lambda item: (int(item.get("sequence") or 0), _text(item.get("path"))))


def _center_metrics(rows: list[dict], center: dict) -> dict[str, int]:
    path = _text(center.get("path"))
    scoped = [row for row in rows if row is not center and _under(row, path)]
    return {
        "active_formal": sum(1 for row in scoped if row.get("active") and row.get("layer") == "formal_product"),
        "active_history": sum(1 for row in scoped if row.get("active") and row.get("layer") == "history_acceptance"),
        "active_system": sum(1 for row in scoped if row.get("active") and row.get("layer") == "system_config"),
        "inactive": sum(1 for row in scoped if not row.get("active")),
        "action": sum(1 for row in scoped if row.get("action_raw")),
    }


def _render_center_tree(rows: list[dict], center: dict) -> list[str]:
    center_path = _text(center.get("path"))
    lines = []
    children = _direct_children(rows, center_path)
    for child in children:
        if not child.get("active") or child.get("layer") != "formal_product":
            continue
        action = _action_label(child)
        suffix = f" -> `{action}`" if action else ""
        lines.append(f"- {_text(child.get('name'))}{suffix}")
        for grandchild in _direct_children(rows, _text(child.get("path")), "formal_product"):
            if not grandchild.get("active"):
                continue
            sub_action = _action_label(grandchild)
            sub_suffix = f" -> `{sub_action}`" if sub_action else ""
            lines.append(f"  - {_text(grandchild.get('name'))}{sub_suffix}")
    if not lines:
        lines.append("- 暂无直接正式产品子入口。")
    return lines


def _render_boundary_section(rows: list[dict], layer: str, title: str) -> list[str]:
    scoped = [row for row in rows if row.get("active") and row.get("layer") == layer]
    lines = [f"## {title}", ""]
    if not scoped:
        lines.append("无。")
        return lines
    roots = []
    for row in scoped:
        parts = _parts(row)
        if len(parts) <= 2 or (parts and parts[0] != PRODUCT_ROOT and len(parts) <= 2):
            roots.append(row)
    if not roots:
        roots = scoped[:20]
    for row in roots:
        action = _action_label(row)
        suffix = f" -> `{action}`" if action else ""
        lines.append(f"- {_text(row.get('path'))}{suffix}")
    return lines


def _history_inside_formal_centers(rows: list[dict]) -> list[dict]:
    out = []
    for row in rows:
        parts = _parts(row)
        if (
            row.get("active")
            and row.get("layer") == "history_acceptance"
            and len(parts) >= 3
            and parts[0] == PRODUCT_ROOT
            and parts[1] not in {"用户核对菜单", "用户验收", "基础设置"}
        ):
            out.append(row)
    return sorted(out, key=lambda item: _text(item.get("path")))


def main() -> int:
    if not INPUT.is_file():
        raise SystemExit(f"missing runtime product menu catalog: {INPUT}")
    payload = json.loads(INPUT.read_text(encoding="utf-8"))
    rows = payload.get("menus") if isinstance(payload.get("menus"), list) else []
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    layer_counts = summary.get("layer_counts") if isinstance(summary.get("layer_counts"), dict) else {}
    review_rows = [row for row in rows if row.get("needs_review")]
    active_rows = [row for row in rows if row.get("active")]
    active_layer_counts = Counter(row.get("layer") for row in active_rows)

    centers = [
        row
        for row in rows
        if row.get("active")
        and row.get("layer") == "formal_product"
        and len(_parts(row)) == 2
        and _parts(row)[0] == PRODUCT_ROOT
    ]
    centers = sorted(centers, key=lambda item: (int(item.get("sequence") or 0), _text(item.get("path"))))
    mixed_history_rows = _history_inside_formal_centers(rows)

    lines = [
        "# 产品菜单蓝图 V1",
        "",
        "本蓝图由运行时菜单台账生成，用于回答“正式产品菜单长什么样”。历史验收、系统配置、开发治理不并入正式产品菜单，只作为边界列示。",
        "",
        "## 当前结论",
        "",
        f"- 正式产品一级中心：`{len(centers)}` 个",
        f"- 正式产品菜单：`{int(layer_counts.get('formal_product', 0))}` 个，其中 active `{int(active_layer_counts.get('formal_product', 0))}` 个",
        f"- 系统配置菜单：`{int(layer_counts.get('system_config', 0))}` 个，其中 active `{int(active_layer_counts.get('system_config', 0))}` 个",
        f"- 历史验收菜单：`{int(layer_counts.get('history_acceptance', 0))}` 个，其中 active `{int(active_layer_counts.get('history_acceptance', 0))}` 个",
        f"- 开发治理菜单：`{int(layer_counts.get('dev_governance', 0))}` 个，其中 active `{int(active_layer_counts.get('dev_governance', 0))}` 个",
        f"- 待复核菜单：`{len(review_rows)}` 个",
        "",
        "## 正式产品一级中心",
        "",
        "| 中心 | 正式子入口 | 历史验收子入口 | 系统配置子入口 | 隐藏项 | 主要可见用户 | XMLID |",
        "| --- | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for center in centers:
        metrics = _center_metrics(rows, center)
        visible = ", ".join(center.get("visible_logins") or [])
        lines.append(
            "| %s | %d | %d | %d | %d | %s | `%s` |"
            % (
                _escape(center.get("name")),
                metrics["active_formal"],
                metrics["active_history"],
                metrics["active_system"],
                metrics["inactive"],
                _escape(visible),
                _escape(center.get("xmlid")),
            )
        )

    lines.extend(["", "## 正式产品菜单结构", ""])
    for center in centers:
        metrics = _center_metrics(rows, center)
        lines.extend(
            [
                f"### {_text(center.get('name'))}",
                "",
                f"- formal_active: `{metrics['active_formal']}`",
                f"- history_active_under_center: `{metrics['active_history']}`",
                f"- system_config_active_under_center: `{metrics['active_system']}`",
                "",
            ]
        )
        lines.extend(_render_center_tree(rows, center))
        lines.append("")

    lines.extend(_render_boundary_section(rows, "system_config", "系统配置边界"))
    lines.extend([""])
    lines.extend(_render_boundary_section(rows, "history_acceptance", "历史验收边界"))
    lines.extend([""])
    lines.extend(_render_boundary_section(rows, "dev_governance", "开发治理边界"))

    lines.extend(
        [
            "",
            "## 混入正式中心的历史入口",
            "",
            "这些入口仍挂在正式产品中心下，但分类属于历史验收。下一步应逐项决定：迁到用户验收/用户核对入口、转成正式产品入口，或隐藏。",
            "",
        ]
    )
    if not mixed_history_rows:
        lines.append("无。")
    else:
        lines.extend(["| 中心 | 菜单 | 模型 | XMLID |", "| --- | --- | --- | --- |"])
        for row in mixed_history_rows:
            parts = _parts(row)
            center = parts[1] if len(parts) > 1 else ""
            lines.append(
                "| %s | %s | `%s` | `%s` |"
                % (
                    _escape(center),
                    _escape(row.get("path")),
                    _escape(_action_label(row)),
                    _escape(row.get("xmlid")),
                )
            )

    lines.extend(["", "## 收口信号", ""])
    if review_rows:
        lines.append(f"- 存在 `{len(review_rows)}` 个待复核菜单，必须先归类或隐藏。")
    else:
        lines.append("- 当前无待复核菜单。")
    if int(active_layer_counts.get("user_config", 0)) == 0:
        lines.append("- 当前无独立用户配置入口；低代码和产品配置仍归入系统配置边界。")
    for center in centers:
        metrics = _center_metrics(rows, center)
        if metrics["active_history"] or metrics["active_system"]:
            lines.append(
                f"- `{_text(center.get('name'))}` 下存在非正式产品子入口：history={metrics['active_history']} system={metrics['active_system']}，需要确认是否应继续对业务用户可见。"
            )
    if mixed_history_rows:
        lines.append(f"- 共 `{len(mixed_history_rows)}` 个历史入口混在正式产品中心下，建议作为下一轮菜单收口清单。")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": "PASS",
                "input": str(INPUT),
                "output": str(OUTPUT),
                "formal_centers": len(centers),
                "needs_review": len(review_rows),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
