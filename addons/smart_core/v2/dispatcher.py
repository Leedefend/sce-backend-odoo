from __future__ import annotations

from typing import Any, Dict, Optional

from .kernel.pipeline import RebuildPipelineV2
from .intents.registry import IntentRegistry, build_default_registry
from .policies.permission_policy import PermissionPolicyV2
from .validators.base import DefaultIntentValidatorV2


class IntentDispatcher:
    def __init__(self, registry: Optional[IntentRegistry] = None) -> None:
        self._registry = registry or build_default_registry()
        self._pipeline = RebuildPipelineV2(
            validator=DefaultIntentValidatorV2(),
            permission_policy=PermissionPolicyV2(),
        )

    def dispatch(self, intent: str, payload: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self._pipeline.execute(
            specs=self._registry.build_spec_map(),
            intent=intent,
            payload=payload or {},
            context=context or {},
        )


_DEFAULT_DISPATCHER = IntentDispatcher()


def dispatch_intent(intent: str, payload: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return _DEFAULT_DISPATCHER.dispatch(intent=intent, payload=payload, context=context)
