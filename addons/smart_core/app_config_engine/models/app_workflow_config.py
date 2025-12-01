# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval
import json, hashlib, logging

_logger = logging.getLogger(__name__)


class AppWorkflowConfig(models.Model):
    _name = 'app.workflow.config'
    _description = 'Application Workflow Configuration'
    _rec_name = 'model'
    _order = 'model'

    # ===== 基础信息 =====
    model = fields.Char('Model', required=True, index=True)

    # 版本与追踪
    version = fields.Integer('Version', default=1)
    config_hash = fields.Char('Config Hash', readonly=True, index=True)
    last_generated = fields.Datetime('Last Generated', readonly=True)

    # 标准化工作流定义（契约直用）
    # 结构示例见 _build_workflow_def()
    workflows_def = fields.Json('Workflow Definition')

    # 扩展
    meta_info = fields.Json('Meta Info')
    is_active = fields.Boolean('Active', default=True)

    _sql_constraints = [
        ('uniq_model', 'unique(model)', '每个模型仅允许一条工作流配置（model 唯一）。'),
    ]

    # ======================= 生成入口 =======================

    @api.model
    def _generate_from_workflow(self, model_name):
        """
        生成/更新“工作流契约”：
        1) 如果存在旧版 workflow 引擎 → 按活动/迁移表提取（engine='legacy'）
        2) 否则：基于模型字段(state / stage) + 表单按钮(states 属性) 推断（engine='inferred'）
        3) 附带 mail.activity.type 作为活动建议
        仅当结构变化时 +1 版本
        """
        try:
            if model_name not in self.env:
                raise ValueError(_("模型不存在：%s") % model_name)

            # 1) 首选：旧版工作流（Odoo 9 以前）
            if self._model_exists('workflow'):
                wf_def = self._build_from_legacy_workflow(model_name)
            else:
                # 2) 现代推断：state/stage + 按钮 states
                wf_def = self._build_inferred_workflow(model_name)

            # 3) 附加：mail.activity.type 建议（如可用）
            wf_def["activities"] = self._collect_mail_activities(model_name)

            # 4) 稳定哈希 & 落库
            payload = json.dumps(wf_def, sort_keys=True, ensure_ascii=False, default=str)
            new_hash = hashlib.md5(payload.encode('utf-8')).hexdigest()

            cfg = self.sudo().search([('model', '=', model_name)], limit=1)
            vals = {
                "model": model_name,
                "workflows_def": wf_def,
                "config_hash": new_hash,
                "last_generated": fields.Datetime.now(),
            }
            if cfg:
                if cfg.config_hash != new_hash:
                    vals["version"] = cfg.version + 1
                    cfg.write(vals)
                    _logger.info("Workflow config updated for %s → version %s", model_name, cfg.version)
                else:
                    _logger.info("Workflow config for %s unchanged, keep version %s", model_name, cfg.version)
            else:
                vals["version"] = 1
                cfg = self.sudo().create(vals)
                _logger.info("Workflow config created for %s → version 1", model_name)

            return cfg

        except Exception:
            _logger.exception("Failed to generate workflow config for %s", model_name)
            raise

    # ======================= 标准化输出 =======================

    def get_workflow_contract(self, filter_runtime=True):
        """
        返回标准化“工作流契约”结构
        - filter_runtime=True：按当前用户组过滤“迁移（transitions）”的可见性（基于 groups_xmlids）
        """
        self.ensure_one()
        wf = json.loads(json.dumps(self.workflows_def or {}, ensure_ascii=False))  # 深拷贝

        if not filter_runtime:
            return wf

        # 运行态：按用户组过滤每条迁移的可见性（按钮 groups）
        user_groups = set(self.env.user.groups_id.ids)

        def xmlids_to_ids(xmlids):
            ids = set()
            for xid in (xmlids or []):
                try:
                    g = self.env.ref(xid, raise_if_not_found=False)
                    if g and g._name == 'res.groups':
                        ids.add(g.id)
                except Exception:
                    pass
            return ids

        for t in wf.get('transitions', []):
            gx = set(t.get('groups_xmlids') or [])
            if not gx:
                continue
            gids = xmlids_to_ids(gx)
            if not (gids & user_groups):
                t['hidden_by_group'] = True  # 标记为不可见；前端可直接过滤
        # 过滤不可见
        wf['transitions'] = [t for t in wf.get('transitions', []) if not t.get('hidden_by_group')]

        return wf

    # ======================= 构建：统一结构 =======================

    def _build_workflow_def(self, model_name, engine, states, state_field=None, transitions=None, extra=None):
        """
        统一的工作流结构（契约 2.0）：
        {
          "model": "sale.order",
          "engine": "legacy|inferred",
          "state_field": "state",
          "states": [
            {"key":"draft","label":"草稿","color":null,"fold":false,"sequence":10},
            ...
          ],
          "transitions": [
            {
              "from": ["draft","sent"],
              "to": "sale",                         # 未能确定时为 null
              "trigger": {"kind":"object","name":"action_confirm","label":"确认"},
              "conditions": {
                 "domain_raw": "[]", "domain": [],
                 "states_attr": ["draft","sent"]   # 来自按钮 states 属性
              },
              "groups_xmlids": ["base.group_user"], # 从按钮 groups 解析（xmlid）
              "notes": "by parser"
            }
          ],
          "activities": [                           # 来自 mail.activity.type（按需）
            {"id": 12, "name":"跟进", "category":"todo", "res_model":"sale.order"}
          ],
          "meta": {...}
        }
        """
        return {
            "model": model_name,
            "engine": engine,
            "state_field": state_field,
            "states": states or [],
            "transitions": transitions or [],
            "activities": [],
            "meta": extra or {}
        }

    # ======================= 分支1：旧版工作流 =======================

    def _build_from_legacy_workflow(self, model_name):
        """
        老工作流引擎（Odoo 8 及以前）：
        - workflow / workflow.activity / workflow.transition
        - 仅抽取基本活动与迁移关系；条件以字符串保留
        """
        try:
            Wf = self.env['workflow'].sudo()
            Act = self.env['workflow.activity'].sudo() if self._model_exists('workflow.activity') else None
            Trn = self.env['workflow.transition'].sudo() if self._model_exists('workflow.transition') else None

            wfs = Wf.search([('osv', '=', model_name)])
            if not wfs:
                # 无旧引擎定义 → 回退到推断
                return self._build_inferred_workflow(model_name)

            states = []
            transitions = []
            seen_states = set()

            for wf in wfs:
                activities = Act.search([('wkf_id', '=', wf.id)]) if Act else Act
                trans = Trn.search([('wkf_id', '=', wf.id)]) if Trn else Trn

                # 活动名当作状态 key
                for a in (activities or []):
                    key = (a.name or '').strip() or f"act_{a.id}"
                    if key not in seen_states:
                        states.append({"key": key, "label": a.name or key, "color": None, "fold": False, "sequence": getattr(a, 'flow_start', False) and 5 or 50})
                        seen_states.add(key)

                # 迁移
                for t in (trans or []):
                    fr = getattr(t, 'act_from', None)
                    to = getattr(t, 'act_to', None)
                    cond = getattr(t, 'condition', None)  # Python 表达式字符串
                    transitions.append({
                        "from": [getattr(fr, 'name', None) or None],
                        "to": getattr(to, 'name', None) or None,
                        "trigger": {"kind": "server", "name": getattr(t, 'signal', '') or "transition", "label": getattr(t, 'signal', '') or "transition"},
                        "conditions": {"domain_raw": cond or None, "domain": None, "states_attr": []},
                        "groups_xmlids": [],
                        "notes": "legacy workflow"
                    })

            # 取 state_field 尝试探测（可为 selection 'state'）
            state_field = self._guess_state_field(model_name)

            return self._build_workflow_def(
                model_name=model_name,
                engine="legacy",
                states=states,
                state_field=state_field,
                transitions=transitions,
                extra={"source": "workflow/*"}
            )
        except Exception:
            _logger.exception("build legacy workflow failed for %s", model_name)
            # 出错时回退到推断
            return self._build_inferred_workflow(model_name)

    # ======================= 分支2：现代推断 =======================

    def _build_inferred_workflow(self, model_name):
        """
        现代 Odoo：无旧引擎 → 依据
        - fields_get 中的 'state'（selection）或 '...stage...'（many2one）识别状态空间
        - 解析 form 视图按钮的 states 属性，推断“允许的起始状态”
        - 尝试基于方法名猜测“目标状态”（不可保证命中；猜不中则 to=None）
        """
        Model = self.env[model_name].sudo()
        fget = Model.fields_get()
        # 1) 识别状态字段与状态集
        state_field, states = self._infer_states_from_fields(fget)

        # 2) 解析表单视图，提取 buttons（含 states/groups/context 等）
        arch = self._get_form_arch(model_name)
        buttons = self._parse_buttons_from_form_arch(arch) if arch else []

        # 3) 生成 transitions
        state_keys = [s['key'] for s in states]
        transitions = []
        for b in buttons:
            from_states = [s for s in (b.get('states') or []) if s in state_keys]  # 限制到有效状态
            if not from_states and state_keys:
                # 未声明 states → 允许从任意状态
                from_states = state_keys[:]

            to_state = self._guess_to_state(b.get('name') or '', state_keys)
            transitions.append({
                "from": sorted(list(set(from_states))),
                "to": to_state,  # 可能为 None（未知）
                "trigger": {
                    "kind": "object" if b.get('type') == 'object' else "open",
                    "name": b.get('name') or '',
                    "label": b.get('label') or b.get('name') or ''
                },
                "conditions": {
                    "domain_raw": b.get('domain_raw'),
                    "domain": self._safe_eval_expr(b.get('domain_raw')) if b.get('domain_raw') else [],
                    "states_attr": b.get('states') or []
                },
                "groups_xmlids": b.get('groups_xmlids') or [],
                "notes": "inferred from form buttons"
            })

        return self._build_workflow_def(
            model_name=model_name,
            engine="inferred",
            states=states,
            state_field=state_field,
            transitions=transitions,
            extra={"source": "fields_get + form.buttons"}
        )

    # ======================= 采集：mail 活动建议 =======================

    def _collect_mail_activities(self, model_name):
        """
        收集 mail.activity.type（如存在）：
        - 新版本有 res_model 字段可限定模型；老版本没有则返回全局类型
        """
        res = []
        if not self._model_exists('mail.activity.type'):
            return res
        T = self.env['mail.activity.type'].sudo()
        # 兼容是否存在 res_model 字段
        domain = []
        try:
            if 'res_model' in T._fields:
                domain = [('res_model', 'in', (False, model_name))]
        except Exception:
            domain = []
        for t in T.search(domain):
            res.append({
                "id": t.id,
                "name": t.name,
                "category": getattr(t, 'category', None),
                "res_model": getattr(t, 'res_model', None),
            })
        return res

    # ======================= 工具：状态推断 =======================

    def _infer_states_from_fields(self, fields_get):
        """
        优先识别 selection 型 'state' 字段；否则识别包含 'stage' 的 many2one
        返回：(state_field_name, states_list)
        """
        # 1) selection 'state'
        if 'state' in fields_get and (fields_get['state'] or {}).get('type') == 'selection':
            sel = fields_get['state'].get('selection') or []
            states = [{"key": k, "label": v, "color": None, "fold": False, "sequence": (i + 1) * 10} for i, (k, v) in enumerate(sel)]
            return 'state', states

        # 2) many2one *stage*（如 stage_id）
        for fname, meta in (fields_get or {}).items():
            t = meta.get('type')
            rel = meta.get('relation')
            if t == 'many2one' and ('stage' in fname or (rel and 'stage' in rel)):
                # 无法直接读到阶段名称集（依赖目标模型数据），这里用“占位的可扩展”形式
                states = [{"key": "__dynamic_stage__", "label": _("Dynamic Stage"), "color": None, "fold": False, "sequence": 10}]
                return fname, states

        # 3) 兜底：无状态字段
        return None, []

    def _guess_state_field(self, model_name):
        fget = self.env[model_name].sudo().fields_get()
        if 'state' in fget and (fget['state'] or {}).get('type') == 'selection':
            return 'state'
        for fname, meta in (fget or {}).items():
            if meta.get('type') == 'many2one' and ('stage' in fname or (meta.get('relation') or '').endswith('.stage')):
                return fname
        return None

    def _guess_to_state(self, method_name, available_states):
        """
        基于常见方法名启发式猜测目标状态（猜不中返回 None）：
        - confirm/approve/validate -> sale/confirmed/approved/done 中择优
        - cancel -> cancel
        - set_to_done/mark_done/done -> done
        - reset/draft -> draft
        - refuse/reject -> refuse/cancel
        """
        name = (method_name or '').lower()
        if not name or not available_states:
            return None

        def pick(candidates):
            for c in candidates:
                if c in available_states:
                    return c
            return None

        if any(k in name for k in ('confirm', 'approve', 'validate', 'accept')):
            return pick(['sale', 'confirmed', 'approved', 'done'])
        if 'cancel' in name or 'reject' in name or 'refuse' in name:
            return pick(['cancel', 'rejected', 'refused'])
        if 'done' in name or 'complete' in name or 'close' in name:
            return pick(['done', 'closed'])
        if 'draft' in name or 'reset' in name or 'set_to_draft' in name:
            return pick(['draft'])
        if 'send' in name:
            return pick(['sent'])
        return None

    # ======================= 工具：表单按钮解析 =======================

    def _get_form_arch(self, model_name):
        """
        获取表单视图最终 arch（优先 get_view；回退 fields_view_get）
        """
        Model = self.env[model_name].sudo()
        try:
            data = Model.get_view(view_type='form')
            if isinstance(data, dict) and data.get('arch'):
                return data.get('arch')
        except Exception:
            pass
        try:
            fv = Model.fields_view_get(view_type='form', toolbar=True)
            return fv.get('arch')
        except Exception:
            return None

    def _parse_buttons_from_form_arch(self, arch):
        """
        解析 <form> 内按钮：
        - type/name/string/states/groups/domain/context
        - groups 保留 xmlids（运行态再转换为 ids）
        """
        out = []
        try:
            from lxml import etree
            if not arch:
                return out
            root = etree.fromstring(arch.encode('utf-8'))
            for btn in root.xpath('.//button'):
                btype = btn.get('type') or 'object'
                name = btn.get('name') or ''
                label = btn.get('string') or btn.get('title') or name
                states_attr = btn.get('states') or ''
                groups_attr = btn.get('groups') or ''
                domain_raw = btn.get('domain')
                context_raw = btn.get('context')

                groups_xmlids = [g.strip() for g in groups_attr.split(',') if g.strip()]
                states = [s.strip() for s in states_attr.split(',') if s.strip()]

                out.append({
                    "type": btype,
                    "name": name,
                    "label": label,
                    "states": states,
                    "groups_xmlids": groups_xmlids,
                    "domain_raw": domain_raw,
                    "context_raw": context_raw
                })
        except Exception:
            _logger.exception("parse buttons from form arch failed")
        return out

    # ======================= 通用工具 =======================

    def _model_exists(self, name):
        try:
            self.env[name]
            return True
        except Exception:
            return False

    def _safe_eval_expr(self, expr):
        if not expr or not isinstance(expr, str):
            return None
        try:
            return safe_eval(expr, {})
        except Exception:
            return None
