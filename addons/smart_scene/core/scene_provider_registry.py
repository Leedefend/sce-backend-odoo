# -*- coding: utf-8 -*-
from __future__ import annotations

import time
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Tuple


_ADDONS_ROOT_NAMES = {"addons", "extra-addons", "addons_external"}
_LOADED_PROVIDER_MODULES: Dict[tuple[str, str], object] = {}
_REGISTRATION_MODULE_PATH_STATUS: Dict[str, bool] = {}
_PROVIDER_PATH_AVAILABILITY: Dict[str, bool] = {}


def _resolve_addons_root_from_absolute_parts(base_dir: Path) -> Optional[Path]:
    if not base_dir.is_absolute():
        return None
    parts = base_dir.parts
    for index in range(len(parts) - 1, -1, -1):
        if parts[index] in _ADDONS_ROOT_NAMES:
            return Path(*parts[: index + 1])
    return None


def _provider_path_identity_key(provider_path: Path) -> str:
    if provider_path.is_absolute():
        return str(provider_path)
    return str(provider_path.resolve())


def _resolve_addons_root(base_dir: Path) -> Path:
    fast_root = _resolve_addons_root_from_absolute_parts(base_dir)
    if fast_root is not None:
        return fast_root
    current = base_dir.resolve()
    if current.is_file():
        current = current.parent
    for parent in [current] + list(current.parents):
        if parent.name == "addons":
            return parent
    return current.parents[2]


def _resolve_addons_root_with_timings(base_dir: Path) -> Tuple[Path, dict[str, int]]:
    timings_ms: dict[str, int] = {}

    def _mark(stage: str, started_at: float) -> float:
        timings_ms[stage] = int((time.perf_counter() - started_at) * 1000)
        return time.perf_counter()

    stage_ts = time.perf_counter()
    fast_root = _resolve_addons_root_from_absolute_parts(base_dir)
    stage_ts = _mark("fast_absolute_addons_lookup", stage_ts)
    if fast_root is not None:
        return fast_root, timings_ms
    stage_ts = time.perf_counter()
    current = base_dir.resolve()
    stage_ts = _mark("base_dir_resolve", stage_ts)
    if current.is_file():
        stage_ts = time.perf_counter()
        current = current.parent
        _mark("adjust_file_parent", stage_ts)
    stage_ts = time.perf_counter()
    parents = [current] + list(current.parents)
    stage_ts = _mark("materialize_parent_chain", stage_ts)
    stage_ts = time.perf_counter()
    for parent in parents:
        if parent.name == "addons":
            _mark("scan_parent_chain", stage_ts)
            return parent, timings_ms
    _mark("scan_parent_chain", stage_ts)
    stage_ts = time.perf_counter()
    fallback = current.parents[2]
    _mark("fallback_second_resolve", stage_ts)
    return fallback, timings_ms


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
        if not self.provider_path.is_absolute():
            return self.provider_path.exists() and self.provider_path.is_file()
        path_key = str(self.provider_path)
        cached_status = _PROVIDER_PATH_AVAILABILITY.get(path_key)
        if cached_status is not None:
            return cached_status
        available = self.provider_path.exists() and self.provider_path.is_file()
        _PROVIDER_PATH_AVAILABILITY[path_key] = available
        return available


