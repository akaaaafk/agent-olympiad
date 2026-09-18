# work 显式目标题的进展统计与自动切题修复

日期：2026-09-18。仅离线验证，无模型 API、远程评测或历史比赛重跑。

## 修复范围

`src/contest_engine.py::_apply_agent_action` 原先在动作执行前只保存
`session.active_task`。但 `work(problem_id=...)` 可以在同一动作中切换题目并写入。
因此写入实际成功后，引擎仍比较旧题的版本数，漏记实际目标题的进展，也未触发
single-agent/decentralized 已有的“保存草稿后切到下一未作答题”机制。

现在仅对带非空 `problem_id` 的 `work`，按显式目标题保存写入前状态，再使用
同一题对象检查写入后变化。原 dispatcher 继续负责目标存在性、权限、内容绑定、
长度和其他运行时校验；没有提前执行动作或放宽权限。

未改变：

- 任一模式的轮数、API/token 配额、选题计费、失败动作计费。
- 模型提示、OTC 策略、独立审阅、截止交卷或评分器。
- 重复草稿的去重规则、被拒绝写入的无变更语义。
- 历史结果及分数。新版本实跑验证须使用新输出目录；源文件哈希已改变。

编程 OTC 的 `work` 仍只是笔记，不会因此生成可执行源码；对应的工作访问记录
现在归到实际目标而非旧题。centralized/OTC 只修正进展归属，不开启普通基线的自动切题。

## 回归验证

新文件：`tests/test_work_target_scheduling.py`。

1. 修复前运行原始 10 个回归用例：**10 failed**；其中完整轮次复现首题重复停留。
2. 应用源代码修复后，相同命令：**10 passed**。
3. 扩充边界后：**27 passed**。覆盖首次无当前题、跨题、不同历史版本数、去重、
   未知题号、内容题号冲突、超长、分工权限、五种基线、编程笔记及 checkpoint 恢复。
4. 相关协议、编程和 run identity 联合测试（扩充分工权限测试前）：
   **70 passed，36 subtests passed**。
5. 全套测试：**1783 passed，1345 subtests passed**，耗时 261.17 秒，退出码 0。

离线模型替身驱动真实引擎/动作验证/写入/截止交卷路径：

- single-agent：直接 `work(problem_id=...)` 开始，10 轮、10 次模拟 API，
  10 题各保存一次并交卷，没有额外选题轮。
- decentralized：6 个席位，2 轮、12 次模拟 API，12 题各保存一次并交卷。

这是确定性机械链路测试，不是模型能力、实际覆盖率或得分承诺。

命令：

```powershell
& 'E:\agent_olympiad\.venv\Scripts\python.exe' -m pytest tests/test_work_target_scheduling.py -q
& 'E:\agent_olympiad\.venv\Scripts\python.exe' -m pytest tests -q
```

## 仍需区分的问题

此前检查的 13 场、32 道空白题都没有已保存草稿，而且都从独立
`select_problem` 开始，因此不能把这些历史空白归因于此次修复。
独立选题仍占一轮；动作恢复耗尽仍可能损失该席位作答机会；15 题/10 轮仍不保证
完成；同轮数但不同团队人数、无总调用/token 上限仍不等于等计算预算。
以上属于另需明确口径的行为，没有在此次修复中顺带调整。

源码修复前备份：`tmp/work_target_scheduling_before_20260918_1100/contest_engine.py`。
机器可读验证记录：`results/work_target_scheduling_20260918/validation.json`。
防止复发的关键是测试真实跨题写入和调度的组合，而不只测试答案保存或当前题写入。
