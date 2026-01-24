/** @odoo-module **/

import { FormStatusIndicator } from "@web/views/form/form_status_indicator/form_status_indicator";
import { patch } from "@web/core/utils/patch";

patch(FormStatusIndicator.prototype, {
    get scHideDiscard() {
        const root = this.props?.model?.root;
        if (!root) {
            return false;
        }
        const resModel = root.resModel || this.props?.resModel || "";
        if (resModel !== "project.project") {
            return false;
        }
        const state = root.data?.lifecycle_state || "";
        if (state !== "draft") {
            return false;
        }
        return Boolean(root.dirty);
    },
});
