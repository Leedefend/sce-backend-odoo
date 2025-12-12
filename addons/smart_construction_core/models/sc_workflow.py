# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ScWorkflowDef(models.Model):
    _name = "sc.workflow.def"
    _description = "SC Workflow Definition"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "id desc"

    name = fields.Char(required=True, tracking=True)
    active = fields.Boolean(default=True, tracking=True)
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company, index=True)

    model_name = fields.Char(
        string="Target Model",
        required=True,
        tracking=True,
        help="Technical model name, e.g. project.material.plan",
    )
    trigger = fields.Char(
        string="Trigger",
        tracking=True,
        help="Logical trigger name, e.g. submit",
    )

    node_ids = fields.One2many("sc.workflow.node", "workflow_def_id", string="Nodes")
    instance_count = fields.Integer(compute="_compute_instance_count")

    def _compute_instance_count(self):
        Inst = self.env["sc.workflow.instance"].sudo()
        for rec in self:
            rec.instance_count = Inst.search_count([("workflow_def_id", "=", rec.id)])

    def get_start_node(self):
        self.ensure_one()
        nodes = self.node_ids.filtered(lambda n: n.active).sorted("sequence")
        return nodes[:1] if nodes else self.env["sc.workflow.node"]


class ScWorkflowNode(models.Model):
    _name = "sc.workflow.node"
    _description = "SC Workflow Node"
    _order = "sequence,id"

    workflow_def_id = fields.Many2one("sc.workflow.def", required=True, ondelete="cascade", index=True)
    active = fields.Boolean(default=True)

    code = fields.Char(required=True, index=True, help="Stable node code, e.g. submit_review")
    name = fields.Char(required=True)
    sequence = fields.Integer(default=10, index=True)

    node_type = fields.Selection(
        [("approve", "Approve"), ("notify", "Notify")],
        default="approve",
        required=True,
    )
    can_reject = fields.Boolean(default=True)

    groups_xml_ids = fields.Char(
        string="Allowed Groups (XMLIDs)",
        help="Comma-separated group XMLIDs, e.g. smart_construction_core.group_sc_cap_material_manager",
    )

    next_node_id = fields.Many2one(
        "sc.workflow.node",
        string="Next Node",
        domain="[('workflow_def_id', '=', workflow_def_id)]",
        help="Simple linear workflow. For Phase2, one next node is enough.",
    )

    def allowed_group_set(self):
        self.ensure_one()
        raw = (self.groups_xml_ids or "").strip()
        if not raw:
            return set()
        return {x.strip() for x in raw.split(",") if x.strip()}


class ScWorkflowInstance(models.Model):
    _name = "sc.workflow.instance"
    _description = "SC Workflow Instance"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "id desc"

    workflow_def_id = fields.Many2one("sc.workflow.def", required=True, ondelete="restrict", index=True)
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company, index=True)

    model_name = fields.Char(required=True, index=True)
    res_id = fields.Integer(required=True, index=True)

    state = fields.Selection(
        [("running", "Running"), ("done", "Done"), ("rejected", "Rejected"), ("cancelled", "Cancelled")],
        default="running",
        tracking=True,
        index=True,
    )

    current_node_id = fields.Many2one("sc.workflow.node", ondelete="restrict", index=True)
    started_by = fields.Many2one("res.users", default=lambda self: self.env.user, index=True)
    started_at = fields.Datetime(default=fields.Datetime.now, index=True)
    finished_at = fields.Datetime()

    workitem_ids = fields.One2many("sc.workflow.workitem", "instance_id")
    log_ids = fields.One2many("sc.workflow.log", "instance_id")

    @api.model
    def create_instance(self, workflow_def, model_name, res_id, note=None):
        """Create instance + first workitem, minimal linear workflow."""
        if isinstance(workflow_def, int):
            workflow_def = self.env["sc.workflow.def"].browse(workflow_def)
        workflow_def = workflow_def.exists()
        if not workflow_def:
            raise UserError(_("Workflow definition not found."))

        start = workflow_def.get_start_node()
        if not start:
            raise UserError(_("Workflow definition has no active nodes."))

        inst = self.create({
            "workflow_def_id": workflow_def.id,
            "company_id": workflow_def.company_id.id or self.env.company.id,
            "model_name": model_name,
            "res_id": res_id,
            "current_node_id": start.id,
        })

        self.env["sc.workflow.workitem"].create_workitem(inst, start)
        self.env["sc.workflow.log"].create_log(inst, action="submit", note=note)
        return inst


class ScWorkflowWorkitem(models.Model):
    _name = "sc.workflow.workitem"
    _description = "SC Workflow Workitem"
    _order = "id desc"

    instance_id = fields.Many2one("sc.workflow.instance", required=True, ondelete="cascade", index=True)
    node_id = fields.Many2one("sc.workflow.node", required=True, ondelete="restrict", index=True)

    assigned_to = fields.Many2one("res.users", string="Assigned User")
    assigned_group_xmlid = fields.Char(string="Assigned Group XMLID")

    status = fields.Selection([("todo", "To Do"), ("done", "Done"), ("cancelled", "Cancelled")], default="todo", index=True)
    created_at = fields.Datetime(default=fields.Datetime.now, index=True)
    acted_at = fields.Datetime()

    @api.model
    def create_workitem(self, instance, node):
        allowed = node.allowed_group_set()
        group_xmlid = next(iter(allowed), None)
        return self.create({
            "instance_id": instance.id,
            "node_id": node.id,
            "assigned_group_xmlid": group_xmlid,
            "status": "todo",
        })


class ScWorkflowLog(models.Model):
    _name = "sc.workflow.log"
    _description = "SC Workflow Log"
    _order = "id desc"

    instance_id = fields.Many2one("sc.workflow.instance", required=True, ondelete="cascade", index=True)
    action = fields.Selection(
        [("submit", "Submit"), ("approve", "Approve"), ("reject", "Reject"), ("cancel", "Cancel"), ("back", "Back")],
        required=True,
        index=True,
    )
    actor_id = fields.Many2one("res.users", default=lambda self: self.env.user, index=True)
    note = fields.Text()
    created_at = fields.Datetime(default=fields.Datetime.now, index=True)

    @api.model
    def create_log(self, instance, action, note=None):
        return self.create({
            "instance_id": instance.id,
            "action": action,
            "note": note,
        })
