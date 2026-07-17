# smart_core/security/intent_permission.py
import odoo
from odoo import api
from odoo.http import request
from odoo.exceptions import AccessError, MissingError
from ..core.intent_operation_policy import access_mode_for_intent, nested_params
from ..core.request_identity import identity_id
from ..utils.backend_contract_boundaries import APPROVAL_POLICY_INTENTS, BUSINESS_CONFIG_INTENTS
from ..utils.extension_hooks import call_extension_hook_first
from .auth import get_user_from_token

SOURCE_KIND = "odoo_native_permission_projection"
SOURCE_AUTHORITIES = ("odoo.access", "ir.rule", "ir.ui.menu", "ir.actions", "sc.entitlement", "sc.capability")
NO_BUSINESS_FACT_AUTHORITY = True


def source_authority_contract() -> dict:
    return {
        "kind": SOURCE_KIND,
        "authorities": list(SOURCE_AUTHORITIES),
        "projection_only": True,
        "rebuildable": True,
        "no_business_fact_authority": NO_BUSINESS_FACT_AUTHORITY,
        "runtime_carrier": "intent_permission",
    }


def _find_capability(env, cap_key):
    key = str(cap_key or "").strip()
    if not key:
        return None
    try:
        Capability = env["sc.capability"].sudo()
    except Exception:
        return None
    try:
        return Capability.search([("key", "=", key)], limit=1)
    except Exception:
        return None


def _nested_params(ctx_params):
    return nested_params(ctx_params)


def _param_value(ctx_params, key, default=None):
    params = ctx_params if isinstance(ctx_params, dict) else {}
    if key in params:
        return params.get(key)
    nested = _nested_params(params)
    if isinstance(nested, dict):
        return nested.get(key, default)
    return default


def _model_acl_policy(env, *, intent_name: str, model: str, access_mode: str, params: dict) -> dict:
    try:
        payload = call_extension_hook_first(
            env,
            "smart_core_intent_permission_model_acl_policy",
            env,
            intent_name,
            model,
            access_mode,
            params if isinstance(params, dict) else {},
        )
    except Exception:
        payload = None
    return payload if isinstance(payload, dict) else {}


def _record_ids(ctx_params):
    record_id = _param_value(ctx_params, "record_id") or _param_value(ctx_params, "id")
    ids = _param_value(ctx_params, "ids")
    out = []
    if record_id not in (None, "", False):
        out.append(record_id)
    if isinstance(ids, (list, tuple, set)):
        out.extend(ids)
    elif ids not in (None, "", False):
        out.append(ids)
    normalized = []
    for value in out:
        try:
            rid = int(value)
        except Exception:
            raise MissingError(f"记录 {value} 不存在")
        if rid <= 0:
            raise MissingError(f"记录 {value} 不存在")
        if rid not in normalized:
            normalized.append(rid)
    return normalized


def _capability_key(ctx_params):
    params = ctx_params if isinstance(ctx_params, dict) else {}
    nested = _nested_params(params)
    for source in (nested, params):
        if not isinstance(source, dict):
            continue
        cap_key = source.get("capability_key") or source.get("capability") or source.get("key")
        if cap_key:
            return cap_key
    return None


def _resolve_model(env, model):
    model_name = str(model or "").strip()
    if not model_name:
        return None
    try:
        return env[model_name]
    except Exception:
        raise MissingError(f"模型 {model_name} 不存在")


def _to_int(value):
    try:
        return int(value)
    except Exception:
        return 0


def _is_synthetic_navigation_menu_id(menu_id):
    return _to_int(menu_id) >= 600_000_000


def _action_model_for_type(action_type):
    action_type = str(action_type or "").strip()
    if action_type.startswith("ir.actions."):
        return action_type
    aliases = {
        "window": "ir.actions.act_window",
        "act_window": "ir.actions.act_window",
        "client": "ir.actions.client",
        "server": "ir.actions.server",
        "url": "ir.actions.act_url",
        "report": "ir.actions.report",
    }
    return aliases.get(action_type, "")


def _menu_visible_for_user(menu, user):
    current = menu
    user_groups = getattr(user, "groups_id", None)
    while current:
        groups = getattr(current, "groups_id", None)
        if groups and user_groups is not None and not (groups & user_groups):
            return False
        parent = getattr(current, "parent_id", None)
        if not parent:
            break
        current = parent
    return True


