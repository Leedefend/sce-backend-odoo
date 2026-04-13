from __future__ import annotations

from ..contracts.results import SessionBootstrapResultV2


class SessionBootstrapResponseBuilderV2:
    def build(self, result: SessionBootstrapResultV2) -> dict:
        return {
            "intent": str(result.intent or "session.bootstrap"),
            "session_status": str(result.session_status or "ready"),
            "bootstrap_ready": bool(result.bootstrap_ready),
            "schema_validated": bool(result.schema_validated),
            "app_key": str(result.app_key or "platform"),
            "user_id": int(result.user_id or 0),
            "company_id": int(result.company_id or 0),
            "trace_id": str(result.trace_id or ""),
            "registry_count": int(result.registry_count or 0),
            "phase": str(result.phase or "boundary_closure"),
            "version": str(result.version or "v2"),
        }


def build_session_bootstrap_response(result: SessionBootstrapResultV2) -> dict:
    return SessionBootstrapResponseBuilderV2().build(result)
