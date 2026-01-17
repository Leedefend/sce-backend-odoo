/** @odoo-module **/

import { registry } from "@web/core/registry";
import { ScProjectWorkbench } from "./sc_project_workbench";

registry.category("actions").add("sc_project_workbench", ScProjectWorkbench);

