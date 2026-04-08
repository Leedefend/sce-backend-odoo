# Contract Runtime Settlement Action-Surface Compare v1

## Scope
- base_url: `http://localhost:8069`
- db_name: `sc_demo`
- roles: `owner, pm, finance, outsider`

## Role observations
- `owner` payment_actions=0 settle_intent_hits=0 settle_intent_ready_buttons=1
- `pm` payment_actions=0 settle_intent_hits=0 settle_intent_ready_buttons=1
- `finance` payment_actions=4 settle_intent_hits=0 settle_intent_ready_buttons=1
- `outsider` payment_actions=0 settle_intent_hits=0 settle_intent_ready_buttons=1

## Aggregated evidence
- payment action-surface roles with actions: `1/4`
- settlement dedicated-action intent hits: `0`
- settlement ui.contract intent-ready button hits: `4/4`

## CRG-004 closure classification
- classification: `CLOSED`
- 解释：payment 与 settlement 均存在可观测 action surface，CRG-004 可收口。
