# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
from typing import Any, Dict, Iterable, List, Tuple

_logger = logging.getLogger(__name__)


IntentContribution = Dict[str, Any]


def _normalize_intent(intent: Any) -> str:
    return str(intent or "").strip()


def _safe_list(raw: Any) -> List[Any]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return raw
    if isinstance(raw, tuple):
        return list(raw)
    return []


def validate_contributions(
    module_name: str,
    raw_contributions: Any,
) -> Tuple[List[IntentContribution], List[str]]:
    """
    Validate module-supplied intent handler contributions.
    Required keys: intent, handler.
    Optional keys: source_module, domain, status.
    """
    contributions: List[IntentContribution] = []
    errors: List[str] = []
    rows = _safe_list(raw_contributions)
    if not rows:
        return contributions, errors

    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            errors.append(f"{module_name}[{index}] must be dict")
            continue

        intent = _normalize_intent(row.get("intent"))
        handler = row.get("handler")

        if not intent:
            errors.append(f"{module_name}[{index}] missing intent")
            continue
        if handler is None:
            errors.append(f"{module_name}[{index}] missing handler")
            continue

        contributions.append(
            {
                "intent": intent,
                "handler": handler,
                "source_module": row.get("source_module") or module_name,
                "domain": row.get("domain") or "unknown",
                "status": row.get("status") or "active",
            }
        )
    return contributions, errors


def merge_contributions(
    batches: Iterable[IntentContribution],
) -> Tuple[List[IntentContribution], List[str]]:
    """
    Merge by intent key, reject duplicate ownership in extension layer.
    """
    merged: List[IntentContribution] = []
    errors: List[str] = []
    seen: Dict[str, IntentContribution] = {}

    for item in batches:
        intent = _normalize_intent(item.get("intent"))
        if not intent:
            continue
        if intent in seen:
            prev = seen[intent]
            errors.append(
                "duplicate intent contribution: "
                f"{intent} ({prev.get('source_module')} vs {item.get('source_module')})"
            )
            continue
        seen[intent] = item
        merged.append(item)

    return merged, errors


def final_register_contributions(
    registry: Dict[str, Any],
    contributions: Iterable[IntentContribution],
) -> Dict[str, int]:
    """
    Final register is platform-owned: write merged contributions into registry.
    Existing core registry keys are not overridden.
    """
    added = 0
    skipped_existing = 0

    for row in contributions:
        intent = _normalize_intent(row.get("intent"))
        handler = row.get("handler")
        if not intent or handler is None:
            continue

        if intent in registry:
            skipped_existing += 1
            _logger.warning(
                "[intent_contrib] skip existing intent=%s source=%s",
                intent,
                row.get("source_module"),
            )
            continue

        registry[intent] = handler
        added += 1

    return {
        "added": added,
        "skipped_existing": skipped_existing,
    }

