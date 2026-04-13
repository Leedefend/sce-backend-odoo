# -*- coding: utf-8 -*-

from __future__ import annotations

from dataclasses import asdict, dataclass
import ast
import importlib
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from .registry_entries import ENTRY_MODULES


@dataclass(frozen=True)
class IntentRegistryEntry:
    intent_name: str
    canonical_intent: str
    intent_class: str
    handler_class: str
    request_schema: str
    response_contract: str
    capability_code: str
    permission_mode: str
    idempotent: bool
    version: str
    tags: Tuple[str, ...]

    def as_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["tags"] = list(self.tags)
        return payload


def _normalize_entry(raw: Dict[str, Any]) -> IntentRegistryEntry:
    tags = tuple(str(item).strip() for item in (raw.get("tags") or []) if str(item).strip())
    return IntentRegistryEntry(
        intent_name=str(raw.get("intent_name") or "").strip(),
        canonical_intent=str(raw.get("canonical_intent") or raw.get("intent_name") or "").strip(),
        intent_class=str(raw.get("intent_class") or "").strip(),
        handler_class=str(raw.get("handler_class") or "").strip(),
        request_schema=str(raw.get("request_schema") or "").strip(),
        response_contract=str(raw.get("response_contract") or "").strip(),
        capability_code=str(raw.get("capability_code") or "").strip(),
        permission_mode=str(raw.get("permission_mode") or "").strip(),
        idempotent=bool(raw.get("idempotent", False)),
        version=str(raw.get("version") or "").strip(),
        tags=tags,
    )


def _iter_raw_entries() -> Iterable[Dict[str, Any]]:
    for module_path in ENTRY_MODULES:
        module = importlib.import_module(module_path)
        for row in list(getattr(module, "ENTRIES", []) or []):
            if isinstance(row, dict):
                yield row


def build_intent_registry() -> List[IntentRegistryEntry]:
    return [_normalize_entry(raw) for raw in _iter_raw_entries()]


def audit_registry_structure(entries: List[IntentRegistryEntry]) -> Dict[str, Any]:
    required_fields = [
        "intent_name",
        "canonical_intent",
        "intent_class",
        "handler_class",
        "request_schema",
        "response_contract",
        "capability_code",
        "permission_mode",
        "idempotent",
        "version",
        "tags",
    ]
    duplicates: List[str] = []
    seen = set()
    invalid_entries: List[str] = []

    for entry in entries:
        if entry.intent_name in seen:
            duplicates.append(entry.intent_name)
        seen.add(entry.intent_name)

        payload = entry.as_dict()
        missing = [field for field in required_fields if field not in payload or payload[field] in ("", None)]
        if missing:
            invalid_entries.append(f"{entry.intent_name or '<empty>'}:missing={','.join(missing)}")

    return {
        "entry_count": len(entries),
        "duplicates": sorted(set(duplicates)),
        "invalid_entries": sorted(set(invalid_entries)),
    }


def discover_handler_intents(handler_root: Path) -> List[str]:
    intents: List[str] = []
    if not handler_root.exists():
        return intents

    for path in sorted(handler_root.rglob("*.py")):
        if path.name.startswith("_"):
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Assign):
                continue
            if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
                continue
            if node.targets[0].id != "INTENT_TYPE":
                continue
            value = node.value
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                intent = value.value.strip()
                if intent and intent != "base.intent":
                    intents.append(intent)
    return sorted(set(intents))


def audit_registry_coverage(entries: List[IntentRegistryEntry], discovered_intents: List[str]) -> Dict[str, Any]:
    registered = {entry.intent_name for entry in entries}
    discovered = set(discovered_intents)
    missing_from_registry = sorted(discovered - registered)
    stale_registry_entries = sorted(registered - discovered)

    return {
        "discovered_handler_intent_count": len(discovered),
        "registered_intent_count": len(registered),
        "missing_from_registry": missing_from_registry,
        "stale_registry_entries": stale_registry_entries,
    }


ALLOWED_INTENT_CLASSES = {"system", "app", "ui", "meta", "api", "domain"}


def audit_registry_taxonomy(entries: List[IntentRegistryEntry]) -> Dict[str, Any]:
    invalid_class_entries: List[str] = []
    invalid_canonical_entries: List[str] = []

    for entry in entries:
        cls = entry.intent_class.strip().lower()
        if cls not in ALLOWED_INTENT_CLASSES:
            invalid_class_entries.append(entry.intent_name)

        canonical = entry.canonical_intent.strip()
        if not canonical:
            invalid_canonical_entries.append(f"{entry.intent_name}:empty")
            continue
        if "." not in canonical:
            invalid_canonical_entries.append(f"{entry.intent_name}:missing_prefix")
            continue
        prefix = canonical.split(".", 1)[0].strip().lower()
        if prefix not in ALLOWED_INTENT_CLASSES:
            invalid_canonical_entries.append(f"{entry.intent_name}:prefix={prefix}")

    return {
        "allowed_intent_classes": sorted(ALLOWED_INTENT_CLASSES),
        "invalid_intent_class_entries": sorted(set(invalid_class_entries)),
        "invalid_canonical_intent_entries": sorted(set(invalid_canonical_entries)),
    }
