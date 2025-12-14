# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError

CONFIG_GROUP = "smart_construction_core.group_sc_cap_config_admin"


class ScWorkflowDef(models.Model):
    _name = "sc.workflow.def"
    _description = "SC Workflow Definition"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "id desc"

    name = fields.Char(required=True, tracking=True, string="名称")
    code = fields.Char(required=True, index=True, tracking=True, string="编码")
    state = fields.Selection(
        [("draft", "草稿"), ("published", "已发布")],
        default="draft",
        tracking=True,
        index=True,
    )
    active = fields.Boolean(default=True, tracking=True, string="启用")
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company, index=True, string="公司")

    model_name = fields.Char(
        string="目标模型",
        required=True,
        tracking=True,
        help="Technical model name, e.g. project.material.plan",
    )
    trigger = fields.Char(
        string="触发器",
        tracking=True,
        help="Logical trigger name, e.g. submit",
    )

    node_ids = fields.One2many("sc.workflow.node", "workflow_def_id", string="节点")
    start_node_id = fields.Many2one(
        "sc.workflow.node",
        string="起始节点",
        domain="[('workflow_def_id', '=', id)]",
        tracking=True,
    )
    instance_count = fields.Integer(compute="_compute_instance_count")

    def _compute_instance_count(self):
        Inst = self.env["sc.workflow.instance"].sudo()
        for rec in self:
            rec.instance_count = Inst.search_count([("workflow_def_id", "=", rec.id)])

    # ==== 权限 / 校验 ====
    def _require_admin(self):
        if not self.env.user.has_group(CONFIG_GROUP):
            raise UserError(_("You do not have permission to manage workflows."))

    def action_publish(self):
        self._require_admin()
        for rec in self:
            start = rec.start_node_id or rec.get_start_node()
            if not start:
                raise UserError(_("Please configure at least one active start node before publishing."))
            rec.state = "published"

    def action_draft(self):
        self._require_admin()
        self.write({"state": "draft"})

    def get_start_node(self):
        self.ensure_one()
        if self.start_node_id and self.start_node_id.active:
            return self.start_node_id
        nodes = self.node_ids.filtered(lambda n: n.active and n.node_type == "start").sorted("sequence")
        if nodes:
            return nodes[0]
        nodes = self.node_ids.filtered(lambda n: n.active).sorted("sequence")
        return nodes[:1] if nodes else self.env["sc.workflow.node"]


class ScWorkflowNode(models.Model):
    _name = "sc.workflow.node"
    _description = "SC Workflow Node"
    _order = "sequence,id"

    workflow_def_id = fields.Many2one("sc.workflow.def", required=True, ondelete="cascade", index=True, string="工作流定义")
    active = fields.Boolean(default=True, string="启用")

    code = fields.Char(required=True, index=True, help="Stable node code, e.g. submit_review", string="编码")
    name = fields.Char(required=True, string="名称")
    sequence = fields.Integer(default=10, index=True, string="顺序")

    node_type = fields.Selection(
        [("start", "开始"), ("normal", "普通"), ("end", "结束")],
        default="normal",
        required=True,
        string="节点类型",
    )
    can_reject = fields.Boolean(default=True, string="允许驳回")

    approve_group_id = fields.Many2one(
        "res.groups",
        string="审批组",
        required=True,
        help="Users in this group can approve the workitem.",
    )

    next_node_id = fields.Many2one(
        "sc.workflow.node",
        string="下一节点",
        domain="[('workflow_def_id', '=', workflow_def_id)]",
        help="Simple linear workflow. For Phase2, one next node is enough.",
    )
    reject_node_id = fields.Many2one(
        "sc.workflow.node",
        string="驳回到",
        domain="[('workflow_def_id', '=', workflow_def_id)]",
        help="When rejected, flow will jump to this node. If empty, jump to start node.",
    )

    def allowed_group_set(self):
        self.ensure_one()
        xmlid = self.approve_group_id.get_external_id().get(self.approve_group_id.id) if self.approve_group_id else None
        return {xmlid} if xmlid else set()


