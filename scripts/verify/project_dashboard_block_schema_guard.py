#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BUILDERS_DIR = ROOT / "addons" / "smart_construction_core" / "services" / "project_dashboard_builders"

# block_type -> required data keys in all states (ready/empty/forbidden)
REQUIRED_KEYS = {
    "record_summary": {"summary"},
    "metric_row": {"items"},
    "progress_summary": {"task_total", "task_done", "completion_percent"},
    "record_table": {"columns", "rows"},
    "alert_panel": {"alerts"},
    "action_list": {"actions", "summary"},
}


def _must(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit(msg)


def _dict_keys(node):
    if not isinstance(node, ast.Dict):
        return None
    out = set()
    for k in node.keys:
        if isinstance(k, ast.Constant) and isinstance(k.value, str):
            out.add(k.value)
        else:
            return None
    return out


def _collect_builder_contract(path: Path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    block_key = ""
    block_type = ""
    states = {}

    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        for stmt in node.body:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name) and target.id == "block_key":
                        if isinstance(stmt.value, ast.Constant):
                            block_key = str(stmt.value.value)
                    if isinstance(target, ast.Name) and target.id == "block_type":
                        if isinstance(stmt.value, ast.Constant):
                            block_type = str(stmt.value.value)
            if isinstance(stmt, ast.FunctionDef) and stmt.name == "build":
                data_literal = None
                for line in stmt.body:
                    # capture "data = {...}" for ready state envelope(data=data)
                    if isinstance(line, ast.Assign):
                        for t in line.targets:
                            if isinstance(t, ast.Name) and t.id == "data":
                                k = _dict_keys(line.value)
                                if k is not None:
                                    data_literal = k
                    if isinstance(line, ast.If):
                        for sub in list(line.body) + list(line.orelse):
                            if isinstance(sub, ast.Return) and isinstance(sub.value, ast.Call):
                                call = sub.value
                                if isinstance(call.func, ast.Attribute) and call.func.attr == "_envelope":
                                    state = None
                                    data_keys = None
                                    for kw in call.keywords:
                                        if kw.arg == "state" and isinstance(kw.value, ast.Constant):
                                            state = str(kw.value.value)
                                        if kw.arg == "data":
                                            data_keys = _dict_keys(kw.value)
                                    if state and data_keys is not None:
                                        states[state] = data_keys
                    elif isinstance(line, ast.Return) and isinstance(line.value, ast.Call):
                        call = line.value
                        if isinstance(call.func, ast.Attribute) and call.func.attr == "_envelope":
                            state = None
                            uses_data_var = False
                            data_keys = None
                            for kw in call.keywords:
                                if kw.arg == "state" and isinstance(kw.value, ast.Constant):
                                    state = str(kw.value.value)
                                if kw.arg == "data":
                                    data_keys = _dict_keys(kw.value)
                                if kw.arg == "data" and isinstance(kw.value, ast.Name) and kw.value.id == "data":
                                    uses_data_var = True
                            if state and data_keys is not None:
                                states[state] = data_keys
                            elif state and uses_data_var and data_literal is not None:
                                states[state] = data_literal

    _must(bool(block_key), f"{path.name}: missing block_key")
    _must(bool(block_type), f"{path.name}: missing block_type")
    return block_key, block_type, states


def main():
    files = sorted(BUILDERS_DIR.glob("project_*_builder.py"))
    _must(len(files) >= 7, "expected at least 7 project block builders")

    for path in files:
        block_key, block_type, states = _collect_builder_contract(path)
        required = REQUIRED_KEYS.get(block_type)
        _must(required is not None, f"{path.name}: unsupported block_type {block_type}")
        for state in ("ready", "empty", "forbidden"):
            _must(state in states, f"{block_key}: missing envelope state {state}")
            keys = states[state]
            missing = sorted(required - keys)
            _must(not missing, f"{block_key}:{state}: missing required data keys {missing}")

    print("[verify.project.dashboard.block_schema] PASS")


if __name__ == "__main__":
    main()
