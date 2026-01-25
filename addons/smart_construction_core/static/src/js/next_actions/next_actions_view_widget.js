/** @odoo-module **/

import { Component, xml } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { ScNextActionsWidget } from "./next_actions_widget";

export class ScNextActionsViewWidget extends Component {
  static components = { ScNextActionsWidget };
  static props = {
    record: { optional: true },
    options: { optional: true },
    readonly: { optional: true },
  };
  static template = xml`
    <ScNextActionsWidget t-props="childProps"/>
  `;

  get childProps() {
    const record = this.props?.record;
    const options = this.props?.options || {};
    const model =
      record?.resModel ||
      record?.model ||
      record?.res_model ||
      record?.modelName ||
      options.model ||
      "project.project";
    const resId = Number(record?.resId || record?.res_id || record?.id || 0);
    const limit = Number(options.limit || 3);
    return {
      model,
      resId: Number.isFinite(resId) ? resId : 0,
      limit: Number.isFinite(limit) ? limit : 3,
    };
  }
}

registry.category("view_widgets").add("sc_next_actions", {
  component: ScNextActionsViewWidget,
});
