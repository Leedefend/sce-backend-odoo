# smart_core/security/intent_permission.py
from odoo.http import request
from odoo.exceptions import AccessError, MissingError
from .auth import get_user_from_token,decode_token


def check_intent_permission(ctx):
    """
    核心权限校验入口：模型、记录、字段、菜单、动作
    :param ctx: RequestContext 封装对象
    :raises AccessError: 无权限访问模型、记录、菜单或动作
    :raises MissingError: 模型或记录不存在
    """
    

    user_id = get_user_from_token()
    if not user_id:
        raise AccessError("Token 无效或缺少 user_id")
    # 2. 切换 request.env 用户
    request.env = request.env(user=user_id)
    env = request.env

    # 3. 正常的权限检查逻辑
    model = ctx.params.get("model")
    record_id = ctx.params.get("record_id")
    menu_id = ctx.params.get("menu_id")
    action_id = ctx.params.get("action_id")


    # ✅ 校验模型访问权限
    if model:
        try:
            env[model].check_access_rights("read")
        except AccessError:
            raise AccessError(f"用户无权访问模型 {model}")

    # ✅ 校验记录访问权限（如果传入 record_id）
    if model and record_id:
        rec = env[model].browse(int(record_id))
        if not rec.exists():
            raise MissingError(f"记录 {record_id} 不存在")
        try:
            rec.check_access_rule("read")
        except AccessError:
            raise AccessError(f"用户无权读取记录 {record_id}")

    # ✅ 校验菜单权限（如果传入 menu_id）
    if menu_id:
        menu = env["ir.ui.menu"].browse(int(menu_id))
        if not menu.exists():
            raise MissingError(f"菜单 {menu_id} 不存在")
        if not menu._is_visible():
            raise AccessError(f"用户无权访问菜单 {menu.name}")

    # ✅ 校验动作权限（如果传入 action_id）
    if action_id:
        action = env["ir.actions.act_window"].browse(int(action_id))
        if not action.exists():
            raise MissingError(f"动作 {action_id} 不存在")
        # 集合交集判断
        if action.groups_id and not (action.groups_id & env.user.groups_id):
            raise AccessError(f"用户无权执行动作 {action.name}")

    # ✅ 授权/功能开关检查（若启用）
    try:
        Entitlement = env.get("sc.entitlement")
        if Entitlement:
            params = ctx.params.get("params") or {}
            cap_key = params.get("capability_key") or params.get("capability") or params.get("key")
            cap = None
            if cap_key:
                cap = env["sc.capability"].sudo().search([("key", "=", cap_key)], limit=1)
            plan = Entitlement._resolve_plan(env.user.company_id) if Entitlement else None
            flags = plan.feature_flags_json or {} if plan else {}
            if cap and cap.required_flag:
                if not Entitlement._flag_enabled(flags, cap.required_flag):
                    raise AccessError(f"FEATURE_DISABLED: {{'required_flag': '{cap.required_flag}', 'capability_key': '{cap.key}'}}")
    except Exception:
        raise

    return True
