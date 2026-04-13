from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SessionBootstrapResultV2:
    intent: str
    session_status: str
    bootstrap_ready: bool
    schema_validated: bool
    app_key: str
    user_id: int
    company_id: int
    trace_id: str
    registry_count: int
    phase: str
    version: str
