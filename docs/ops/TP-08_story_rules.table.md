# TP-08锝滃彊浜嬩笌杞彁绀鸿鍒欒〃锛堥鏋讹級

> 鏈〃鐢ㄤ簬鎶?TP-04 / TP-05 瑙勫垯杞负鈥滃彲鎵ц琛ㄦ牸鈥濄€?
| rule_id | level | condition | fields | message_template | fallback |
| --- | --- | --- | --- | --- | --- |
| N-01 | narrative:y | lifecycle_state='in_progress' AND cost_budget_gap < 0 | lifecycle_state, cost_budget_gap | 椤圭洰鎴愭湰宸茶秴鍑洪绠楋紝褰撳墠瀛樺湪鎴愭湰鍘嬪姏銆?| 鑻?cost_budget_gap 缂哄け鍒欎笉鎻愮ず |
| N-02 | narrative:g | lifecycle_state='in_progress' AND cost_budget_gap >= 0 | lifecycle_state, cost_budget_gap | 椤圭洰鎴愭湰澶勪簬棰勭畻鑼冨洿鍐咃紝缁х画淇濇寔銆?| 鑻?cost_budget_gap 缂哄け鍒欎笉鎻愮ず |
| N-03 | narrative:y | pay_settlement_total > 0 AND pay_paid_total = 0 | pay_settlement_total, pay_paid_total | 椤圭洰宸茬粨绠椾絾鏈粯娆撅紝寤鸿鍏虫敞璧勯噾瀹夋帓銆?| 鑻ヤ换涓€瀛楁缂哄け鍒欎笉鎻愮ず |
| N-04 | narrative:b | progress_rate_latest = 0 AND progress_entry_count = 0 | progress_rate_latest, progress_entry_count | 褰撳墠鏆傛棤椤圭洰杩涘害鏁版嵁锛屽缓璁ˉ鍏呰繘搴︿俊鎭€?| 鑻ョ己澶辨爣璁颁笉鍙敤鍒欎笉鎻愮ず |
| N-05 | narrative:b | document_completion_rate < 0.8 | document_completion_rate | 椤圭洰璧勬枡涓嶅畬鏁达紝璇疯ˉ榻愬叧閿祫鏂欍€?| 鑻ユ枃妗ｆ寚鏍囩己澶卞垯涓嶆彁绀?|
| N-06 | narrative:b | contract_count = 0 | contract_count | 褰撳墠椤圭洰鏆傛棤鍚堝悓淇℃伅锛岃纭鏄惁宸插畬鎴愬綍鍏ャ€?| 鑻ュ悎鍚屾暟閲忕己澶卞垯涓嶆彁绀?|
| W-01 | warning:y | cost_budget_gap < 0 | cost_budget_gap | 鎴愭湰宸茶秴棰勭畻锛屽缓璁叧娉ㄦ垚鏈帶鍒舵帾鏂姐€?| 鑻?cost_budget_gap 缂哄け鍒欎笉鎻愮ず |
| W-02 | warning:y | pay_settlement_total > 0 AND pay_paid_total = 0 | pay_settlement_total, pay_paid_total | 瀛樺湪宸茬粨绠楁湭浠樻鎯呭喌锛屽缓璁叧娉ㄤ粯娆捐鍒掋€?| 鑻ヤ换涓€瀛楁缂哄け鍒欎笉鎻愮ず |
| W-03 | warning:b | progress_rate_latest = 0 AND progress_entry_count = 0 | progress_rate_latest, progress_entry_count | 鏆傛棤杩涘害鏁版嵁锛屽缓璁ˉ鍏呰繘搴︿俊鎭€?| 鑻ョ己澶辨爣璁颁笉鍙敤鍒欎笉鎻愮ず |
| W-04 | warning:b | document_completion_rate < 0.8 | document_completion_rate | 璧勬枡瀹屽鐜囧亸浣庯紝寤鸿琛ラ綈鍏抽敭璧勬枡銆?| 鑻ユ枃妗ｆ寚鏍囩己澶卞垯涓嶆彁绀?|
| W-05 | warning:b | contract_count = 0 | contract_count | 褰撳墠椤圭洰鏆傛棤鍚堝悓淇℃伅锛岃纭鍚堝悓鏄惁宸插綍鍏ョ郴缁熴€?| 鑻ュ悎鍚屾暟閲忕己澶卞垯涓嶆彁绀?|

## 璇存槑

- condition锛氭槑纭Е鍙戞潯浠讹紙瀛楁 + 姣旇緝锛?- fields锛氬垪鍑轰緷璧栧瓧娈碉紙鍙В閲婏級
- fallback锛氱己澶卞€兼椂鐨勯粯璁よ涓猴紙鏃犳彁绀?鎻愮ず锛?