def _resolve_action(env, action_id, action_type=None):
    action_id = _to_int(action_id)
    if action_id <= 0:
        return None
    models = []
    action_model = _action_model_for_type(action_type)
    if action_model:
        models.append(action_model)
    models.extend(["ir.actions.actions", "ir.actions.act_window"])
    seen = set()
    for model_name in models:
        if model_name in seen:
            continue
        seen.add(model_name)
        try:
            action = env[model_name].sudo().browse(action_id)
            if action.exists():
                return action
        except Exception:
            continue
    return None


def _is_ui_only_config_intent(intent_name):
    return str(intent_name or "").strip() in {
        "user.view.preference.get",
        "user.view.preference.set",
        BUSINESS_CONFIG_INTENTS["list_search_set"],
        BUSINESS_CONFIG_INTENTS["analysis_set"],
        BUSINESS_CONFIG_INTENTS["contract_save"],
        BUSINESS_CONFIG_INTENTS["contract_publish"],
        BUSINESS_CONFIG_INTENTS["contract_rollback"],
        BUSINESS_CONFIG_INTENTS["change_set_open"],
        BUSINESS_CONFIG_INTENTS["change_set_get"],
        BUSINESS_CONFIG_INTENTS["change_set_stage"],
        BUSINESS_CONFIG_INTENTS["change_set_validate"],
        BUSINESS_CONFIG_INTENTS["change_set_preview"],
        BUSINESS_CONFIG_INTENTS["change_set_publish"],
        BUSINESS_CONFIG_INTENTS["change_set_rollback"],
        BUSINESS_CONFIG_INTENTS["change_set_discard"],
        BUSINESS_CONFIG_INTENTS["mutation_audit_snapshot"],
        APPROVAL_POLICY_INTENTS["config_set"],
        APPROVAL_POLICY_INTENTS["steps_set"],
    }


def _effective_flags(Entitlement, company):
    ent = Entitlement.get_effective(company)
    if not ent:
        return {}
    flags = getattr(ent, "effective_flags_json", None)
    return flags if isinstance(flags, dict) else {}


def _sync_authenticated_identity(ctx, user):
    user_id = identity_id(user)
    request.env = request.env(user=user_id)
    env = request.env
    try:
        request.uid = user_id
    except Exception:
        pass
    try:
        ctx.env = env
        ctx.user = env.user
        ctx.uid = getattr(env, "uid", user_id)
    except Exception:
        pass
    return env


def _permission_env_for_params(env, user, ctx_params):
    target_db = str(_param_value(ctx_params, "db") or _param_value(ctx_params, "database") or "").strip()
    current_db = str(getattr(getattr(env, "cr", None), "dbname", "") or "").strip()
    user_id = identity_id(user)
    if not target_db or not current_db or target_db == current_db or not user_id:
        return env, user, None

    registry = odoo.registry(target_db)
    try:
        registry.check_signaling()
    except Exception:
        pass
    cr = registry.cursor()
    try:
        target_env = api.Environment(cr, user_id, dict(getattr(env, "context", {}) or {}))
        target_user = target_env["res.users"].browse(user_id).exists()
        if not target_user:
            raise AccessError("Token 中指定的用户不存在")
        return target_env, target_user, cr
    except Exception:
        cr.close()
        raise


