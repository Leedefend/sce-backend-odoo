# 自筹资金办理闭环口径

日期：2026-06-12

## 业务边界

- 自筹资金反映承包人与公司的资金责任关系，项目用于归属、约束和追溯，不改变“公司-承包人”责任主体。
- 自筹垫付、自筹退回是独立办理事实，不进入普通收付款申请；`payment.request` 只承载收付款申请意图。
- 正式自筹办理完成后进入 `sc.treasury.ledger`，资金台账通过 `source_model/source_res_id` 追溯 `sc.self.funding.registration`，不写 `payment_request_id`。
- 自筹退回必须受公司-承包人自筹未退余额约束，不能超过已形成的未退责任余额。
- 旧系统历史事实继续由 `sc.legacy.self.funding.fact` 承载，作为责任余额和历史追溯来源；新发生业务走正式办理单据。
- 系统币种口径确定为人民币 CNY；业务办理不再把币种作为用户选择项。

## 功能入口

- `finance.self_funding.income`：自筹垫付办理，目标模型 `sc.self.funding.registration`，完成动作 `action_done`。
- `finance.self_funding.refund`：自筹退回办理，目标模型 `sc.self.funding.registration`，完成动作 `action_done`，余额约束 `self_funding_balance`。
- `finance.responsibility.self_funding_income/refund`：责任事实视图，只读追溯公司-承包人责任来源。
- `finance.responsibility.company_contractor.balance`：公司-承包人资金责任余额，聚合到款、自筹、付款、扣款等办理事实。

## 迭代原则

- 优先闭合有真实用户业务数据的能力域，先办理、再台账、再报表。
- 菜单入口可以整合，但业务类别必须字典化，动作域和表单分组按用户数据口径切分。
- 报表不得反向定义办理逻辑；办理单据、责任事实、资金台账口径一致后再收口报表。
- 验证优先使用增量、按需的业务闭环脚本和 HTTP 表面 smoke；浏览器验证只在需要真实页面证据时使用。

## 本轮验收命令

- `DB_NAME=sc_demo make verify.self_funding.handling.audit`
- `DB_NAME=sc_demo scripts/ops/validate_finance_business_category_runtime.sh`
- `DB_NAME=sc_demo make verify.finance_handling.http_surface.smoke`
- `DB_NAME=sc_demo make verify.company_contractor.responsibility_http.smoke`
