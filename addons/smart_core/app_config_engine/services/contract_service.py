# -*- coding: utf-8 -*-
"""
smart_core/app_config_engine/services/contract_service.py
【职责】统一接口服务入口：
  1) 读取 JSON Body、If-None-Match（ETag）；
  2) 解析/规范化 payload；
  3) 根据 subject 分发到对应 Dispatcher；
  4) 计算 ETag、命中 304、拼装 meta；
  5) 返回响应三件套：status/headers/body

相对原版的关键改动：
- 修正 3.x 统一化后处理的缩进，确保 finalize_contract 一定执行。
- 合并视图内按钮（form.header_buttons/stat_buttons/button_box）到顶层 buttons，并去重。
- statusbar 在字段为 state 且 states 为空时，从 fields.state.selection 兜底构造。
- 去除 _norm_str 重复定义，仅保留一个静态方法版本。
"""
import re
from copy import deepcopy
import ast
from odoo.tools.safe_eval import safe_eval
import json, time, logging
from odoo.http import request
from odoo import api, SUPERUSER_ID
from typing import Tuple
from odoo.addons.smart_core.app_config_engine.utils.http import read_json_body
from odoo.addons.smart_core.app_config_engine.utils.payload import parse_payload
from odoo.addons.smart_core.app_config_engine.utils.misc import stable_etag, format_versions
from odoo.addons.smart_core.app_config_engine.services.dispatchers.nav_dispatcher import NavDispatcher
from odoo.addons.smart_core.app_config_engine.services.dispatchers.menu_dispatcher import MenuDispatcher
from odoo.addons.smart_core.app_config_engine.services.dispatchers.action_dispatcher import ActionDispatcher
from odoo.addons.smart_core.core.trace import get_trace_id
from odoo.addons.smart_core.core.exceptions import (
    BAD_REQUEST,
    VALIDATION_ERROR,
    INTERNAL_ERROR,
    DEFAULT_API_VERSION,
    DEFAULT_CONTRACT_VERSION,
    build_error_envelope,
)

_logger = logging.getLogger(__name__)