class SceneProviderRegistry:
    def __init__(self):
        self._providers: Dict[str, List[SceneContentProvider]] = {}
        self._provider_keys: Dict[str, set[tuple[str, str]]] = {}
        self._resolved_provider_paths: Dict[str, str] = {}
        self._timings_ms: Dict[str, int] = {}

    def _accumulate_timing(self, stage: str, elapsed_ms: int) -> None:
        self._timings_ms[stage] = int(self._timings_ms.get(stage, 0) + max(int(elapsed_ms), 0))

    def timing_snapshot(self) -> Dict[str, int]:
        return dict(self._timings_ms)

    def register(self, provider: SceneContentProvider) -> None:
        total_started_at = time.perf_counter()
        scene_key = provider.normalized_scene_key()
        self._accumulate_timing(
            "register.normalized_scene_key",
            int((time.perf_counter() - total_started_at) * 1000),
        )
        if not scene_key:
            self._accumulate_timing(
                "register.total",
                int((time.perf_counter() - total_started_at) * 1000),
            )
            return

        dedup_started_at = time.perf_counter()
        provider_path_key = str(provider.provider_path)
        provider_path_resolved = self._resolved_provider_paths.get(provider_path_key)
        if provider_path_resolved is None:
            provider_path_resolved = _provider_path_identity_key(provider.provider_path)
            self._resolved_provider_paths[provider_path_key] = provider_path_resolved
        self._accumulate_timing(
            "register.provider_path_resolve",
            int((time.perf_counter() - dedup_started_at) * 1000),
        )
        rows = self._providers.setdefault(scene_key, [])
        keys = self._provider_keys.setdefault(scene_key, set())
        dedup_key = (provider.provider_key, provider_path_resolved)
        scan_started_at = time.perf_counter()
        if dedup_key in keys:
            self._accumulate_timing(
                "register.duplicate_scan",
                int((time.perf_counter() - scan_started_at) * 1000),
            )
            self._accumulate_timing(
                "register.total",
                int((time.perf_counter() - total_started_at) * 1000),
            )
            return
        self._accumulate_timing(
            "register.duplicate_scan",
            int((time.perf_counter() - scan_started_at) * 1000),
        )
        rows.append(provider)
        keys.add(dedup_key)
        sort_started_at = time.perf_counter()
        rows.sort(key=lambda item: (int(item.priority), item.provider_key), reverse=True)
        self._accumulate_timing(
            "register.sort_rows",
            int((time.perf_counter() - sort_started_at) * 1000),
        )
        self._accumulate_timing(
            "register.total",
            int((time.perf_counter() - total_started_at) * 1000),
        )

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
    started_at = time.perf_counter()
    cache_key = (module_name, str(path))
    cached = _LOADED_PROVIDER_MODULES.get(cache_key)
    if cached is not None:
        return cached, {
            "cache_lookup": int((time.perf_counter() - started_at) * 1000),
            "cache_hit": 0,
        }
    lookup_ms = int((time.perf_counter() - started_at) * 1000)
    stage_ts = time.perf_counter()
    spec = spec_from_file_location(module_name, path)
    spec_ms = int((time.perf_counter() - stage_ts) * 1000)
    if spec is None or spec.loader is None:
        return None, {
            "cache_lookup": lookup_ms,
            "cache_miss_spec": spec_ms,
        }
    stage_ts = time.perf_counter()
    module = module_from_spec(spec)
    module_from_spec_ms = int((time.perf_counter() - stage_ts) * 1000)
    stage_ts = time.perf_counter()
    spec.loader.exec_module(module)
    exec_module_ms = int((time.perf_counter() - stage_ts) * 1000)
    _LOADED_PROVIDER_MODULES[cache_key] = module
    return module, {
        "cache_lookup": lookup_ms,
        "cache_miss_spec": spec_ms,
        "cache_miss_module_from_spec": module_from_spec_ms,
        "cache_miss_exec_module": exec_module_ms,
    }


def _registration_module_path_exists(path: Path) -> bool:
    if not path.is_absolute():
        return path.exists() and path.is_file()
    path_key = str(path)
    cached_status = _REGISTRATION_MODULE_PATH_STATUS.get(path_key)
    if cached_status is not None:
        return cached_status
    exists = path.exists() and path.is_file()
    _REGISTRATION_MODULE_PATH_STATUS[path_key] = exists
    return exists