class ScWorkflowInstance(models.Model):
    _name = "sc.workflow.instance"
    _description = "SC Workflow Instance"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "id desc"

    name = fields.Char(string="实例", compute="_compute_name", store=True)
    workflow_def_id = fields.Many2one("sc.workflow.def", required=True, ondelete="restrict", index=True, string="工作流定义")
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company, index=True, string="公司")

    model_name = fields.Char(required=True, index=True, string="模型")
    res_id = fields.Integer(required=True, index=True, string="资源ID")

    state = fields.Selection(
        [("draft", "草稿"), ("running", "进行中"), ("done", "完成"), ("rejected", "已驳回"), ("cancelled", "已取消")],
        default="draft",
        tracking=True,
        index=True,
        string="状态",
    )

    current_node_id = fields.Many2one("sc.workflow.node", ondelete="restrict", index=True, string="当前节点")
    submitter_id = fields.Many2one("res.users", index=True, string="提交人")
    submitted_at = fields.Datetime(index=True, string="提交时间")
    finished_at = fields.Datetime(string="完成时间")

    workitem_ids = fields.One2many("sc.workflow.workitem", "instance_id")
    log_ids = fields.One2many("sc.workflow.log", "instance_id")

    @api.depends("workflow_def_id", "res_id")
    def _compute_name(self):
        for rec in self:
            if rec.workflow_def_id and rec.res_id:
                rec.name = "%s#%s" % (rec.workflow_def_id.code or rec.workflow_def_id.name, rec.res_id)
            elif rec.workflow_def_id:
                rec.name = rec.workflow_def_id.code or rec.workflow_def_id.name
            else:
                rec.name = ""

    # ==== 权限 / 校验 ====
    def _require_admin(self):
        if not self.env.user.has_group(CONFIG_GROUP):
            raise UserError(_("You do not have permission to manage workflow instances."))

    def _require_group(self, group_xmlid):
        if group_xmlid and not self.env.user.has_group(group_xmlid):
            raise UserError(_("You are not allowed to perform this action."))
        if not group_xmlid and not self.env.user.has_group(CONFIG_GROUP):
            raise UserError(_("No approval group configured and you are not config admin."))

    @staticmethod
    def _group_xmlid(group):
        return group.get_external_id().get(group.id) if group else None

    def _get_start_node(self):
        self.ensure_one()
        node = self.workflow_def_id.get_start_node()
        if not node:
            raise UserError(_("Workflow definition has no start node."))
        return node

    def _get_todo_workitem(self):
        self.ensure_one()
        return self.workitem_ids.filtered(lambda w: w.status == "todo")[:1]

    def _create_workitem(self, node):
        self.ensure_one()
        if not node.approve_group_id:
            raise UserError(_("Node %s has no approve group") % node.name)
        return self.env["sc.workflow.workitem"].create({
            "instance_id": self.id,
            "node_id": node.id,
            "assignee_group_id": node.approve_group_id.id,
            "status": "todo",
        })

    def _log(self, action, from_state, to_state, from_node, to_node, note=None):
        self.ensure_one()
        return self.env["sc.workflow.log"].create({
            "instance_id": self.id,
            "action": action,
            "from_state": from_state,
            "to_state": to_state,
            "from_node_id": from_node.id if from_node else False,
            "to_node_id": to_node.id if to_node else False,
            "actor_id": self.env.user.id,
            "note": note,
        })

    # ==== 运行时动作 ====
    @api.model
    def create_instance(self, workflow_def, model_name, res_id, note=None):
        self._require_admin()
        if isinstance(workflow_def, int):
            workflow_def = self.env["sc.workflow.def"].browse(workflow_def)
        workflow_def = workflow_def.exists()
        if not workflow_def:
            raise UserError(_("Workflow definition not found."))
        if workflow_def.state != "published":
            raise UserError(_("Workflow definition is not published."))
        start = workflow_def.get_start_node()
        if not start:
            raise UserError(_("Workflow definition has no active start node."))

        inst = self.create({
            "workflow_def_id": workflow_def.id,
            "company_id": workflow_def.company_id.id or self.env.company.id,
            "model_name": model_name,
            "res_id": res_id,
            "current_node_id": start.id,
            "state": "draft",
        })
        inst._log("create", "draft", "draft", start, start, note=note)
        return inst

    def action_submit(self):
        self._require_admin()
        for rec in self:
            if rec.state != "draft":
                raise UserError(_("Only draft workflow can be submitted."))
            start = rec.current_node_id or rec._get_start_node()
            rec.write({
                "state": "running",
                "current_node_id": start.id,
                "submitter_id": self.env.user.id,
                "submitted_at": fields.Datetime.now(),
            })
            rec._create_workitem(start)
            rec._log("submit", "draft", "running", start, start)
        return True

    def action_approve(self, note=None):
        for rec in self:
            if rec.state != "running":
                raise UserError(_("Only running workflow can be approved."))
            workitem = rec._get_todo_workitem()
            if not workitem:
                raise UserError(_("No pending workitem."))
            node = workitem.node_id
            # 权限校验：节点审批组或配置管理员
            if not self.env.user.has_group(CONFIG_GROUP):
                rec._require_group(self._group_xmlid(node.approve_group_id))

            workitem.write({"status": "done", "done_by": self.env.user.id, "done_at": fields.Datetime.now()})

            next_node = node.next_node_id
            from_state = rec.state
            if not next_node or next_node.node_type == "end":
                rec.write({
                    "state": "done",
                    "current_node_id": next_node.id if next_node else node.id,
                    "finished_at": fields.Datetime.now(),
                })
                rec._log("approve", from_state, "done", node, next_node or node, note=note)
                continue

            rec.write({"current_node_id": next_node.id})
            rec._create_workitem(next_node)
            rec._log("approve", from_state, "running", node, next_node, note=note)
        return True

    def action_reject(self, note=None):
        for rec in self:
            if rec.state != "running":
                raise UserError(_("Only running workflow can be rejected."))
            workitem = rec._get_todo_workitem()
            if not workitem:
                raise UserError(_("No pending workitem."))
            node = workitem.node_id
            if not self.env.user.has_group(CONFIG_GROUP):
                rec._require_group(self._group_xmlid(node.approve_group_id))

            workitem.write({"status": "cancelled", "done_by": self.env.user.id, "done_at": fields.Datetime.now(), "note": note})
            target = node.reject_node_id or rec._get_start_node()
            rec.write({
                "state": "running",
                "current_node_id": target.id,
            })
            rec._create_workitem(target)
            rec._log("reject", "running", "running", node, target, note=note)
        return True

    def action_cancel(self, note=None):
        self._require_admin()
        for rec in self:
            if rec.state in ("done", "cancelled"):
                continue
            todo_items = rec.workitem_ids.filtered(lambda w: w.status == "todo")
            todo_items.write({"status": "cancelled", "done_by": self.env.user.id, "done_at": fields.Datetime.now()})
            from_state = rec.state
            rec.write({
                "state": "cancelled",
                "finished_at": fields.Datetime.now(),
            })
            rec._log("cancel", from_state, "cancelled", rec.current_node_id, rec.current_node_id, note=note)
        return True


