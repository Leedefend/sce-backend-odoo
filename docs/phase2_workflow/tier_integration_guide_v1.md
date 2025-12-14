# 业务单据 × Tier 审批接入规范 v1.0

## 0. 目标与边界

**目标：**用最小改动让任意业务单据（例：`project.material.plan`）接入 OCA `base_tier_validation`，实现：

- 提交触发审批实例（`tier.review`）
- 审批人有“待我审批”入口
- 审批通过/驳回回写业务状态与字段
- 权限依旧走“能力组”体系，不散落到角色/旧组

**边界：**

- Tier 负责审批机制与记录；业务模型负责状态机与业务字段。
- 不在业务模型里硬编码审批人派单、待办、邮件。

---

## 1. 依赖与加载

`__manifest__.py`：

- `depends`: `base_tier_validation`, `base_tier_validation_server_action`
- `data` 至少包含：
  - `data/<doc>_tier_actions.xml`（审批通过/驳回回调的 server action）
  - `views/<tier_review_entry>.xml`（“待我审批”入口 action + menu）
  - （可选）`models/tier_definition_ext.py` 扩展可选模型白名单

---

## 2. 业务模型接入

### 2.1 继承

```python
_inherit = ["mail.thread", "mail.activity.mixin", "tier.validation"]
```

### 2.2 状态机

建议：`draft` → `submit` → `approved` → `done/cancel`。`submit` 是审批入口态。

### 2.3 提交流程（模板）

```python
def action_submit(self):
    for rec in self:
        rec._business_validate_before_submit()  # 业务校验
        rec.write({
            "state": "submit",
            "submitted_by": self.env.user.id,
            "submitted_at": fields.Datetime.now(),
            "reject_reason": False,
        })
        rec.invalidate_recordset()
        company = rec.company_id or self.env.company
        rec.with_context(
            allowed_company_ids=[company.id],
            force_company=company.id,
        ).request_validation()
        rec.message_post(body=_("单据已提交，进入审批流程。"))
```

禁止：提交时再派单/发待办/硬编码审批人。

### 2.4 Gate：确保 request_validation 可触发

必须覆盖 `_check_state_from_condition`：

```python
def _check_state_from_condition(self):
    self.ensure_one()
    parent = getattr(super(), "_check_state_from_condition", None)
    base_ok = parent() if parent else False
    return base_ok or (self.state == "submit")
```

### 2.5 审批回调（Server Action 调用）

```python
def action_on_tier_approved(self):
    for rec in self:
        if rec.state != "submit":
            continue
        rec.write({
            "state": "approved",
            "approved_by": self.env.user.id,
            "approved_at": fields.Datetime.now(),
        })
        rec.message_post(body=_("审批通过。"))

def action_on_tier_rejected(self, reason=None):
    for rec in self:
        if rec.state != "submit":
            continue
        rec.write({
            "state": "draft",
            "reject_reason": reason or _("未填写原因"),
        })
        rec.message_post(body=_("审批驳回：%s") % rec.reject_reason)
```

---

## 3. Tier Definition 配置（UI）

- Referenced Model：业务模型
- Apply On：`[("state","=","submit")]`
- Reviewer：人/组/字段（三选一）
- 多级审批用 sequence 配置

---

## 4. Server Action 绑定

为每个模型提供两条 server action 并在 Tier Definition 绑定：

- Approved → `records.action_on_tier_approved()`
- Rejected → `records.action_on_tier_rejected()`

回调只做“业务状态回写”，不要加复杂业务逻辑。

---

## 5. “待我审批”入口规范

Action（示例）：

```xml
<record id="action_sc_tier_review_my_doc" model="ir.actions.act_window">
    <field name="name">待我审批（XXX）</field>
    <field name="res_model">tier.review</field>
    <field name="view_mode">tree,form</field>
    <field name="domain">[
        ('reviewer_id','=',uid),
        ('status','in',('waiting','pending')),
        ('model','=','your.model')
    ]</field>
</record>
```

Menu：

```xml
<menuitem id="menu_sc_tier_review_my_doc"
          name="待我审批"
          parent="...业务中心父菜单..."
          action="smart_construction_core.action_sc_tier_review_my_doc"
          groups="smart_construction_core.group_sc_cap_<domain>_manager"/>
```

要点：groups 绑定业务域审批能力组。

---

## 6. 权限策略

- 不依赖 base_tier_validation 的组（它可能无 res.groups）。
- 入口/动作/ACL 绑定你自己的能力组：
  - 配置/定义：`group_sc_cap_config_admin`
  - 审批入口：对应域的 `*_manager`
- 若审批人能看菜单但 403，补一条 ACL 给能力组（对 `tier.review` 读/写/创建）。

---

## 7. 验收标准（DoD）

接入一个模型时，须满足：

1) 提交后生成 `tier.review`  
2) 审批人能在“待我审批（该模型）”看到记录  
3) 审批通过：state=approved，审计字段写入  
4) 审批驳回：state=draft，驳回原因写入  
5) 升级通过，无 registry 错误  
6) 多公司下 definition 命中（company/context 正确）

---

## 8. 参考实现

- 业务模型：`project.material.plan`  
- 接入文件：  
  - Python：`addons/smart_construction_core/models/material_plan.py`  
  - 回调动作：`addons/smart_construction_core/data/material_plan_tier_actions.xml`  
  - 待审入口：`addons/smart_construction_core/views/tier_review_views.xml`  
  - 白名单扩展：`addons/smart_construction_core/models/tier_definition_ext.py`

