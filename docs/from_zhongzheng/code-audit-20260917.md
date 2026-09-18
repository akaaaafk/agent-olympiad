# 其他代码审计（2026-09-17）

后续状态：下述分析配对问题已修复，旧测试清理与验证见 [修复记录](analysis-repair-20260917.md)。下文保留修复前的审计证据。

范围：`src`、`scripts`、全部 140 个 `test*.py` 模块。检查执行器、提交与评分、模型传输、记忆边界、恢复身份及结果分析。本轮未启动付费实验；全量测试进程禁止外部 socket 连接。

## 已复现、尚未修改的代码问题

`src/analyze_runs.py:62` 的 `_comparable_key` 仅使用 competition、problem_id、task_id、team、model_label、model、rules_mode；没有比较 provider、temperature、轮数、token/API 预算或完整实验配置。

最小复现：同名模型的 solo、subagent、team 三条记录分别使用不同 provider，温度为 0.2／0.6／1.0，轮数为 10／30／90，分数为 0.4／0.6／0.8。脚本仍输出 division_gain=0.2、cohesion_gain=0.2，gain_reason=null。这样的比较不能据此归因于协作方式。

同文件 `group_summaries` 的分组字段更少，也可能把不同实验设置混合求均值。这属于旧分析入口的问题，并不证明主 pipeline 的单场判分或恢复身份检查失效。

复现输入和结果：`tmp/code_audit_analysis_repro.json`。后续应使用明确的可比设置字段分组，对缺少身份信息的历史记录明确标记；不能直接要求三种 condition 的整个指纹相同，因为 condition 本身就是对照变量。

## 更新的旧测试

仅修改了四个测试文件，共对应五处旧失败：

- `test_computer_capacity.py`：显式 1 轮按新规则应得到 10。
- `test_vanilla_team.py`：按实际 10 轮准备响应和 API 预算，保留普通 prompt 边界及最终合成只额外计费一次的断言。
- `test_programming_judge.py`：允许新预算下的中间行动，保留最终只合成一次、提交完整源码且不使用数学答题纸 prompt 的检查。
- `test_readiness_routes.py`：构造明确的 not_ready 测试题包，保留 live 入口拒绝和不写输出的断言，不再假定当前 IIOT 数据永远未就绪。

本轮没有修改生产运行代码，也没有更改数据 readiness。

## 验证结果

- 282 个源码／脚本 Python 文件语法检查通过。
- 首轮全量：1066 项，无跳过，1061 通过、3 FAIL、2 ERROR；五处均为上述旧测试条件。
- 更新测试后，受影响四个模块共 26 项全部通过。没有为制造“全量绿”重复运行未受影响的 1040 项。
- 首轮日志：`tmp/code_audit_full.log`；结构化结果：`tmp/code_audit_full.json`。
- 修正后日志：`tmp/code_audit_fixture_recheck.log`。

离线测试通过不能替代真实模型、Docker 服务和远程裁判的端到端运行验证。上述旧分析入口的可比性问题仍然存在，现有测试未覆盖这个复现。
