/** @odoo-module **/

import { Component, onMounted, useState, xml } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { navigateToTarget } from "./insight_nav";

export class ScInsightWidget extends Component {
  static props = {
    model: { type: String },
    resId: { type: Number },
    scene: { type: String },
  };

  static template = xml`
    <div class="sc-insight-banner sc-insight--compact">
      <t t-if="state.loading">
        <div class="alert alert-info mb-2"><span class="text-muted">正在生成系统洞察…</span></div>
      </t>
      <t t-elif="state.unsaved">
        <div class="alert alert-info mb-2">
          <div class="fw-bold">项目尚未保存</div>
          <div>保存后系统将生成“项目启动洞察”，并给出下一步建议。</div>
        </div>
      </t>
      <t t-elif="state.error">
        <div class="alert alert-warning mb-2">
          <div class="fw-bold">系统提示</div>
          <div t-esc="state.error"/>
        </div>
      </t>
      <t t-else="">
        <t t-if="state.ui and state.ui.hero">
          <div class="sc-insight-hero">
            <div class="sc-insight-hero__title" t-esc="state.ui.hero.title || '项目启动洞察'"/>
          </div>
        </t>

        <t t-if="state.ui and state.ui.next_best and state.ui.next_best.item">
          <div class="sc-insight-next">
            <div class="sc-insight-next__label" t-esc="state.ui.next_best.title || '建议现在先做这一件：'"/>
            <div class="sc-insight-next__headline" t-esc="state.ui.next_best.item.headline || ''"/>
            <t t-if="state.ui.next_best.item.because">
              <div class="sc-insight-next__because" t-esc="state.ui.next_best.item.because"/>
            </t>
            <div class="sc-insight-next__actions">
              <t t-if="state.ui.next_best.item.cta_primary">
                <button type="button" class="btn btn-sm btn-primary"
                        t-att-data-target="state.ui.next_best.item.cta_primary.target"
                        t-on-click="onAction">
                  <t t-esc="getPrimaryLabel(state.ui.next_best.item.cta_primary)"/>
                </button>
              </t>
              <t t-if="state.ui.next_best.item.cta_secondary">
                <button type="button" class="btn btn-sm btn-link sc-insight-secondary"
                        t-att-data-target="state.ui.next_best.item.cta_secondary.target"
                        t-on-click="onAction">
                  <t t-esc="getSecondaryLabel(state.ui.next_best.item.cta_secondary)"/>
                </button>
              </t>
            </div>
          </div>
        </t>

        <t t-if="state.ui and state.ui.more and state.ui.more.items and state.ui.more.items.length">
          <details class="sc-insight-more">
            <summary class="sc-insight-more__summary" t-esc="getCollapsedTitle(state.ui.more.collapsed_title)"/>
            <div class="sc-insight-more__list">
              <t t-foreach="state.ui.more.items" t-as="it" t-key="it.key">
                <div class="sc-insight-more__item">
                  <div class="sc-insight-more__headline" t-esc="it.headline || ''"/>
                  <t t-if="it.consequence"><div class="sc-insight-more__text" t-esc="it.consequence"/></t>
                  <t t-if="it.block_stage"><div class="sc-insight-more__text" t-esc="it.block_stage"/></t>
                  <t t-if="it.cta">
                    <div class="sc-insight-more__actions">
                      <button type="button" class="btn btn-sm btn-outline-primary"
                              t-att-data-target="it.cta.target"
                              t-on-click="onAction">
                        <t t-esc="it.cta.label || '去完善'"/>
                      </button>
                    </div>
                  </t>
                </div>
              </t>
            </div>
          </details>
        </t>

        <t t-if="state.hint">
          <div class="sc-insight-hint"><t t-esc="state.hint"/></div>
        </t>
      </t>
    </div>
  `;

  setup() {
    this.insight = useService("sc_insight");
    this.state = useState({
      loading: false,
      unsaved: false,
      error: "",
      ui: null,
      hint: "",
    });

    onMounted(() => this.refresh());
  }

  async refresh() {
    const { model, resId, scene } = this.props;
    if (!resId) {
      this.state.unsaved = true;
      this.state.loading = false;
      this.state.error = "";
      this.state.ui = null;
      return;
    }

    this.state.unsaved = false;
    this.state.loading = true;
    this.state.error = "";
    this.state.ui = null;

    try {
      const payload = await this.insight.get({ model, id: resId, scene });
      if (!payload || payload.ok !== true) {
        this.state.error = payload?.error?.message || "无法获取系统洞察。";
        return;
      }
      const data = payload.data || {};
      const initiation = data.initiation || {};
      this.state.ui = initiation.ui_model || null;
      if (!this.state.ui) {
        this.state.error = "当前未返回可渲染的洞察模型，请稍后刷新。";
      }
    } catch (err) {
      this.state.error = "网络异常，无法获取系统洞察。";
    } finally {
      this.state.loading = false;
    }
  }

  onAction(targetOrEvent) {
    let target = targetOrEvent;
    if (targetOrEvent && targetOrEvent.currentTarget) {
      const el = targetOrEvent.currentTarget;
      target = el && el.dataset ? el.dataset.target : "";
    }
    if (!target) {
      this.state.hint = "好的，你先继续当前工作；系统会在合适的时候再提醒你。";
      setTimeout(() => (this.state.hint = ""), 2000);
      return;
    }
    const formRoot = (this.el && this.el.closest(".o_form_view")) || document;
    const ok = navigateToTarget(formRoot, target, {
      onStatus: (status) => {
        if (status === "action") {
          this.state.hint = "正在打开对应入口…";
          setTimeout(() => (this.state.hint = ""), 2000);
        }
        if (status === "no_permission") {
          this.state.hint = "当前账号无权限进入该模块，请联系管理员。";
          setTimeout(() => (this.state.hint = ""), 3000);
        }
      },
    });
    if (!ok) {
      this.state.hint = "已尝试定位入口，请手动查看对应区域。";
      setTimeout(() => (this.state.hint = ""), 2000);
    }
  }

  getPrimaryLabel(cta) {
    const target = cta && cta.target ? String(cta.target) : "";
    if (target === "wbs") return "开始拆 WBS";
    if (target === "boq") return "导入清单";
    if (target === "schedule") return "设置周期";
    if (target === "manager") return "指定负责人";
    return (cta && cta.label) || "去处理";
  }

  getSecondaryLabel(cta) {
    return (cta && cta.label) || "稍后处理";
  }

  getCollapsedTitle(title) {
    if (!title) return "";
    return String(title).replace("（可稍后处理）", "");
  }
}
