# smart_core/security/intent_permission.py
import re

from odoo.http import request
from odoo.exceptions import AccessError, MissingError
from .auth import get_user_from_token

SOURCE_KIND = "odoo_native_permission_projection"
SOURCE_AUTHORITIES = ("odoo.access", "ir.rule", "ir.ui.menu", "ir.actions", "sc.entitlement", "sc.capability")
NO_BUSINESS_FACT_AUTHORITY = True
_WRITE_INTENT_RE = re.compile(
    r"(write|update|set|execute|upload|cancel|approve|reject|submit|done|import|rollback|pin)",
    re.IGNORECASE,
)


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
    params = ctx_params if isinstance(ctx_params, dict) else {}
    nested = params.get("params")
    if isinstance(nested, dict):
        return nested
    payload = params.get("payload")
    if isinstance(payload, dict):
        return payload
    return params


def _param_value(ctx_params, key, default=None):
    params = ctx_params if isinstance(ctx_params, dict) else {}
    if key in params:
        return params.get(key)
    nested = _nested_params(params)
    if isinstance(nested, dict):
        return nested.get(key, default)
    return default


def _intent_operation(intent_name, ctx_params):
    intent = str(intent_name or "").strip().lower()
    params = _nested_params(ctx_params)
    op = str((params or {}).get("op") or "").strip().lower()
    action = str((params or {}).get("action") or "").strip().lower()

    if intent == "api.data":
        return op or "read"
    if intent == "api.data.batch":
        if action:
            return action
        if op:
            return op
        if isinstance(params, dict) and (params.get("vals") or params.get("values")):
            return "write"
        return "batch"
    if intent.startswith("api.data."):
        suffix = intent.split(".", 2)[-1].strip().lower()
        return suffix or op or "read"
    if op:
        return op
    if "create" in intent:
        return "create"
    if "unlink" in intent or "delete" in intent:
        return "unlink"
    if _WRITE_INTENT_RE.search(intent):
        return "write"
    return "read"


def _access_mode_for_operation(operation):
    op = str(operation or "").strip().lower()
    if op in {"create", "new"}:
        return "create"
    if op in {"write", "update", "set", "archive", "activate", "assign", "unarchive", "batch.write", "batch.update"}:
        return "write"
    if op in {"unlink", "delete", "remove", "batch.unlink", "batch.delete"}:
        return "unlink"
    return "read"


def _record_ids(ctx_params):
    record_id = _param_value(ctx_params, "record_id") or _param_value(ctx_params, "id")
    ids = _param_value(ctx_params, "ids")
    out = []
    if record_id:
        out.append(record_id)
    if isinstance(ids, (list, tuple, set)):
        out.extend(ids)
    elif ids:
        out.append(ids)
    normalized = []
    for value in out:
        try:
            rid = int(value)
        except Exception:
            continue
        if rid and rid not in normalized:
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

    user_id = get_user_from_token()
    if not user_id:
        raise AccessError("Token 无效或缺少 user_id")
    # 2. 切换 request.env 用户
    request.env = request.env(user=user_id)
    env = request.env

    # 3. 正常的权限检查逻辑
    model = _param_value(ctx_params, "model")
    menu_id = _param_value(ctx_params, "menu_id")
    action_id = _param_value(ctx_params, "action_id")
    operation = _intent_operation(intent_name, ctx_params)
    access_mode = _access_mode_for_operation(operation)


    # ✅ 校验模型访问权限
    if model:
        try:
            env[model].check_access_rights(access_mode)
        except AccessError:
            raise AccessError(f"用户无权以 {access_mode} 访问模型 {model}")

    # ✅ 校验记录访问权限（如果传入 record_id/id/ids；create 无既有记录可校验）
    record_ids = _record_ids(ctx_params)
    if model and record_ids and access_mode != "create":
        rec = env[model].browse(record_ids)
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
        menu = env["ir.ui.menu"].browse(int(menu_id))
        if not menu.exists():
            raise MissingError(f"菜单 {menu_id} 不存在")
        if not menu._is_visible():
            raise AccessError(f"用户无权访问菜单 {menu.name}")

    # ✅ 校验动作权限（如果传入 action_id）
    if action_id:
        # 动作元数据读取使用 sudo，避免被 ir.actions.* 模型 ACL 拦截。
        # 最终授权仍基于当前用户组与动作 groups_id 交集判断。
        action = env["ir.actions.act_window"].sudo().browse(int(action_id))
        if not action.exists():
            raise MissingError(f"动作 {action_id} 不存在")
        # 集合交集判断
        if action.groups_id and not (action.groups_id & env.user.groups_id):
            raise AccessError(f"用户无权执行动作 {action.name}")

    # ✅ 授权/功能开关检查（若启用）
    try:
        try:
            Entitlement = env["sc.entitlement"]
        except Exception:
            Entitlement = None
        if Entitlement:
            cap_key = _capability_key(ctx_params)
            cap = _find_capability(env, cap_key)
            ent = Entitlement.get_effective(env.user.company_id)
            flags = ent.effective_flags_json or {}
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

    return True