def _register_fallback_providers(registry: SceneProviderRegistry, addons_root: Path) -> None:
    project_dashboard_candidates = [
        addons_root / "smart_construction_scene" / "profiles" / "project_dashboard_scene_content.py",
        addons_root / "smart_construction_scene" / "services" / "project_dashboard_scene_content.py",
    ]
    for index, path in enumerate(project_dashboard_candidates):
        started_at = time.perf_counter()
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
        registry._accumulate_timing(
            "register_fallback_providers.project_dashboard",
            int((time.perf_counter() - started_at) * 1000),
        )

    scene_registry_candidates = [
        addons_root / "smart_construction_scene" / "profiles" / "scene_registry_content.py",
        addons_root / "smart_construction_scene" / "services" / "scene_registry_content.py",
    ]
    for index, path in enumerate(scene_registry_candidates):
        started_at = time.perf_counter()
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
        registry._accumulate_timing(
            "register_fallback_providers.scene_registry",
            int((time.perf_counter() - started_at) * 1000),
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
    candidates_started_at = time.perf_counter()
    candidates = list(_registration_module_candidates(addons_root))
    registry._accumulate_timing(
        "register_from_modules.candidate_derivation",
        int((time.perf_counter() - candidates_started_at) * 1000),
    )
    for module_name, path in candidates:
        path_check_started_at = time.perf_counter()
        if not _registration_module_path_exists(path):
            registry._accumulate_timing(
                "register_from_modules.path_check_missing",
                int((time.perf_counter() - path_check_started_at) * 1000),
            )
            continue
        registry._accumulate_timing(
            "register_from_modules.path_check_hit",
            int((time.perf_counter() - path_check_started_at) * 1000),
        )
        module, load_timings = _load_module(path, module_name)
        if isinstance(load_timings, dict):
            for key, value in load_timings.items():
                registry._accumulate_timing(
                    f"register_from_modules.load_module.{key}",
                    int(value),
                )
        registry._accumulate_timing(
            "register_from_modules.load_module",
            sum(
                int(value)
                for value in (load_timings or {}).values()
                if isinstance(value, int)
            ),
        )
        if module is None:
            continue
        registrar = getattr(module, "register_scene_content_providers", None)
        if not callable(registrar):
            continue
        try:
            registrar_started_at = time.perf_counter()
            registrar(registry, addons_root)
            registry._accumulate_timing(
                "register_from_modules.registrar_exec",
                int((time.perf_counter() - registrar_started_at) * 1000),
            )
        except Exception:
            continue


def build_scene_provider_registry(base_dir: Path) -> SceneProviderRegistry:
    registry, _timings = build_scene_provider_registry_with_timings(base_dir)
    return registry


def build_scene_provider_registry_with_timings(base_dir: Path) -> Tuple[SceneProviderRegistry, dict[str, int]]:
    timings_ms: dict[str, int] = {}

    def _mark(stage: str, started_at: float) -> float:
        timings_ms[stage] = int((time.perf_counter() - started_at) * 1000)
        return time.perf_counter()

    stage_ts = time.perf_counter()
    addons_root, addons_root_timings = _resolve_addons_root_with_timings(base_dir)
    stage_ts = _mark("resolve_addons_root", stage_ts)
    if isinstance(addons_root_timings, dict):
        for key, value in addons_root_timings.items():
            timings_ms[f"resolve_addons_root.{key}"] = int(value)
    registry = SceneProviderRegistry()
    stage_ts = time.perf_counter()
    _register_fallback_providers(registry, addons_root)
    stage_ts = _mark("register_fallback_providers", stage_ts)
    stage_ts = time.perf_counter()
    _register_from_modules(registry, addons_root)
    _mark("register_from_modules", stage_ts)
    for key, value in registry.timing_snapshot().items():
        timings_ms[key] = int(value)
    return registry, timings_ms


def resolve_scene_provider(scene_key: str, base_dir: Path) -> Optional[SceneContentProvider]:
    registry = build_scene_provider_registry(base_dir)
    return registry.get_provider(scene_key)


def resolve_scene_provider_with_timings(
    scene_key: str,
    base_dir: Path,
) -> Tuple[Optional[SceneContentProvider], dict[str, int]]:
    timings_ms: dict[str, int] = {}

    def _mark(stage: str, started_at: float) -> float:
        timings_ms[stage] = int((time.perf_counter() - started_at) * 1000)
        return time.perf_counter()

    stage_ts = time.perf_counter()
    registry, registry_timings = build_scene_provider_registry_with_timings(base_dir)
    stage_ts = _mark("build_scene_provider_registry", stage_ts)
    if isinstance(registry_timings, dict):
        for key, value in registry_timings.items():
            timings_ms[f"registry.{key}"] = int(value)
    stage_ts = time.perf_counter()
    provider = registry.get_provider(scene_key)
    _mark("registry_get_provider", stage_ts)
    return provider, timings_ms


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
