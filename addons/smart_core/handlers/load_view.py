# 📁 smart_core/handlers/load_view.py
from odoo.exceptions import AccessError, MissingError, UserError

from ..core.base_handler import BaseIntentHandler
from ..view.universal_parser import UniversalViewSemanticParser


class LoadModelViewHandler(BaseIntentHandler):
    INTENT_TYPE = "load_view"
    DESCRIPTION = "加载模型视图结构"
    _SYSTEM_MODEL_BLOCKLIST = {
        "ir.ui.view",
        "ir.model",
        "ir.model.fields",
        "ir.model.access",
        "ir.rule",
        "ir.actions.actions",
        "ir.actions.act_window",
        "ir.ui.menu",
        "ir.config_parameter",
        "res.users",
        "res.groups",
    }

    def _is_system_admin(self) -> bool:
        try:
            return bool(self.env.user.has_group("base.group_system"))
        except Exception:
            return False

    def _parse_view_id(self, raw):
        if raw in (None, "", False):
            return None
        return int(raw)

    def _resolve_target_view_id(self, *, model_name: str, view_type: str, requested_view_id):
        view_id = self._parse_view_id(requested_view_id)
        view_model = self.su_env["ir.ui.view"]
        if view_id:
            view = view_model.browse(view_id)
            if not view.exists():
                raise MissingError(f"未找到视图: {view_id}")
            if view.model and view.model != model_name:
                raise UserError(f"视图 {view_id} 不属于模型 {model_name}")
            if view.type and view.type != view_type:
                raise UserError(f"视图 {view_id} 类型 {view.type} 与请求 {view_type} 不一致")
            return int(view.id)

        default_view = view_model.search([("model", "=", model_name), ("type", "=", view_type)], limit=1)
        if not default_view:
            raise MissingError(f"未找到模型 {model_name} 的 {view_type} 视图")
        return int(default_view.id)

    def run(self, **_kwargs):
        model_name = str(self.params.get("model") or "").strip()
        view_type = str(self.params.get("view_type") or "").strip()
        requested_view_id = self.params.get("view_id")

        if not model_name or not view_type:
            return {
                "ok": False,
                "error": {"code": "BAD_REQUEST", "message": "缺少必要参数 model 或 view_type"},
                "code": 400,
            }
        # 系统模型只允许系统管理员读取，业务角色统一走受控意图输出。
        if model_name in self._SYSTEM_MODEL_BLOCKLIST and not self._is_system_admin():
            return {
                "ok": False,
                "error": {"code": "PERMISSION_DENIED", "message": "不允许直接读取系统模型视图"},
                "code": 403,
            }

        try:
            model_user = self.env[model_name].with_context(self.params)
            # 业务访问权限先由当前用户口径校验，避免无约束 sudo 泄露。
            model_user.check_access_rights("read", raise_exception=True)

            target_view_id = self._resolve_target_view_id(
                model_name=model_name,
                view_type=view_type,
                requested_view_id=requested_view_id,
            )

            # 受控 sudo：仅在模型访问通过后，用超级用户读取视图定义。
            self.su_env[model_name].with_context(self.params).get_view(
                view_id=target_view_id,
                view_type=view_type,
            )

            parser = UniversalViewSemanticParser(
                self.su_env,
                model=model_name,
                view_type=view_type,
                view_id=target_view_id,
                context=self.params,
                permission_env=self.env,
            )
            result = parser.parse()
            result["view_id"] = target_view_id
            return {"ok": True, "data": result}
        except AccessError as e:
            return {
                "ok": False,
                "error": {"code": "PERMISSION_DENIED", "message": str(e)},
                "code": 403,
            }
        except (MissingError, KeyError) as e:
            return {
                "ok": False,
                "error": {"code": "INTENT_NOT_FOUND", "message": str(e)},
                "code": 404,
            }
        except UserError as e:
            return {
                "ok": False,
                "error": {"code": "BAD_REQUEST", "message": str(e)},
                "code": 400,
            }
        except ValueError as e:
            return {
                "ok": False,
                "error": {"code": "BAD_REQUEST", "message": str(e)},
                "code": 400,
            }
        except Exception as e:
            return {
                "ok": False,
                "error": {"code": "INTERNAL_ERROR", "message": str(e)},
                "code": 500,
            }
