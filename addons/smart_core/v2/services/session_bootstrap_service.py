from __future__ import annotations

from typing import Any, Dict

from ..contracts.results import SessionBootstrapResultV2


class SessionBootstrapServiceV2:
    def bootstrap(self, *, payload: Dict[str, Any], context: Dict[str, Any]) -> SessionBootstrapResultV2:
        if bool((payload or {}).get("raise_handler_error")):
            raise RuntimeError("session.bootstrap handler forced error")

        app_key = str((payload or {}).get("app_key") or "platform").strip() or "platform"
        registry_snapshot = context.get("registry_snapshot")
        if not isinstance(registry_snapshot, tuple):
            registry_snapshot = tuple(registry_snapshot or ())

        return SessionBootstrapResultV2(
            intent="session.bootstrap",
            session_status="ready",
            bootstrap_ready=True,
            schema_validated=bool((payload or {}).get("schema_validated")),
            app_key=app_key,
            user_id=int((context or {}).get("user_id") or 0),
            company_id=int((context or {}).get("company_id") or 0),
            trace_id=str((context or {}).get("trace_id") or ""),
            registry_count=len(registry_snapshot),
            phase="boundary_closure",
            version="v2",
        )
