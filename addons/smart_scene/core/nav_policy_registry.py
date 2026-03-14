# -*- coding: utf-8 -*-
from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Dict, Iterable, List, Optional


DEFAULT_NAV_GROUP_LABELS = {
    "others": "其他场景",
}

DEFAULT_NAV_GROUP_ORDER = {
    "others": 999,
}

DEFAULT_NAV_GROUP_ALIASES: Dict[str, str] = {}


class NavPolicyProvider:
    def __init__(
        self,
        *,
        policy_key: str,
        provider_key: str,
        module_name: str,
        provider_path: Path,
        priority: int = 100,
        source: str = "registry",
        policy_version: str = "v1",
        loader_name: str = "build_nav_group_policy",
    ):
        self.policy_key = str(policy_key or "").strip().lower()
        self.provider_key = provider_key
        self.module_name = module_name
        self.provider_path = provider_path
        self.priority = int(priority or 0)
        self.source = source
        self.policy_version = policy_version
        self.loader_name = loader_name

    def is_available(self) -> bool:
        return self.provider_path.exists() and self.provider_path.is_file()


class NavPolicyRegistry:
    def __init__(self):
        self._providers: Dict[str, List[NavPolicyProvider]] = {}

    def register(self, provider: NavPolicyProvider) -> None:
        if not provider.policy_key:
            return
        rows = self._providers.setdefault(provider.policy_key, [])
        dedup_key = (provider.provider_key, str(provider.provider_path.resolve()))
        if any((item.provider_key, str(item.provider_path.resolve())) == dedup_key for item in rows):
            return
        rows.append(provider)
        rows.sort(key=lambda item: (item.priority, item.provider_key), reverse=True)

    def register_spec(self, **kwargs) -> None:
        self.register(NavPolicyProvider(**kwargs))

    def get_provider(self, policy_key: str) -> Optional[NavPolicyProvider]:
        rows = self._providers.get(str(policy_key or "").strip().lower(), [])
        for row in rows:
            if row.is_available():
                return row
        return None

    def list_providers(self, policy_key: Optional[str] = None) -> List[NavPolicyProvider]:
        if policy_key:
            return list(self._providers.get(str(policy_key or "").strip().lower(), []))
        rows: List[NavPolicyProvider] = []
        for group in self._providers.values():
            rows.extend(group)
        return rows


def _resolve_addons_root(base_dir: Path) -> Path:
    current = base_dir.resolve()
    if current.is_file():
        current = current.parent
    for parent in [current] + list(current.parents):
        if parent.name == "addons":
            return parent
    return base_dir.resolve().parents[2]


def _load_module(path: Path, module_name: str):
    spec = spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        return None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _registration_module_candidates(addons_root: Path) -> Iterable[tuple[str, Path]]:
    return [
        (
            "smart_construction_scene_register_nav_policy",
            addons_root / "smart_construction_scene" / "bootstrap" / "register_nav_policy.py",
        ),
    ]


def _register_from_modules(registry: NavPolicyRegistry, addons_root: Path) -> None:
    for module_name, path in _registration_module_candidates(addons_root):
        if not path.exists() or not path.is_file():
            continue
        module = _load_module(path, module_name)
        if module is None:
            continue
        registrar = getattr(module, "register_nav_product_policies", None)
        if not callable(registrar):
            continue
        try:
            registrar(registry, addons_root)
        except Exception:
            continue


def build_nav_policy_registry(base_dir: Path) -> NavPolicyRegistry:
    addons_root = _resolve_addons_root(base_dir)
    registry = NavPolicyRegistry()
    _register_from_modules(registry, addons_root)
    return registry


def _fallback_policy() -> dict:
    return {
        "group_labels": dict(DEFAULT_NAV_GROUP_LABELS),
        "group_order": dict(DEFAULT_NAV_GROUP_ORDER),
        "group_aliases": dict(DEFAULT_NAV_GROUP_ALIASES),
        "source": "platform_default",
        "provider_key": "platform.default.scene_nav_v1",
        "policy_version": "v1",
        "validation": {
            "ok": True,
            "issues": [],
            "policy_key": "scene_nav_v1",
        },
    }


