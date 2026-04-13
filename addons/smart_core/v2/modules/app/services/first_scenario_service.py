from __future__ import annotations

from typing import Any, Dict

from ....contracts.results import FirstScenarioResultV2


class FirstScenarioServiceV2:
    def assemble(self, *, payload: Dict[str, Any], context: Dict[str, Any]) -> FirstScenarioResultV2:
        from ....dispatcher import dispatch_intent

        app_key = str((payload or {}).get("app_key") or "platform").strip() or "platform"
        model = str((payload or {}).get("model") or "").strip()
        view_type = str((payload or {}).get("view_type") or "form").strip().lower() or "form"

        base_context = {
            "user_id": int((context or {}).get("user_id") or 0),
            "company_id": int((context or {}).get("company_id") or 0),
            "trace_id": str((context or {}).get("trace_id") or ""),
        }

        session_resp = dispatch_intent(
            intent="session.bootstrap",
            payload={"app_key": app_key},
            context=base_context,
        )
        meta_resp = dispatch_intent(
            intent="meta.describe_model",
            payload={"model": model},
            context=base_context,
        )
        ui_resp = dispatch_intent(
            intent="ui.contract",
            payload={"model": model, "view_type": view_type},
            context=base_context,
        )

        chain_status = {
            "session_ok": bool(session_resp.get("ok")),
            "model_meta_ok": bool(meta_resp.get("ok")),
            "ui_contract_ok": bool(ui_resp.get("ok")),
        }
        chain_status["overall_ok"] = bool(
            chain_status["session_ok"] and chain_status["model_meta_ok"] and chain_status["ui_contract_ok"]
        )

        return FirstScenarioResultV2(
            intent="app.init",
            app_key=app_key,
            model=model,
            view_type=view_type,
            session=session_resp.get("data") if isinstance(session_resp.get("data"), dict) else {},
            model_meta=meta_resp.get("data") if isinstance(meta_resp.get("data"), dict) else {},
            ui_contract=ui_resp.get("data") if isinstance(ui_resp.get("data"), dict) else {},
            chain_status=chain_status,
            version="v2",
            source="v2-first-scenario",
        )