class ContractService:
    def __init__(self, request_env):
        # 当前用户环境（保留权限语义）
        self.env = request_env
        # 超级权限环境（用于读取配置/菜单元数据，避免 ACL 限制导致元数据拿不到）
        self.su_env = api.Environment(self.env.cr, SUPERUSER_ID, dict(self.env.context or {}))

    def handle_request(self) -> Tuple[bool, int, list, bytes]:
        """
        主处理流程：返回 (ok, status, headers, body)
        - ok: 逻辑成功标志，这里仅用于内部诊断（控制器不使用）
        - status: HTTP 状态码（含 304 命中）
        - headers: 响应头（含 ETag）
        - body: 二进制 JSON
        """
        ts0 = time.time()
        trace_id = get_trace_id(request.httprequest.headers)

        def _err(status: int, code: str, message: str, details: dict | None = None):
            body = build_error_envelope(
                code=code,
                message=message,
                trace_id=trace_id,
                details=details,
                api_version=DEFAULT_API_VERSION,
                contract_version=DEFAULT_CONTRACT_VERSION,
            )
            headers = [
                ("Content-Type", "application/json; charset=utf-8"),
                ("X-Trace-Id", trace_id),
            ]
            return False, status, headers, json.dumps(body, ensure_ascii=False).encode("utf-8")

        # 1) 读取 body 与请求头
        payload = read_json_body()
        client_etag = request.httprequest.headers.get('If-None-Match')
        _logger.warning("CONTRACT_REQUEST payload=%s headers=%s", payload, dict(request.httprequest.headers))

        # 2) 解析/规范化 payload（强约束字段、兜底默认值）
        p = parse_payload(payload)
        _logger.warning("CONTRACT_PARSED_PAYLOAD %s", p)

        # 3) 根据 subject 分发
        subject = p.get('subject')
        data, versions = {}, {}

        if subject == 'nav':
            data, versions = NavDispatcher(self.env, self.su_env).build_nav(p)
        elif subject == 'menu':
            data, versions = MenuDispatcher(self.env, self.su_env).open_menu(p)
        elif subject in ('action', 'model', 'operation'):
            data, versions = ActionDispatcher(self.env, self.su_env).dispatch(p)
        else:
            return _err(400, BAD_REQUEST, "不支持的 subject", {"subject": subject})

        # 3.x) 统一化后处理（关键嵌点）
        # -----------------------------------------
        # finalize_contract 期望传入“完整返回体”，所以这里包一个最小壳：
        #   { "ok": True, "data": <分发产出的 data>, "meta": { "subject": ... } }
        # 统一化会在 data 下修正 views/buttons/search/workflow/permissions 等。
        # 若开启了自检（_self_check_strict），发现问题会抛 AssertionError。
        try:
            _contract_min = {"ok": True, "data": data, "meta": {"subject": subject, "version": format_versions(versions)}}
            _contract_fixed = self.finalize_contract(_contract_min)
            # 用修复后的 data 覆盖
            data = _contract_fixed.get("data", data)
        except AssertionError as ae:
            # 统一化自检失败：返回 422，方便开发期快速定位脏数据/不一致
            _logger.exception("contract finalize self-check failed")
            return _err(422, VALIDATION_ERROR, "contract_self_check_failed", {"detail": str(ae)})
        # -----------------------------------------

        # 4) 计算 ETag，支持 304
        etag = stable_etag(data)
        # 约定：with_data=True 时不缓存（避免列表数据频繁变化造成误判）
        skip_cache = bool(p.get("with_data"))
        if not skip_cache and client_etag and client_etag == etag:
            # 命中 304：只回 ETag，body 为空
            return True, 304, [("ETag", etag), ("X-Trace-Id", trace_id)], b''

        # 5) 拼装 meta，包含版本/耗时等
        elapsed = int((time.time() - ts0) * 1000)
        meta = {
            "subject": subject,
            "version": format_versions(versions),  # "model:12|view:34|..."
            "etag": etag,
            "ts": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            "elapsed_ms": elapsed,
            "trace_id": trace_id,
            "api_version": DEFAULT_API_VERSION,
            "contract_version": DEFAULT_CONTRACT_VERSION,
        }

        # 6) 返回成功响应
        body = json.dumps({"ok": True, "data": data, "meta": meta}, ensure_ascii=False, default=str).encode('utf-8')
        return True, 200, [
            ('Content-Type','application/json; charset=utf-8'),
            ('ETag', etag),
            ("X-Trace-Id", trace_id),
        ], body

    # =========================
    # 对外唯一需要调用的入口
    # =========================
    def finalize_contract(self, contract):
        """
        统一化后处理入口：
        - 输入：contract（dict），为你原先已经组装好的完整返回体
        - 输出：返回同结构的“修正版”contract
        """
        data = deepcopy(contract)  # 深拷贝，避免原地副作用

        # 0) 先把视图内按钮汇总到顶层，便于统一清洗/权限处理
        self._merge_view_buttons_to_top(data)

        # 1) 对齐表单状态栏字段（form.statusbar.field）
        self._fix_form_statusbar_field(data)

        # 1.x)（可选兜底）为 statusbar.states 提供 selection 值（仅 state 字段）
        self._fill_statusbar_states_from_selection(data)

        # 2) 清理非法/占位的 object 按钮
        self._cleanup_object_buttons(data)

        # 3) 统一搜索过滤器 key 命名（全部转 snake_case）
        self._normalize_search_filter_keys(data)

        # 4) 尝试把 domain_raw 解析为结构化 domain（能解析的才解析）
        self._unify_domains_from_raw(data)

        # 5) 约束“永真”权限子句，仅对项目经理组生效（或删除）
        self._sanitize_permissions(data)

        # 6) 处理不被契约支持的 groups_xmlids 取非（"!" 前缀）
        self._strip_negative_groups_syntax(data)

        # 7) （可选）开发态自检——发现问题直接抛错，避免脏数据流出
        self._self_check_strict(data)

        return data

    # =========================
    # 具体修复实现
    # =========================
    def _merge_view_buttons_to_top(self, data):
        try:
            root = data.get("data") or {}
            views = root.get("views") or {}
            form = views.get("form") or {}
            header_buttons = form.get("header_buttons") or []
            # 兼容两种命名
            stat_buttons = form.get("stat_buttons") or form.get("button_box") or []
            top_buttons = root.get("buttons") or []

            def _key(b):
                if not isinstance(b, dict): 
                    return None
                p = (b.get("payload") or {})
                # 语义主键：不含 label，确保真正相同的动作被折叠
                ident = p.get("method") or p.get("ref") or p.get("url") or ""
                return (b.get("kind"), b.get("level"), ident)


            merged = {}
            for b in (top_buttons + header_buttons + stat_buttons):
                if not isinstance(b, dict):
                    continue
                merged[_key(b)] = b
            root["buttons"] = list(merged.values())
            data["data"] = root
        except Exception:
            pass

    def _fix_form_statusbar_field(self, data):
        """
        目的：消除 form.statusbar.field 与实际可用字段不一致的问题
        策略：
          - 如果 form.statusbar.field 不在 fields 集合里，则优先用 workflow.state_field
          - 如果 workflow.state_field 也不存在，则尝试回落到 'stage_id' 或删除 statusbar
        """
        try:
            views = data['data']['views']
            fields = data['data']['fields']
            workflow = data['data'].get('workflow', {})
            form = views.get('form', {})
            statusbar = form.get('statusbar', {})

            sb_field = statusbar.get('field')
            if not sb_field or sb_field not in fields:
                # 优先用 workflow.state_field
                wf_field = workflow.get('state_field')
                if wf_field and wf_field in fields:
                    statusbar['field'] = wf_field
                elif 'stage_id' in fields:
                    statusbar['field'] = 'stage_id'
                else:
                    # 实在没有可用的状态字段，移除 statusbar 避免前端报错
                    form.pop('statusbar', None)

            # 回写
            views['form'] = form
            data['data']['views'] = views
        except Exception:
            # 容错：任何异常不影响主流程
            pass

    def _fill_statusbar_states_from_selection(self, data):
        """当 statusbar.field == 'state' 且 states 为空时，从 fields.state.selection 构造 states。"""
        try:
            fields = (data.get("data") or {}).get("fields") or {}
            form = (data.get("data") or {}).get("views", {}).get("form", {}) or {}
            sb = form.get("statusbar") or {}
            if sb.get("field") == "state" and not (sb.get("states") or []):
                sel = (fields.get("state") or {}).get("selection") or []
                sb["states"] = [{"value": v, "label": lbl} for v, lbl in sel if isinstance(v, (str, int))]
                form["statusbar"] = sb
                data["data"]["views"]["form"] = form
        except Exception:
            pass

    def _cleanup_object_buttons(self, data):
        """
        目的：移除/修正空方法或空标签的对象按钮（kind == 'object'）
        规则：
          - method 为空的一律移除
          - label 为空：若 method 存在，则用 method 作为兜底 label
        """
        try:
            buttons = data['data'].get('buttons', [])
            cleaned = []
            for btn in buttons:
                if not isinstance(btn, dict):
                    continue
                kind = btn.get('kind')
                payload = btn.get('payload') or {}
                method = (payload.get('method') or '').strip() if isinstance(payload.get('method'), str) else payload.get('method')
                label = (btn.get('label') or '').strip()

                if kind == 'object':
                    # 对象按钮必须有方法名
                    if not method:
                        continue  # 丢弃此按钮
                    # 标签兜底：如果 label 为空，用 method 名顶上，避免前端显示空白
                    if not label:
                        btn['label'] = str(method)
                cleaned.append(btn)

            data['data']['buttons'] = cleaned
        except Exception:
            pass

    def _normalize_search_filter_keys(self, data):
        """
        目的：统一搜索过滤器 key 为 snake_case，避免大小写/空格导致路由或缓存不一致
        例：'Manager' -> 'manager'， 'My Projects' -> 'my_projects'
        """
        try:
            filters_ = data['data']['search'].get('filters', [])
            for f in filters_:
                key = f.get('key')
                if not key:
                    continue
                snake = self._to_snake_case(key)
                f['key'] = snake
        except Exception:
            pass

    @staticmethod
    def _to_snake_case(s):
        """
        把任意字符串转为 snake_case：
        - 先把空白/连接符替换为下划线
        - 再把驼峰切分为下划线
        """
        s = re.sub(r'[\s\-]+', '_', str(s).strip())
        s = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', s)         # AbcX -> Abc_X
        s = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', s)         # abcX -> abc_X
        s = re.sub(r'_+', '_', s).lower()
        return s

    def _unify_domains_from_raw(self, data):
        """
        目的：把能安全解析的 domain_raw（字符串）转换为结构化的 domain（列表）
        安全策略：
          - 仅在 domain 为空且 domain_raw 看起来像一个 Python 列表字面量时尝试解析
          - 如果包含明显不可在此处安全解析的符号（如 context_today(), user.等），则跳过
        """
        try:
            filters_ = data['data']['search'].get('filters', [])
            for f in filters_:
                dom = f.get('domain')
                dom_raw = f.get('domain_raw')

                if (not dom) and isinstance(dom_raw, str) and dom_raw.strip().startswith('['):
                    raw = dom_raw.strip()

                    # 粗略过滤：遇到明显依赖上下文/用户函数的，先别解析，避免报错
                    if any(x in raw for x in ('context_today', 'user.', 'uid', 'company_id', 'res_model')):
                        continue

                    try:
                        parsed = safe_eval(raw, {})  # 不提供上下文，限制解析能力，保证安全
                        if isinstance(parsed, list):
                            f['domain'] = parsed
                    except Exception:
                        pass
        except Exception:
            pass

    def _sanitize_permissions(self, data):
        """
        目的：约束权限规则中“永真域”[(1,'=',1)]，避免误放权
        策略：
        - 若检测到该子句，则仅对项目经理组生效（groups_xmlids += project.group_project_manager）
        - 同时取消 global 放开（global=False）
        - 不依赖 group id 映射，避免跨库/环境差异
        - 兼容 data 或 {"data": data} 两种包装
        """
        try:
            # 兼容顶层/包裹两种结构
            root = data.get('data') if isinstance(data, dict) and 'data' in data else data
            if not isinstance(root, dict):
                return

            perms = (root.get('permissions') or {})
            rules = (perms.get('rules') or {})

            changed = False

            for op in ('read', 'write', 'create', 'unlink'):
                block = rules.get(op) or {}
                clauses = block.get('clauses') or []
                for c in clauses:
                    dom = c.get('domain', [])
                    raw = (c.get('domain_raw') or '').strip()
                    if self._domain_is_tautology(dom, raw):
                        # 绑定到项目经理组
                        xmlids = set(c.get('groups_xmlids') or [])
                        xmlids.add('project.group_project_manager')
                        c['groups_xmlids'] = sorted(xmlids)

                        # 取消全局放开
                        if c.get('global') is True:
                            c['global'] = False

                        changed = True

            if changed:
                _logger.info("SANITIZE_PERMS: 永真域已限制到项目经理组并取消 global。")

        except Exception:
            _logger.exception("SANITIZE_PERMS: 处理权限时发生异常（已忽略以不中断流程）")

    def _safe_literal_eval(self, s: str):
        """对 domain_raw 做安全解析；解析失败返回 None"""
        try:
            return ast.literal_eval(s)
        except Exception:
            return None

    def _domain_is_tautology(self, dom, raw):
        """
        识别“恒真域”，用于在权限/规则展示时省略无意义的域：
        - [] 或 [(1, '=', 1)]
        同时兼容 raw 是字符串的情况。
        """
        # 1) 结构化优先
        try:
            if isinstance(dom, (list, tuple)):
                if dom == []:
                    return True
                if len(dom) == 1 and isinstance(dom[0], (list, tuple)) and len(dom[0]) == 3:
                    l, op, r = dom[0]
                    if (op in ("=", "==")) and (l in (1, True)) and (r in (1, True)):
                        return True
        except Exception:
            pass

        # 2) 若给了 raw，尝试解析后复用本函数判断
        if raw:
            try:
                v = self._safe_literal_eval(raw)
                if isinstance(v, (list, tuple)):
                    return self._domain_is_tautology(v, None)
            except Exception:
                pass

        # 3) 字符串兜底
        s = self._norm_str(raw or "")
        if s in ("[]", "[(1,'=',1)]", "[(1,'==',1)]"):
            return True
        return False

    def _strip_negative_groups_syntax(self, data):
        """
        目的：去除 groups_xmlids 中非标准取非语法（'!group.xmlid'）
        说明：
        - 契约很多时候不支持 '!' 前缀；这里直接剥离这些项
        - 更严谨做法：在服务端**生成阶段**就按用户组判定是否下发此按钮
        """
        try:
            buttons = data['data'].get('buttons', [])
            for btn in buttons:
                groups = btn.get('groups_xmlids', []) or []
                if not groups:
                    continue
                normalized = [g for g in groups if not (isinstance(g, str) and g.startswith('!'))]
                btn['groups_xmlids'] = normalized
        except Exception:
            pass
        try:
            views = (data.get('data') or {}).get('views') or {}
            form = (views.get('form') or {})
            for bucket in ('header_buttons', 'stat_buttons', 'button_box'):
                for btn in form.get(bucket, []) or []:
                    groups = btn.get('groups_xmlids', []) or []
                    btn['groups_xmlids'] = [g for g in groups if not (isinstance(g, str) and g.startswith('!'))]
        except Exception:
            pass

    @staticmethod
    def _norm_str(s):
        """
        宽松字符串归一化：去空白、统一引号、小写化。
        用于对 domain_raw 做容错比较。
        """
        if s is None:
            return ""
        return re.sub(r"\s+", "", str(s)).replace('"', "'").lower()

    # =========================
    # 自检（开发/测试环境启用）
    # =========================
    def _self_check_strict(self, data):
        """
        目的：在开发/测试环境提前暴露契约不一致问题（生产可关）
        断言项：
          - form.statusbar.field 必须存在于 fields（如果 statusbar 存在）
          - 所有 kind=object 的按钮必须有非空 method
          - tree.columns 中的字段必须存在于 fields
        """
        try:
            fields = data['data'].get('fields', {})
            # 1) statusbar 字段存在性
            form = data['data']['views'].get('form', {})
            statusbar = form.get('statusbar')
            if statusbar:
                sb_field = statusbar.get('field')
                assert sb_field in fields, "statusbar.field 不在 fields 集合中：%s" % sb_field

            # 2) object 按钮必须有 method
            for btn in data['data'].get('buttons', []):
                if btn.get('kind') == 'object':
                    method = (btn.get('payload') or {}).get('method')
                    assert method, "发现 kind=object 但无 method 的按钮：%s" % btn

            # 3) tree.columns 必须在 fields 里
            cols = data['data']['views'].get('tree', {}).get('columns', []) or []
            for col in cols:
                assert col in fields, "tree.columns 包含未知字段：%s" % col

        except AssertionError:
            # 这里直接抛出有利于测试阶段快速发现；线上可改为 logger.warning
            raise
        except Exception:
            # 容错：自检异常不影响主流程
            pass
