# Setting / Baseline / OpenAgents 审计

> 本文保留初始审计状态。文中列出的测试失败和错误已在后续修复中解决；当前结果见
> [修复报告](settings-baselines-repair-20260914.md)，扩大审计 481 项测试全部通过。

审计对象：`E:\agent_olympiad\agent-olympiad`，2026-09-14。
检查当前文件、运行入口、运行时边界与离线回归；不重跑历史付费实验。

## 结论

五个 baseline 的主要行为通过独立预设和运行时开关分开，公共执行器可以共享。
这不是五份彼此复制的代码，也不应该把共享评分、题目输入和工具基础设施算成混用。
本次发现并修复了普通 baseline 接收规则卡、显式 baseline 落入旧入口的实际缺口。
但整个仓库尚不能判定为全部通过：预算、协议快照和旧 OpenAI/GLM 测试存在不一致。

Setting 有有效配置和恢复指纹，但没有一个统一的实验配置文件统管所有入口。
只凭 `model`、`system_variant` 或目录名不能确认实验可比。

## 五个 Baseline

| 维度 | single_agent | decentralized | centralized | vallina_otc | otc |
| --- | --- | --- | --- | --- | --- |
| 人数 | 固定 1 | 多人 | 多人，至少 2 | 规则卡默认人数 | 同左 |
| 组织 | 独立完成 | 无指定队长 | Agent_1 分配工作并提交 | 一次外部盲 Coach | 同左 |
| 规则卡 | 禁止附带，off | 同左 | 同左 | enforced | enforced |
| 独立审核预设 | 关闭 | 关闭 | 关闭 | 开启 | 开启 |
| 队内私信 | 无 | 无 | 有 | 有 | 有 |
| 显式 memory 工具 | 无 | 无 | 无 | 无 | 有 |
| automatic memory | 无 | 无 | 无 | 无 | 有 |
| 上下文 | 普通草稿与对话 | 普通草稿与对话 | 普通草稿与对话 | 当前团队轮次 | 可见历史与记忆 |
| 提交主体 | 单个参赛者 | 合法参赛者 | 队长 | 规则卡角色与运行时门控 | 同左 |

定义：`src/contest_config.py::BASELINES`。
`vallina_otc = replace(BASELINES['otc'], memory_actions=False)`。
这个开关还控制跨轮观察和自动记忆，不能解释成“仅从工具列表删掉三个名字”。
普通 baseline 没有 memory 模块，不代表其普通对话和答案历史每轮清空。
审计日志中保留历史，也不代表历史向参赛 agent 开放。

`vanilla` / `vanilla_team` 指向 `decentralized`；`vanilla_otc` 指向拼写保留的
`vallina_otc`；`strategic` / `open_table_coach` 指向 `otc`。这些不是额外 baseline。

`require_review`、`require_final_review` 和直接传入的 `features` 支持实验覆盖。
因此上述表格描述预设；报告实验时仍须读取保存的实际 `baseline` 开关。

## Setting 在哪里

| 配置层 | 当前入口 | 隔离 / 比较要求 |
| --- | --- | --- |
| 题目与任务顺序 | contest manifest + benchmark | manifest 内容参与指纹 |
| baseline | contest_config.py | 规范名称、实际 features、人数、审核开关参与指纹 |
| 规则 | data/rules + rules_root | 附带卡内容哈希；普通 baseline 不附带卡 |
| 原生比赛预算 | contest_budget.py + CLI overrides | max_turns、token/API 上限、模拟时钟需逐项比较 |
| artifact 预算 | otc_artifact_pipeline.py | 使用卡的 simulation rounds，minutes_per_turn=0；和原生时钟不是同一含义 |
| 模型与采样 | CLI + llm.py + 环境变量 | solver provider/model/temperature/output cap 分开记录 |
| OpenAgents | configs/providers/openagents.json | 独立 key/model/base_url 环境变量，显式 CLI model 优先 |
| 辅助评分 | judge_provider / judge_model / flags | 与 solver 分开；不能把 solver provider 当作 judge provider |
| 输出与恢复 | contest_run_identity.py | manifest、实际配置、所有 src Python 内容哈希等参与指纹 |
| 底层引擎恢复 | contest_engine.py::_runtime_settings | 检查运行时特性、规则卡及 memory/observation 版本 |

原生入口未指定 judge provider 时，除 Tinker 特例外仍默认 Perplexity。
artifact 入口默认 judge 跟随 solver；两个入口的默认值不同。
`scripts/run_pipeline.py` 固定运行 OTC，并默认显式传入 `openai/gpt-5.4-mini`；
它不是五 baseline 通用矩阵。调用批处理时须同时检查 provider 与 model 参数。

## 本次修复

1. **普通 baseline 规则卡泄漏。** CLI 原先允许 `prompt_only`，直接构造配置还能
   附带卡。这与当前文档和边界测试不符。现于 CLI 和 `ContestRunConfig` 两层拒绝。
2. **artifact 入口附带规则卡。** 原先对五种 baseline 一律传入 card。现仅 OTC
   两种预设附带；公共 deliverable、渲染与 rubric 仍由环境单独解析。
3. **显式 baseline 落入 legacy。** `--system-variant` 没有 manifest 时原先可能继续
   旧 per-problem 路径。现启动时拒绝，支持 `--system-variant=value` 形式。
4. **OpenAgents 正式入口。** 新增实际被读取的 provider JSON、主 CLI solver/judge
   选项、Chat Completions 适配、文本调用、native tools、usage 字段转换与附件适配。
5. **服务配置隔离。** 使用 `OPENAGENTS_*`；仅没有专用 key 且仓库本地旧块明确
   指向该网关时兼容旧 `OPENAI_*`。不会借用 shell 中另一服务的 OPENAI key。
