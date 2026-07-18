from odoo.exceptions import UserError


def uninstall_hook(env):
    if not env.context.get("allow_audited_tenant_destroy"):
        raise UserError(
            "Customer delivery modules cannot be uninstalled. "
            "Use the audited tenant-destroy workflow."
        )
