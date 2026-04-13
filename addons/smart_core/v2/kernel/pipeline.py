from __future__ import annotations

import importlib
from time import perf_counter
from typing import Any, Dict, Mapping

from ..contracts.envelope import make_envelope
from ..handlers.base import HandlerContextV2
from ..reasons import (
    REASON_DISPATCH_FAILED,
    REASON_INTENT_NOT_FOUND,
    REASON_PERMISSION_DENIED,
    REASON_VALIDATION_FAILED,
    build_error,
)


class RebuildPipelineV2:
    def __init__(self, *, validator, permission_policy) -> None:
        self._validator = validator
        self._permission_policy = permission_policy

    def execute(self, *, specs: Mapping[str, Any], intent: str, payload: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        started_at = perf_counter()
        trace_id = str((context or {}).get("trace_id") or "")
        try:
            self._validator.validate(intent, payload, context)
            spec = specs.get(intent)
            if spec is None:
                return make_envelope(
                    ok=False,
                    intent=intent,
                    error=build_error(REASON_INTENT_NOT_FOUND, f"intent not registered: {intent}"),
                    trace_id=trace_id,
                    contract_version="v2",
                    schema_version="v1",
                    started_at=started_at,
                )

            allowed, reason = self._permission_policy.authorize(
                intent=intent,
                permission_mode=getattr(spec, "permission_mode", "public"),
                context=context,
            )
            if not allowed:
                return make_envelope(
                    ok=False,
                    intent=intent,
                    error=build_error(REASON_PERMISSION_DENIED, reason),
                    trace_id=trace_id,
                    contract_version="v2",
                    schema_version="v1",
                    started_at=started_at,
                )

            normalized_payload = self._apply_request_schema(
                request_schema=getattr(spec, "request_schema", ""),
                payload=payload or {},
                context=context,
            )

            handler = spec.handler_factory()
            handler_ctx = HandlerContextV2(
                trace_id=trace_id,
                user_id=int((context or {}).get("user_id") or 0),
                company_id=int((context or {}).get("company_id") or 0),
                registry_snapshot=tuple(sorted(specs.keys())),
                registry_entries=dict(specs),
            )
            data = handler.run(normalized_payload, handler_ctx)
            return make_envelope(
                ok=True,
                intent=intent,
                data=data,
                trace_id=trace_id,
                contract_version="v2",
                schema_version="v1",
                started_at=started_at,
            )
        except ValueError as error:
            return make_envelope(
                ok=False,
                intent=intent,
                error=build_error(REASON_VALIDATION_FAILED, str(error)),
                trace_id=trace_id,
                contract_version="v2",
                schema_version="v1",
                started_at=started_at,
            )
        except Exception as error:
            return make_envelope(
                ok=False,
                intent=intent,
                error=build_error(REASON_DISPATCH_FAILED, str(error)),
                trace_id=trace_id,
                contract_version="v2",
                schema_version="v1",
                started_at=started_at,
            )

    def _apply_request_schema(self, *, request_schema: str, payload: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        schema_path = str(request_schema or "").strip()
        if not schema_path or "." not in schema_path:
            return payload

        module_name, _, class_name = schema_path.rpartition(".")
        if not module_name or not class_name:
            return payload

        if module_name.startswith("v2.") and class_name.startswith("v") and class_name[1:].isdigit():
            return payload

        importable_prefixes = (
            "odoo.addons.",
            "addons.",
            "smart_core.",
        )
        if not module_name.startswith(importable_prefixes):
            return payload

        module = None
        candidate_module_names = [module_name]
        if module_name.startswith("addons.smart_core."):
            candidate_module_names.append(
                module_name.replace("addons.smart_core.", "odoo.addons.smart_core.", 1)
            )
            candidate_module_names.append(
                module_name.replace("addons.smart_core.", "smart_core.", 1)
            )
            candidate_module_names.append(
                module_name.replace("addons.smart_core.", "", 1)
            )

        import_error = None
        for candidate in candidate_module_names:
            try:
                module = importlib.import_module(candidate)
                break
            except Exception as error:
                import_error = error
                continue

        if module is None:
            raise import_error if import_error else ImportError(module_name)

        schema_cls = getattr(module, class_name)
        validate = getattr(schema_cls, "validate")
        try:
            normalized = validate(payload, context)
        except TypeError:
            normalized = validate(payload)
        if not isinstance(normalized, dict):
            raise ValueError("schema validate must return dict")
        return normalized
