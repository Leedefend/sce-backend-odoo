#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE = ROOT / "addons/smart_core/utils/contract_governance.py"
SCENES = ROOT / "addons/smart_core/utils/contract_governance_scenes.py"
CI = ROOT / "make/ci.mk"

MAX_GOVERNANCE_LINES = 4213


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    errors: list[str] = []
    governance_text = _read(GOVERNANCE)
    scenes_text = _read(SCENES)
    ci_text = _read(CI)

    if not governance_text:
        errors.append(f"missing governance file: {GOVERNANCE.relative_to(ROOT)}")
    if not scenes_text:
        errors.append(f"missing scenes module: {SCENES.relative_to(ROOT)}")

    if governance_text:
        line_count = len(governance_text.splitlines())
        if line_count > MAX_GOVERNANCE_LINES:
            errors.append(f"contract_governance.py line budget exceeded: {line_count} > {MAX_GOVERNANCE_LINES}")
        for token in [
            "def _load_scenes_module()",
            "contract_governance_scenes.py",
            "_scenes._SCENE_SEMANTIC_PROFILE_REGISTRY = _SCENE_SEMANTIC_PROFILE_REGISTRY",
            "def normalize_scenes(scenes: list) -> list[dict]:",
        ]:
            if token not in governance_text:
                errors.append(f"contract_governance.py missing scene split token: {token}")

    if scenes_text:
        for token in [
            "def normalize_scenes(",
            "def _normalize_scene_list_profile(",
            "def _derive_scene_meta(",
            "_SCENE_SEMANTIC_PROFILE_REGISTRY",
        ]:
            if token not in scenes_text:
                errors.append(f"scenes module missing token: {token}")
        for token in (".search(", ".write(", "requests.", "env[", "registry["):
            if token in scenes_text:
                errors.append(f"scenes module must remain projection-only; found token: {token}")

    if "python3 scripts/verify/contract_governance_scenes_split_guard.py" not in ci_text:
        errors.append("ci.local.quick must run contract_governance_scenes_split_guard.py")

    if not errors:
        governance = _load(GOVERNANCE, "contract_governance_scenes_split_under_guard")
        before = list(governance._SCENE_SEMANTIC_PROFILE_REGISTRY)
        governance.register_scene_semantic_profile({"purpose": "Guard Purpose", "code_prefixes": ["guard."]})
        normalized = governance.normalize_scenes([{"code": "guard.scene", "name": "Guard Scene"}])
        purpose = ((normalized[0] or {}).get("scene_meta") or {}).get("purpose") if normalized else ""
        if purpose != "Guard Purpose":
            errors.append("normalize_scenes must read the shared scene semantic registry")
        governance._SCENE_SEMANTIC_PROFILE_REGISTRY[:] = before

    if errors:
        print("[contract_governance_scenes_split_guard] FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[contract_governance_scenes_split_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
