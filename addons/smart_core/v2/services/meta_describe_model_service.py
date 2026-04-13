from __future__ import annotations

from typing import Any, Dict

from ..contracts.results import MetaDescribeModelResultV2
from .meta_service import MetaService


class MetaDescribeModelServiceV2:
    def __init__(self) -> None:
        self._meta_service = MetaService()

    def describe(self, *, payload: Dict[str, Any], context: Dict[str, Any]) -> MetaDescribeModelResultV2:
        _ = context
        if bool((payload or {}).get("raise_handler_error")):
            raise RuntimeError("meta.describe_model handler forced error")

        model = str((payload or {}).get("model") or "").strip()
        raw = self._meta_service.describe_model_stub(model_name=model)
        capabilities = raw.get("capabilities") if isinstance(raw.get("capabilities"), dict) else {}
        fields = raw.get("fields") if isinstance(raw.get("fields"), dict) else {}

        return MetaDescribeModelResultV2(
            intent="meta.describe_model",
            model=str(raw.get("model") or model),
            display_name=str(raw.get("display_name") or model),
            fields=fields,
            can_read=bool(capabilities.get("can_read")),
            can_write=bool(capabilities.get("can_write")),
            source=str(raw.get("source") or "v2-shadow"),
            version=str(raw.get("version") or "v2"),
            schema_validated=bool((payload or {}).get("schema_validated")),
            phase="boundary_closure",
        )