6. **网关恢复隔离。** OpenAgents endpoint 和 API 类型进入 solver/judge 指纹；
   改 endpoint 后不能复用旧结果。密钥不写入指纹，正常换 key 不改变实验身份。
7. **未知 solver 不再静默走 Perplexity。** `_make_live_query` 对未支持的 provider
   明确拒绝；OpenAgents 有独立适配分支。
8. 调整两处旧测试 fixture：普通 baseline 的 pending-source 测试不再附带卡；
   规则卡 allowlist 测试改用 OTC。保留原本的 source lock / allowlist 断言。

## 仍存在的遗漏与不一致

### P1：预算 / 协议定义没有统一

`src/contest_budget.py::turns_for_duration` 当前四舍五入，范围 1 到 90；
ARML Local 默认 9 轮、National Team 默认 4 轮，未知比赛默认 60 分钟 / 12 轮。
多个长赛使用 30、60 或 120 分钟一步。
但 `test_contest_budget.py` 和 `test_computer_capacity.py` 要求至少 10 轮、向上取整、
统一 5 分钟一步、未知赛 90 轮；`test_contest_settings.py` 还要求 `submission_turn`。
当前 `ContestRunConfig` 没有这个属性，协议仍是 `contest_session_v11`；
`test_contest_engine_replay.py:231` 已要求 v12，20 个 replay 子场景在版本检查失败。

这说明当前源代码与部分测试不是同一套协议定义。没有为通过测试而把 v11 标签改成
v12，也没有改比赛预算或覆盖历史快照。需先确定采用哪套预算/结束语义，再完整实现。

### P1：旧 GLM / OpenAI 适配的测试要求未实现

`tests/test_action_transport.py` 要求旧 OpenAI caller 接受 temperature、处理 GLM
隐藏推理，以及输出截断后增加预算重试；当前旧 caller 和 action transport 缺少这些能力。
本次 OpenAgents 路径独立接通，但不等于这些旧路径缺口已修复。
截断输出会明确失败，不会把不完整 tool arguments 当作合法行动执行；自动扩预算
重试和所有失败调用的精确 usage 保留仍需统一设计。

### P2：artifact 与原生 setting 默认值不可直接等同

artifact 使用规则卡 simulation rounds，并未暴露与原生 CLI 完全相同的 temperature
选项；其 identity 也未显式保存该固定采样值。两种入口的预算和 judge 默认选择不同。
这些不是 baseline 混用，但会使跨入口结果不满足严格 matched setting。

### P2：旧分析入口的可比性键过窄

`src/analyze_runs.py::_comparable_key` 包含任务、team、model 和 rules_mode，
不包含 provider、temperature、预算或协议指纹。它是旧结果分析路径，不能作为当前
比赛配对结果已经同 setting 的证明。当前导出应以保存的实际 identity 为依据。

### P3：部分测试 / 说明已过时

`test_memory_activation.py` 搜索 `ACTIVE MEMORY USE:`，当前 prompt 使用
`AUTOMATIC CONVERSATION MEMORY`、`MEMORY DECISION` 与 `MEMORY CONTROL`。
实际记忆说明和工具仍存在，不能把这个字符串断言失败解释成记忆全部失效。
`test_pipeline_entry_guards` 有 Windows 路径盘符大小写断言差异。
旧 `docs/vallina-otc.md` 描述早期 basic Coach 分支；README 已明确标为历史说明。

## 验证范围

本次修改相关的 71 项测试全部通过：OpenAgents provider、普通 baseline 边界、
主入口、五种 delivery route、artifact 渲染/评分、source guards、比赛工具和 run identity。
包含五 baseline 的 gateway 配置解析、跨 endpoint 禁止复用、密钥隔离、工具 schema
转换、token 字段、PDF 指定页转图片，以及不改历史结果的恢复检查。

更广的离线审计结果保存于 `tmp/settings_audit_final_20260914.json` 和同名 `.log`。
该轮执行 446 项测试，记录 33 个失败断言、7 个错误断言，无跳过。
随后对最终改动单独执行的 71 项相关测试全部通过；新增的未知 provider 拒绝测试包含
在这 71 项中。不能据此把更广审计中的已有失败当作已解决。
复现命令：

```powershell
E:\agent_olympiad\.venv\Scripts\python.exe .codex_tmp\audit_runtime_settings_20260914.py
```

这是明确列出的运行时测试集合，非所有数据修复脚本的全仓验证；全量 discovery 在收集
阶段长时间没有测试进度后已停止。失败统计包含 unittest 子测试，不能直接从总测试数
减去失败断言数得出“通过 test method 数”。没有重写历史结果、replay 快照或记忆文件。

## OpenAgents 实测与用法

- `glm-5.2`，temperature=0.2：真实认证文本请求成功，返回非空文本。
- 同模型 native tools：真实返回一个 `rest` 调用，usage 为 input 148 / output 26。
- `kimi-k2.6`，temperature=0.2：HTTP 400，网关提示必须 temperature=1；
  未静默改变采样参数。默认 profile 因而使用已验证的 `glm-5.2`。
- 32-token 文本探针发生截断，512-token 文本探针成功；这不是认证失败。
- PDF 到图片和页范围已离线测试；没有据此声称真实模型的视觉理解已验证。
- 没有启动完整生产比赛；这些 API 请求仅验证 provider 连通与协议。

入口与完整示例见 `configs/providers/README.md`。主比赛命令核心参数：

```text
--provider openagents --model glm-5.2
--judge-provider openagents --judge-model glm-5.2
--system-variant vallina_otc --contest-manifest <manifest> --output <fresh-output>
```

对照组改为 `otc` 并使用另一新目录，其他任务、人数、预算、采样、Coach brief 和
judge setting 保持一致。更换 provider 不会自动更换 baseline。
