# QANTA 答案批注修复

已修复主数据62条错误答案编码，并同步mini中的8条。100条QANTA主答案均通过现有评分函数验证。记录数量、题面、分值和last_exam没有改动。

逐条核对原始QANTA记录，将答案正文与可接受别名分开；原始批注保留在judge侧provenance中。更新主/mini curated short-answer mappings，防止重建时回退。原始upstream answer key保留原文作为来源证据。

仅加入原文明确、无条件接受的别名；不把提示后追问、限线索时点的答案转为无条件接受。不实现开放式语义近似匹配。修复DoÃ±a到Doña的可逆乱码。评分仍为完整题面下的最终回答评分，不是抢答时序或主持人交互复现。

验证：100条记录共408项实际adapter判分检查通过；4个回归测试及19个子测试通过。检查主答案、别名、空答、错误答案、明确禁止答案和主/mini答案映射一致性。

- 实施脚本：`scripts/repair_qanta_answerlines_20260917.py`
- 逐条证据：`tmp/qanta_answerline_repair_20260917.json`
- 回归：`tests/test_smoke_gold_encodings.py`

没有付费模型调用，没有重写历史实验结果。下一项：IOL 2014多PDF题包接入。
