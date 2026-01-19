/** @odoo-module **/

import { Component, xml } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { ScInsightWidget } from "./insight_widget";
import "./insight_service";

export class ScInsightViewWidget extends Component {
  static template = xml`
    <ScInsightWidget t-props="childProps"/>
  `;
  static props = {
    record: { optional: true },
    options: { optional: true },
    readonly: { optional: true },
  };
  static components = { ScInsightWidget };

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
    const scene = options.scene || "project.entry";
    return {
      model,
      resId: Number.isFinite(resId) ? resId : 0,
      scene,
    };
  }
}

registry.category("view_widgets").add("sc_insight_banner", {
  component: ScInsightViewWidget,
});
