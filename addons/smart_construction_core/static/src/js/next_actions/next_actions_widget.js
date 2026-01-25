/** @odoo-module **/

import { Component, onWillStart, useState, xml } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class ScNextActionsWidget extends Component {
  static template = xml`
    <div class="sc-next-actions">
      <t t-if="state.loading">
        <div class="text-muted">正在生成建议动作…</div>
      </t>
      <t t-elif="state.status === 'need_save'">
        <div class="text-muted" t-esc="state.message"/>
        <button type="button" class="btn btn-light btn-sm mt-2"
                t-on-click="() => window.scrollTo({top: 0, behavior: 'smooth'})">
          继续完善并保存
        </button>
      </t>
      <t t-elif="state.error">
        <div class="text-muted">下一步指令生成失败，请稍后重试。</div>
      </t>
      <t t-elif="state.items.length === 0">
        <div class="text-muted">暂无下一步指令。</div>
        <t t-if="state.fallback">
          <button type="button" class="btn btn-light btn-sm mt-2"
                  t-on-click="() => this.onActionClick(state.fallback)">
            查看阶段要求
          </button>
        </t>
      </t>
      <t t-else="">
        <div class="sc-next-actions__list">
          <t t-foreach="state.items" t-as="item" t-key="item.action_ref + item.title">
            <div class="sc-next-actions__item d-flex align-items-start gap-3">
              <div class="sc-next-actions__index">
                <t t-esc="state.items.indexOf(item) + 1"/>
              </div>
              <div class="sc-next-actions__body">
                <div class="sc-next-actions__headline" t-esc="item.title"/>
                <div class="sc-next-actions__hint" t-if="item.hint" t-esc="item.hint"/>
                <t t-if="state.items.indexOf(item) === 0">
                  <button type="button" class="btn btn-primary btn-sm"
                          t-on-click="() => this.onActionClick(item)">
                    去完成
                  </button>
                </t>
                <t t-else="">
                  <button type="button" class="btn btn-link btn-sm"
                          t-on-click="() => this.onActionClick(item)">
                    去完成
                  </button>
                </t>
              </div>
            </div>
          </t>
        </div>
      </t>
    </div>
  `;
  static props = {
    model: { type: String, optional: true },
    resId: { type: Number, optional: true },
    limit: { type: Number, optional: true },
  };

  setup() {
    this.orm = useService("orm");
    this.action = useService("action");
    this.notification = useService("notification");
    this.state = useState({ loading: true, items: [], error: null, status: "idle", message: "", fallback: null });

    onWillStart(() => this.load());
  }

  get resId() {
    return Number.isFinite(this.props.resId) ? this.props.resId : 0;
  }

  get model() {
    return this.props.model || "project.project";
  }

  get limit() {
    return Number.isFinite(this.props.limit) ? this.props.limit : 3;
  }

  async load() {
    const resId = this.resId;
    this.state.loading = true;
    this.state.error = null;
    this.state.items = [];
    if (!resId) {
      this.state.loading = false;
      this.state.status = "need_save";
      this.state.message = "请先完成创建（保存）以生成建议动作。";
      this.state.items = [];
      return;
    }
    try {
      const payload = await this.orm.call(this.model, "sc_get_next_actions", [[resId], this.limit]);
      const actions = payload && Array.isArray(payload.actions) ? payload.actions : [];
      this.state.items = actions;
      this.state.status = payload && payload.status ? payload.status : "ok";
      this.state.message = payload && payload.message ? payload.message : "";
      this.state.fallback = payload && payload.fallback ? payload.fallback : null;
    } catch (err) {
      this.state.error = err;
    } finally {
      this.state.loading = false;
    }
  }

  async onActionClick(item) {
    if (!item) return;
    try {
      const result = await this.orm.call(this.model, "sc_execute_next_action", [
        [this.resId],
        item.action_type,
        item.action_ref,
        item.payload || {},
      ]);
      if (result) {
        await this.action.doAction(result, { clearBreadcrumbs: false });
      }
      await this.load();
    } catch (err) {
      this.notification.add("执行下一步动作失败，请稍后重试。", { type: "danger" });
    }
  }
}