def _validate_nav_group_policy(policy_key: str, payload: dict) -> dict:
    issues: List[dict] = []
    if not isinstance(payload, dict):
        return {
            "ok": False,
            "issues": [{"code": "policy_not_dict"}],
            "policy_key": policy_key,
        }

    labels = payload.get("group_labels") if isinstance(payload.get("group_labels"), dict) else {}
    order = payload.get("group_order") if isinstance(payload.get("group_order"), dict) else {}
    aliases = payload.get("group_aliases") if isinstance(payload.get("group_aliases"), dict) else {}

    if not labels:
        issues.append({"code": "missing_group_labels"})
    if not order:
        issues.append({"code": "missing_group_order"})

    for key, value in labels.items():
        if not isinstance(key, str) or not key.strip():
            issues.append({"code": "invalid_group_label_key", "key": str(key)})
        if not isinstance(value, str) or not value.strip():
            issues.append({"code": "invalid_group_label_value", "key": str(key)})

    for key, value in order.items():
        if not isinstance(key, str) or not key.strip():
            issues.append({"code": "invalid_group_order_key", "key": str(key)})
            continue
        try:
            int(value)
        except Exception:
            issues.append({"code": "invalid_group_order_value", "key": str(key), "value": str(value)})

    for source_key, target_key in aliases.items():
        if not isinstance(source_key, str) or not source_key.strip():
            issues.append({"code": "invalid_alias_source", "key": str(source_key)})
        if not isinstance(target_key, str) or not target_key.strip():
            issues.append({"code": "invalid_alias_target", "key": str(source_key), "value": str(target_key)})

    return {
        "ok": len(issues) == 0,
        "issues": issues,
        "policy_key": policy_key,
    }


def build_nav_policy_coverage_report(*, base_dir: Path, policy_key: str = "") -> dict:
    registry = build_nav_policy_registry(base_dir)
    providers = registry.list_providers(policy_key if policy_key else None)
    rows = []
    available_count = 0
    for item in providers:
        available = bool(item.is_available())
        if available:
            available_count += 1
        rows.append(
            {
                "policy_key": item.policy_key,
                "provider_key": item.provider_key,
                "module_name": item.module_name,
                "source": item.source,
                "policy_version": item.policy_version,
                "priority": int(item.priority),
                "available": available,
                "provider_path": str(item.provider_path),
            }
        )
    return {
        "policy_key": str(policy_key or ""),
        "provider_count": len(providers),
        "provider_available_count": available_count,
        "providers": rows,
    }


def resolve_nav_group_policy(policy_key: str, *, base_dir: Path) -> dict:
    registry = build_nav_policy_registry(base_dir)
    provider = registry.get_provider(policy_key)
    if provider is None:
        fallback = _fallback_policy()
        fallback["validation"] = {
            "ok": False,
            "issues": [{"code": "provider_not_found", "policy_key": str(policy_key or "")}],
            "policy_key": str(policy_key or ""),
        }
        return fallback

    module = _load_module(provider.provider_path, f"{provider.module_name}_{provider.provider_key}".replace(".", "_"))
    if module is None:
        fallback = _fallback_policy()
        fallback["validation"] = {
            "ok": False,
            "issues": [{"code": "provider_module_load_failed", "provider_key": provider.provider_key}],
            "policy_key": str(policy_key or ""),
        }
        return fallback

    loader = getattr(module, provider.loader_name, None)
    if not callable(loader):
        fallback = _fallback_policy()
        fallback["validation"] = {
            "ok": False,
            "issues": [{"code": "policy_loader_not_callable", "provider_key": provider.provider_key}],
            "policy_key": str(policy_key or ""),
        }
        return fallback

    try:
        payload = loader()
    except Exception:
        fallback = _fallback_policy()
        fallback["validation"] = {
            "ok": False,
            "issues": [{"code": "policy_loader_runtime_error", "provider_key": provider.provider_key}],
            "policy_key": str(policy_key or ""),
        }
        return fallback

    if not isinstance(payload, dict):
        fallback = _fallback_policy()
        fallback["validation"] = {
            "ok": False,
            "issues": [{"code": "policy_payload_not_dict", "provider_key": provider.provider_key}],
            "policy_key": str(policy_key or ""),
        }
        return fallback

    validation = _validate_nav_group_policy(str(policy_key or ""), payload)
    if not validation.get("ok"):
        fallback = _fallback_policy()
        fallback["validation"] = validation
        return fallback

    group_labels = payload.get("group_labels") if isinstance(payload.get("group_labels"), dict) else {}
    group_order = payload.get("group_order") if isinstance(payload.get("group_order"), dict) else {}
    group_aliases = payload.get("group_aliases") if isinstance(payload.get("group_aliases"), dict) else {}

    return {
        "group_labels": {**DEFAULT_NAV_GROUP_LABELS, **group_labels},
        "group_order": {**DEFAULT_NAV_GROUP_ORDER, **group_order},
        "group_aliases": {**DEFAULT_NAV_GROUP_ALIASES, **group_aliases},
        "source": provider.source,
        "provider_key": provider.provider_key,
        "policy_version": provider.policy_version,
        "validation": validation,
    }