def check_intent_permission(ctx):
    """
    核心权限校验入口：模型、记录、字段、菜单、动作
    :param ctx: RequestContext 封装对象
    :raises AccessError: 无权限访问模型、记录、菜单或动作
    :raises MissingError: 模型或记录不存在
    """
    

    ctx_params = ctx.params if isinstance(ctx.params, dict) else {}
    intent_name = (ctx_params.get("intent") or "").strip()
    if intent_name == "session.bootstrap":
        return True
    if intent_name == "permission.check":
        return True

    user = getattr(ctx, "user", None) or get_user_from_token()
    if not user:
        raise AccessError("Token 无效或缺少 user_id")
    # 2. 切换并同步 request/ctx 身份，避免后续跨库分发读取到 public uid。
    env = _sync_authenticated_identity(ctx, user)
    permission_cr = None
    try:
        env, permission_user, permission_cr = _permission_env_for_params(env, user, ctx_params)
        if permission_cr is not None:
            user = permission_user
            try:
                ctx.env = env
                ctx.user = user
                ctx.uid = identity_id(user)
            except Exception:
                pass

        # 3. 正常的权限检查逻辑
        model = _param_value(ctx_params, "model")
        menu_id = _param_value(ctx_params, "menu_id")
        action_id = _param_value(ctx_params, "action_id")
        action_type = _param_value(ctx_params, "action_type") or _param_value(ctx_params, "type")
        access_mode = access_mode_for_intent(intent_name, ctx_params)


        # ✅ 校验模型访问权限
        model_obj = _resolve_model(env, model) if model else None
        skip_model_acl = _is_ui_only_config_intent(intent_name)
        if model and not skip_model_acl:
            model_acl_policy = _model_acl_policy(
                env,
                intent_name=intent_name,
                model=model,
                access_mode=access_mode,
                params=ctx_params,
            )
            skip_model_acl = bool(model_acl_policy.get("skip_model_acl"))
        if model and not skip_model_acl:
            try:
                model_obj.check_access_rights(access_mode)
            except AccessError:
                raise AccessError(f"用户无权以 {access_mode} 访问模型 {model}")

        # ✅ 校验记录访问权限（如果传入 record_id/id/ids；create 无既有记录可校验）
        record_ids = _record_ids(ctx_params)
        if model and record_ids and access_mode != "create" and not skip_model_acl:
            rec = model_obj.browse(record_ids)
            existing = rec.exists()
            try:
                has_missing = len(existing) != len(record_ids)
            except Exception:
                has_missing = not bool(existing)
            if not existing or has_missing:
                raise MissingError(f"记录 {record_ids} 不存在")
            try:
                existing.check_access_rule(access_mode)
            except AccessError:
                raise AccessError(f"用户无权以 {access_mode} 访问记录 {record_ids}")

        # ✅ 校验菜单权限（如果传入 menu_id）
        if menu_id:
            normalized_menu_id = _to_int(menu_id)
            if normalized_menu_id <= 0:
                raise MissingError(f"菜单 {menu_id} 不存在")
            skip_menu_acl = _is_synthetic_navigation_menu_id(normalized_menu_id) and (
                _to_int(action_id) > 0 or bool(model)
            )
            if not skip_menu_acl:
                menu = env["ir.ui.menu"].browse(normalized_menu_id)
                if not menu.exists():
                    raise MissingError(f"菜单 {menu_id} 不存在")
                if not _menu_visible_for_user(menu, env.user):
                    raise AccessError(f"用户无权访问菜单 {menu.name}")

        # ✅ 校验动作权限（如果传入 action_id）
        if action_id:
            # 动作元数据读取使用 sudo，避免被 ir.actions.* 模型 ACL 拦截。
            # 最终授权仍基于当前用户组与动作 groups_id 交集判断。
            action = _resolve_action(env, action_id, action_type=action_type)
            if not action:
                raise MissingError(f"动作 {action_id} 不存在")
            # 集合交集判断
            groups = getattr(action, "groups_id", None)
            if groups and not (groups & env.user.groups_id):
                raise AccessError(f"用户无权执行动作 {getattr(action, 'name', action_id)}")

        # ✅ 授权/功能开关检查（若启用）
        try:
            try:
                Entitlement = env["sc.entitlement"]
            except Exception:
                Entitlement = None
            if Entitlement:
                cap_key = _capability_key(ctx_params)
                cap = _find_capability(env, cap_key)
                flags = _effective_flags(Entitlement, env.user.company_id)
                if cap and cap.required_flag:
                    if not Entitlement._flag_enabled(flags, cap.required_flag):
                        raise AccessError(f"FEATURE_DISABLED: {{'required_flag': '{cap.required_flag}', 'capability_key': '{cap.key}'}}")
            else:
                cap_key = _capability_key(ctx_params)
                cap = _find_capability(env, cap_key)
                if cap and cap.required_flag:
                    raise AccessError(f"FEATURE_DISABLED: {{'required_flag': '{cap.required_flag}', 'capability_key': '{cap.key}', 'reason': 'ENTITLEMENT_UNAVAILABLE'}}")
        except Exception:
            raise
    finally:
        if permission_cr is not None:
            permission_cr.close()

    return True
