# -*- coding: utf-8 -*-
from __future__ import annotations

import os


class LifecycleCapabilityService:
    _MODES = {"allow", "deny", "readonly"}

    def __init__(self, env):
        self.env = env

    def describe_project(self, project):
        matrix, meta = self._load_matrix()
        lifecycle_state = project.lifecycle_state or "draft"
        capabilities = {}
        all_caps = sorted({cap for caps in matrix.values() for cap in caps.keys()})
        for cap in all_caps:
            mode = matrix.get(lifecycle_state, {}).get(cap, "deny")
            if mode not in self._MODES:
                mode = "deny"
            capabilities[cap] = {"mode": mode, "allowed": mode == "allow"}
        return {
            "lifecycle_state": lifecycle_state,
            "capabilities": capabilities,
            "matrix_meta": meta,
        }

    def resolve(self, project, capability_code):
        matrix, meta = self._load_matrix()
        lifecycle_state = project.lifecycle_state or "draft"
        mode = matrix.get(lifecycle_state, {}).get(capability_code, "deny")
        if mode not in self._MODES:
            mode = "deny"
        return {
            "allowed": mode == "allow",
            "mode": mode,
            "reason": {
                "lifecycle_state": lifecycle_state,
                "capability_code": capability_code,
            },
            "matrix_meta": meta,
        }

    def _load_matrix(self):
        path = os.environ.get("SC_LIFECYCLE_CAP_MATRIX_PATH") or self._default_matrix_path()
        if not os.path.exists(path):
            return {}, {"path": path, "error": "matrix_not_found"}
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        matrix = self._parse_matrix(content)
        return matrix, {"path": path, "error": None}

    def _default_matrix_path(self):
        module_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
        repo_root = os.path.abspath(os.path.join(module_root, os.pardir, os.pardir))
        return os.path.join(repo_root, "docs", "architecture", "lifecycle_capability_matrix.yaml")

    def _parse_matrix(self, content):
        matrix = {}
        current_state = None
        for raw in content.splitlines():
            line = raw.split("#", 1)[0].rstrip()
            if not line.strip():
                continue
            if not line.startswith(" "):
                if not line.endswith(":"):
                    continue
                current_state = line[:-1].strip()
                if current_state:
                    matrix[current_state] = {}
                continue
            if not current_state:
                continue
            stripped = line.lstrip()
            if ":" not in stripped:
                continue
            key, value = stripped.split(":", 1)
            key = key.strip()
            value = value.strip()
            if not key or value not in self._MODES:
                continue
            matrix[current_state][key] = value
        return matrix
