# -*- coding: utf-8 -*-
from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional


def _resolve_addons_root(base_dir: Path) -> Path:
    current = base_dir.resolve()
    if current.is_file():
        current = current.parent
    for parent in [current] + list(current.parents):
        if parent.name == "addons":
            return parent
    return base_dir.resolve().parents[2]


class SceneContentProvider:
    def __init__(
        self,
        *,
        scene_key: str,
        provider_key: str,
        module_name: str,
        provider_path: Path,
        priority: int = 100,
        contract_version: str = "v1",
        source: str = "registry",
    ):
        self.scene_key = scene_key
        self.provider_key = provider_key
        self.module_name = module_name
        self.provider_path = provider_path
        self.priority = priority
        self.contract_version = contract_version
        self.source = source

    def normalized_scene_key(self) -> str:
        return str(self.scene_key or "").strip().lower()

    def is_available(self) -> bool:
        return self.provider_path.exists() and self.provider_path.is_file()


class SceneProviderRegistry:
    def __init__(self):
        self._providers: Dict[str, List[SceneContentProvider]] = {}

    def register(self, provider: SceneContentProvider) -> None:
        scene_key = provider.normalized_scene_key()
        if not scene_key:
            return
        rows = self._providers.setdefault(scene_key, [])
        dedup_key = (provider.provider_key, str(provider.provider_path.resolve()))
        if any((item.provider_key, str(item.provider_path.resolve())) == dedup_key for item in rows):
            return
        rows.append(provider)
        rows.sort(key=lambda item: (int(item.priority), item.provider_key), reverse=True)

    def register_spec(self, **kwargs) -> None:
        self.register(SceneContentProvider(**kwargs))

    def get_provider(self, scene_key: str) -> Optional[SceneContentProvider]:
        rows = self._providers.get(str(scene_key or "").strip().lower(), [])
        for row in rows:
            if row.is_available():
                return row
        return None

    def list_providers(self, scene_key: Optional[str] = None) -> List[SceneContentProvider]:
        if scene_key:
            return list(self._providers.get(str(scene_key).strip().lower(), []))
        merged: List[SceneContentProvider] = []
        for rows in self._providers.values():
            merged.extend(rows)
        return merged


def _load_module(path: Path, module_name: str):
    spec = spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        return None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _register_fallback_providers(registry: SceneProviderRegistry, addons_root: Path) -> None:
    project_dashboard_candidates = [
        addons_root / "smart_construction_scene" / "profiles" / "project_dashboard_scene_content.py",
        addons_root / "smart_construction_scene" / "services" / "project_dashboard_scene_content.py",
    ]
    for index, path in enumerate(project_dashboard_candidates):
        registry.register(
            SceneContentProvider(
                scene_key="project.dashboard",
                provider_key=f"construction.project_dashboard.fallback.{index + 1}",
                module_name="smart_construction_scene",
                provider_path=path,
                priority=200 - index,
                source="fallback_candidates",
            )
        )

    scene_registry_candidates = [
        addons_root / "smart_construction_scene" / "profiles" / "scene_registry_content.py",
        addons_root / "smart_construction_scene" / "services" / "scene_registry_content.py",
    ]
    for index, path in enumerate(scene_registry_candidates):
        registry.register(
            SceneContentProvider(
                scene_key="scene.registry",
                provider_key=f"construction.scene_registry.fallback.{index + 1}",
                module_name="smart_construction_scene",
                provider_path=path,
                priority=200 - index,
                source="fallback_candidates",
            )
        )

def _registration_module_candidates(addons_root: Path) -> Iterable[tuple[str, Path]]:
    candidates = [
        (
            "smart_construction_scene_register_scene_providers",
            addons_root / "smart_construction_scene" / "bootstrap" / "register_scene_providers.py",
        ),
    ]
    return candidates


def _register_from_modules(registry: SceneProviderRegistry, addons_root: Path) -> None:
    for module_name, path in _registration_module_candidates(addons_root):
        if not path.exists() or not path.is_file():
            continue
        module = _load_module(path, module_name)
        if module is None:
            continue
        registrar = getattr(module, "register_scene_content_providers", None)
        if not callable(registrar):
            continue
        try:
            registrar(registry, addons_root)
        except Exception:
            continue


def build_scene_provider_registry(base_dir: Path) -> SceneProviderRegistry:
    addons_root = _resolve_addons_root(base_dir)
    registry = SceneProviderRegistry()
    _register_fallback_providers(registry, addons_root)
    _register_from_modules(registry, addons_root)
    return registry


def resolve_scene_provider(scene_key: str, base_dir: Path) -> Optional[SceneContentProvider]:
    registry = build_scene_provider_registry(base_dir)
    return registry.get_provider(scene_key)


def resolve_scene_provider_path(scene_key: str, base_dir: Path) -> Optional[Path]:
    provider = resolve_scene_provider(scene_key, base_dir)
    return provider.provider_path if provider else None


def list_scene_provider_entries(base_dir: Path) -> List[Dict[str, str]]:
    registry = build_scene_provider_registry(base_dir)
    rows: List[Dict[str, str]] = []
    for item in registry.list_providers():
        rows.append(
            {
                "scene_key": item.scene_key,
                "provider_key": item.provider_key,
                "module_name": item.module_name,
                "provider_path": str(item.provider_path),
                "priority": str(item.priority),
                "contract_version": item.contract_version,
                "source": item.source,
                "available": "1" if item.is_available() else "0",
            }
        )
    return rows