class ScWorkflowWorkitem(models.Model):
    _name = "sc.workflow.workitem"
    _description = "SC Workflow Workitem"
    _order = "id desc"

    instance_id = fields.Many2one("sc.workflow.instance", required=True, ondelete="cascade", index=True)
    node_id = fields.Many2one("sc.workflow.node", required=True, ondelete="restrict", index=True)

    assignee_id = fields.Many2one("res.users", string="分配用户")
    assignee_group_id = fields.Many2one("res.groups", string="分配组", required=True)
    done_by = fields.Many2one("res.users", string="处理人")

    status = fields.Selection([("todo", "待办"), ("done", "已完成"), ("cancelled", "已取消")], default="todo", index=True, string="状态")
    created_at = fields.Datetime(default=fields.Datetime.now, index=True, string="创建时间")
    done_at = fields.Datetime(string="处理时间")
    note = fields.Text(string="备注")


class ScWorkflowLog(models.Model):
    _name = "sc.workflow.log"
    _description = "SC Workflow Log"
    _order = "id desc"

    instance_id = fields.Many2one("sc.workflow.instance", required=True, ondelete="cascade", index=True)
    action = fields.Selection(
        [("create", "创建"), ("submit", "提交"), ("approve", "审批通过"), ("reject", "驳回"), ("cancel", "取消"), ("back", "回退")],
        required=True,
        index=True,
        string="动作",
    )
    from_state = fields.Char(string="来源状态")
    to_state = fields.Char(string="目标状态")
    from_node_id = fields.Many2one("sc.workflow.node", ondelete="set null", string="来源节点")
    to_node_id = fields.Many2one("sc.workflow.node", ondelete="set null", string="目标节点")
    actor_id = fields.Many2one("res.users", default=lambda self: self.env.user, index=True, string="执行人")
    note = fields.Text(string="备注")
    created_at = fields.Datetime(default=fields.Datetime.now, index=True, string="时间")

    @api.model
    def create_log(self, instance, action, note=None):
        return self.create({
            "instance_id": instance.id,
            "action": action,
            "note": note,
        })
