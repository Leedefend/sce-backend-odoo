#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guard contract-level default tab projection for business forms.

The standardizer is intentionally a rebuildable UI contract projection. It must
not mutate Odoo XML views or business facts.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
ASSEMBLER_PATH = REPO_ROOT / "addons/smart_core/core/unified_page_contract_v2_assembler.py"


def load_assembler_module():
    package_name = "smart_core_guard.core"
    sys.modules.setdefault("smart_core_guard", type(sys)("smart_core_guard"))
    sys.modules.setdefault(package_name, type(sys)(package_name))

    source_authority_path = REPO_ROOT / "addons/smart_core/core/source_authority.py"
    source_spec = importlib.util.spec_from_file_location(
        f"{package_name}.source_authority",
        source_authority_path,
    )
    source_module = importlib.util.module_from_spec(source_spec)
    assert source_spec and source_spec.loader
    sys.modules[f"{package_name}.source_authority"] = source_module
    source_spec.loader.exec_module(source_module)

    spec = importlib.util.spec_from_file_location(
        f"{package_name}.unified_page_contract_v2_assembler",
        ASSEMBLER_PATH,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def sample_form_tree() -> list[dict[str, Any]]:
    return [
        {
            "type": "sheet",
            "containerType": "sheet",
            "containerId": "main.form.sheet",
            "children": [
                {
                    "type": "container",
                    "containerType": "container",
                    "containerId": "button_box",
                    "attributes": {"class": "oe_button_box"},
                    "children": [],
                },
                {
                    "type": "group",
                    "containerType": "group",
                    "containerId": "main.info",
                    "children": [
                        {"type": "field", "name": "name", "fieldInfo": {"type": "char", "label": "单号"}},
                        {"type": "field", "name": "amount", "fieldInfo": {"type": "monetary", "label": "金额"}},
                    ],
                },
                {
                    "type": "group",
                    "containerType": "group",
                    "containerId": "business.detail",
                    "children": [
                        {"type": "field", "name": "line_ids", "fieldInfo": {"type": "one2many", "label": "明细"}},
                    ],
                },
                {
                    "type": "group",
                    "containerType": "group",
                    "containerId": "legacy.trace",
                    "children": [
                        {"type": "field", "name": "legacy_record_id", "fieldInfo": {"type": "char", "label": "历史记录"}},
                    ],
                },
                {
                    "type": "group",
                    "containerType": "group",
                    "containerId": "note.info",
                    "children": [
                        {"type": "field", "name": "note", "fieldInfo": {"type": "text", "label": "备注"}},
                    ],
                },
            ],
            "widgetList": [],
        }
    ]


def nested_nodes(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    stack = list(nodes)
    while stack:
        node = stack.pop(0)
        if not isinstance(node, dict):
            continue
        out.append(node)
        for key in ("children", "tabs", "pages", "nodes", "items"):
            value = node.get(key)
            if isinstance(value, list):
                stack.extend(item for item in value if isinstance(item, dict))
    return out


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    assembler = load_assembler_module()

    status: list[dict[str, Any]] = []
    tree = sample_form_tree()
    assembler._standardize_business_form_default_tabs(  # pylint: disable=protected-access
        tree,
        model="payment.request",
        view_type="form",
        container_status=status,
    )
    nodes = nested_nodes(tree)
    notebooks = [node for node in nodes if node.get("containerType") == "notebook"]
    pages = [node for node in nodes if node.get("containerType") == "page"]
    assert_true(len(notebooks) == 0, "contract projection must not invent visible generic notebook tabs")
    assert_true(len(pages) == 0, "contract projection must not invent visible generic notebook pages")
    assert_true(
        tree[0]["children"][0].get("containerId") == "button_box",
        "smart button box should stay in its native position",
    )

    untouched = sample_form_tree()
    assembler._standardize_business_form_default_tabs(  # pylint: disable=protected-access
        untouched,
        model="res.partner",
        view_type="form",
        container_status=[],
    )
    assert_true(
        not any(node.get("containerType") == "notebook" for node in nested_nodes(untouched)),
        "non-whitelisted models must not be projected",
    )

    existing = sample_form_tree()
    existing[0]["children"].append(
        {"type": "notebook", "containerType": "notebook", "containerId": "native.notebook", "children": []}
    )
    assembler._standardize_business_form_default_tabs(  # pylint: disable=protected-access
        existing,
        model="payment.request",
        view_type="form",
        container_status=[],
    )
    assert_true(
        len([node for node in nested_nodes(existing) if node.get("containerType") == "notebook"]) == 1,
        "forms with native tabs must not receive duplicate projected notebooks",
    )

    task_tree = sample_form_tree()
    task_status: list[dict[str, Any]] = []
    assembler._standardize_business_form_default_tabs(  # pylint: disable=protected-access
        task_tree,
        model="project.task",
        view_type="form",
        container_status=task_status,
    )
    assert_true(
        not any(node.get("containerType") == "notebook" for node in nested_nodes(task_tree)),
        "project.task should not receive generic tabs when its runtime contract has no native notebook",
    )

    semantic_tree = sample_form_tree()
    assembler._standardize_form_container_semantics(  # pylint: disable=protected-access
        semantic_tree,
        model="sc.equipment.plan",
        view_type="form",
    )
    groups = [node for node in nested_nodes(semantic_tree) if node.get("containerType") == "group"]
    assert_true(groups, "semantic guard fixture should contain group nodes")
    assert_true(
        all(str(node.get("semanticTitle") or "").strip() not in {"", "group"} for node in groups),
        "unlabelled form groups should receive semantic metadata titles",
    )
    assert_true(
        all(not str(node.get("title") or node.get("label") or node.get("string") or "").strip() for node in groups),
        "generated semantic group names must not become user-visible group titles",
    )
    assert_true(
        any((node.get("sourceAuthority") or {}).get("runtime_carrier") == "business_form_semantic_label_standardizer" for node in groups),
        "semantic group labels should declare projection runtime carrier",
    )

    native_label_tree = [
        {
            "type": "sheet",
            "containerType": "sheet",
            "children": [
                {
                    "type": "group",
                    "containerType": "group",
                    "containerId": "task.core",
                    "title": "任务基础信息",
                    "label": "任务基础信息",
                    "string": "任务基础信息",
                    "children": [
                        {"type": "field", "name": "name", "fieldInfo": {"type": "char", "label": "任务名称"}},
                    ],
                }
            ],
        }
    ]
    assembler._standardize_form_container_semantics(  # pylint: disable=protected-access
        native_label_tree,
        model="project.task",
        view_type="form",
    )
    native_group = [node for node in nested_nodes(native_label_tree) if node.get("containerType") == "group"][0]
    assert_true(native_group.get("title") == "任务基础信息", "native group titles should stay visible")
    assert_true(native_group.get("semanticTitle") == "任务基础信息", "native group titles should also become semantic contract metadata")
    assert_true(
        (native_group.get("sourceAuthority") or {}).get("runtime_carrier") == "business_form_semantic_label_standardizer",
        "native semantic metadata should expose the semantic runtime carrier",
    )

    chinese_container_tree = [
        {
            "type": "sheet",
            "containerType": "sheet",
            "children": [
                {
                    "type": "group",
                    "containerType": "group",
                    "containerId": "来源追溯",
                    "title": "来源追溯",
                    "label": "来源追溯",
                    "string": "来源追溯",
                    "children": [
                        {"type": "field", "name": "source_model", "fieldInfo": {"type": "char", "label": "来源模型"}},
                    ],
                }
            ],
        }
    ]
    assembler._standardize_form_container_semantics(  # pylint: disable=protected-access
        chinese_container_tree,
        model="sc.material.price",
        view_type="form",
    )
    chinese_group = [node for node in nested_nodes(chinese_container_tree) if node.get("containerType") == "group"][0]
    assert_true(
        chinese_group.get("semanticTitle") == "来源追溯",
        "Chinese business labels that also appear as container ids should not be treated as generic ids",
    )

    wrapped_tree = [
        {
            "type": "sheet",
            "containerType": "sheet",
            "children": [
                {
                    "type": "group",
                    "containerType": "group",
                    "containerId": "top.wrapper",
                    "children": [
                        {
                            "type": "group",
                            "containerType": "group",
                            "containerId": "schedule.info",
                            "children": [
                                {"type": "field", "name": "start_date", "fieldInfo": {"type": "date", "label": "开始日期"}},
                                {"type": "field", "name": "end_date", "fieldInfo": {"type": "date", "label": "结束日期"}},
                            ],
                        }
                    ],
                }
            ],
        }
    ]
    assembler._standardize_form_container_semantics(  # pylint: disable=protected-access
        wrapped_tree,
        model="sc.equipment.plan",
        view_type="form",
    )
    wrapped_groups = [node for node in nested_nodes(wrapped_tree) if node.get("containerType") == "group"]
    assert_true(
        [node.get("semanticTitle") for node in wrapped_groups] == ["主信息", "时间信息"],
        "top-level structural group should carry semantic metadata while nested groups carry field semantics",
    )
    assert_true(
        all(not str(node.get("title") or node.get("label") or node.get("string") or "").strip() for node in wrapped_groups),
        "generated wrapped group semantics must not become visible titles",
    )

    print("PASS form_structure_contract_standardizer_guard")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
