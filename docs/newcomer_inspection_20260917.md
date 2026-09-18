# 新用户视角检查：code、data、interface

检查日期：2026-09-17（America/New_York）。检查对象：本地 `agent-olympiad` 主 checkout。

**修复状态：本报告的七项问题已逐项处理。** 详见
[修复与验证记录](newcomer_repairs_20260917.md)。干净环境全量测试为
1192 passed / 1341 subtests passed，mini 离线准备为 445/445。
以下内容保留为修复前的检查证据，代码行号、984 条主库统计和失败数字均属于当时快照，
不能当成当前故障清单。当前主库重新审计为 39 tracks / 977 records。

结论：主路径已有较完整的动作、运行身份、数据隔离和评测边界，但目前不能宣称整个项目已经开箱即用。新 provider 的异常恢复与计费存在可复现缺口；全量测试被导入副作用污染；首屏入口文档、安装依赖与部分数据说明不一致。之前的 Tinker smoke 不能替代这些检查。

本次为 inspection，未实施生产修复，未启动付费模型实验。新增审计工件存放在 `results/newcomer_inspection_20260917/`。接口复现全部使用模拟 HTTP 响应；其结论是代码对给定响应的行为，不能解释成真实服务上已观察到的发生频率。

## 优先处理的问题

### 1. P1：Gemini 的思考 token 在缺少候选计数字段时被漏记

- 位置：`src/public_providers.py:163-167`；`src/contest_engine.py:1280-1284`。
- 触发：响应包含 `thoughtsTokenCount=500`，没有 `candidatesTokenCount`，结束原因为 `MAX_TOKENS`。
- 原因：只有存在 `candidatesTokenCount` 才写入统一的 `output_tokens`。引擎随后用空工具调用列表 `[]` 估算，得到 1。
- 实际复现：同一次模拟调用，provider 原始 usage 为 500 个思考 token，最终 `contest['budget']['tokens_used'] == 1`。
- 影响：输出预算和实验用量统计失真；重复触发时，运行器会把已经消耗的预算当作仍可用。
- 建议：分别处理候选和思考计数；保留已知计数，不能因为另一个字段缺失而丢弃它。缺失用量应明确标记，不能把未知输出默认为空调用列表的长度。
- 证据：`interface_reproductions.json` 的 `gemini_thought_only`；可运行 `reproduce_interfaces.py` 复现到真实 contest engine。

Google 的文档分别定义候选与思考 token，说明思考模型的输出费用包含二者；文档本身没有证明本地所用账号会返回上述缺字段情形。因此这里是已经复现的适配器边界缺陷，发生频率尚未验证。[Gemini 用量说明](https://ai.google.dev/gemini-api/docs/generate-content/tokens)、[响应字段定义](https://ai.google.dev/api/generate-content#UsageMetadata)。

### 2. P1：非法 native 参数会直接中断运行，usage 没有交回引擎

- 位置：`src/public_providers.py:98-101` → `src/llm.py:191-208` → `src/contest_engine.py:1223`。
- 触发：DeepSeek / OpenAI-compatible 返回 `finish_reason=tool_calls`，但 function arguments 不是合法 JSON。
- 实际复现：HTTP mock 返回一次带 `completion_tokens=500` 的响应，随后抛出 `ValueError: Function-call arguments are not valid JSON.`。`run_contest` 整体没有返回结果。
- 原因：解析在构造 `LLMResponse` 前抛错；引擎没有收到该次调用的 usage，也没有把它作为可记录的失败动作处理。
- 影响：一个格式错误就能终止单个比赛 job；该响应的 token 无法进入正常的动作计费与日志流程。
- 建议：在适配器边界将可识别的响应解析错误转换成带 usage 的失败响应，继续保持零动作执行；是否重试交给有预算约束的统一控制器。
- 证据：`interface_reproductions.json`、`malformed_arguments_engine.json`。未执行任何坏参数，也未发起真实请求。

### 3. P2：新 provider 的截断恢复语义不一致

- 位置：`src/action_transport.py:37-46`；`src/public_providers.py:132-137,174-177`。
- 原因：通用控制器只识别 `finish_reason == 'length'`；Anthropic 保留 `max_tokens`，Gemini 保留 `MAX_TOKENS`，因此两者直接返回零动作错误，不进入同请求恢复分支。
- 在相同的“先截断、第二次正常”模拟序列中，且 API/token 预算都充足：

| Provider | 实际请求数 | 返回给引擎的完整动作数 |
|---|---:|---:|
| Anthropic | 1 | 0 |
| Gemini | 1 | 0 |
| DeepSeek | 2 | 1 |
| OpenAI-compatible | 2 | 1 |

- 截断后的不完整动作均未执行，这是正确的；问题是 provider 之间失败分类和恢复策略不统一。
- Tinker 的 `transport_recovery_managed` 独立处理阶段采样与续写，本问题不能倒推成 Tinker 最新机制失效。
- 通用 native 重试是重新请求完整动作，并非 Tinker 的精确 token 续写。也不能通过无条件加大预算解决。
- 建议：统一内部结束原因，同时保留 provider 原始标记；只对 token 截断启用有预算的恢复，拒绝/内容过滤等原因保持分离。
- 证据：`interface_reproductions.json` 的 `truncation`。

### 4. P1：测试收集就会把全进程的数据根目录改成 mini

- 位置：`tests/test_reviewed_pdf_judge_repair.py:11` 导入 `scripts/repair_reviewed_pdf_judges.py:19`。
- 原因：脚本在模块顶层执行 `os.environ['AGENT_OLYMPIAD_DATA_ROOT'] = .../data/mini_data`，导入后不恢复。
- 证据：只运行 `pytest --collect-only` 就捕获到这条赋值及完整调用栈，见 `environment_mutation.log`。
- 全量运行因此让 NYU CTF 测试去 mini 找仅主库拥有的题，让 HMMT Guts fixture 去 mini 找不存在的 roster。
- 8 项 CTF 失败和 1 项流程失败在独立进程中均通过。不能把它们解释成 Docker 环境坏了或 9 个生产功能都坏了。
- 更深的风险是：其他基于动态 `data_root()` 的循环测试即使通过，也可能只测了 mini，覆盖范围比名称暗示的小。
- 建议：数据根选择放到 CLI `main()` 或显式配置上下文中；可导入辅助函数保持无全局环境副作用。测试需隔离并恢复环境，不能靠执行顺序掩盖。

### 5. P2：新人首个运行指南已损坏，文档中的“当前”版本相互冲突

- `README.md:20` 直接链接 `docs/from_zhongzheng/mini_pipeline_powershell.md`。该文件 UTF-8 内容包含 **580 个字面问号、0 个中文字符**；标题就是 `# Mini pipeline PowerShell ????`。这不是终端显示问题。
- 该指南第 10-11 行硬编码本机 checkout 和虚拟环境路径。其他机器不能直接复制使用。
- `README.md:112` 仍称当前 OTC 为 protocol v6；当前代码使用更新协议。
- `docs/TESTS_AND_RESULTS.md:17` 将 20 families / 525 records 标为 current，28 行称每名 agent 每 turn 最多一次模型调用；152、193 行将旧 smoke 标为 current。文件虽包含历史日期，仍容易与现在的 39 tracks、重试/辅助调用机制混淆。
- `docs/contest-run-reuse.md` 的旧规则模式说明允许非 OTC 使用 `prompt_only`，而当前 `src/run_competition_batch.py:1083-1085` 要求三个普通 baseline 使用 `off`。
- 建议：首屏只给一个可移植的当前 quickstart；历史文档明确标为历史，不覆盖既有历史结果。已有完整的 `mini_dataset_commands_20260916.md` 可作为整理依据。

### 6. P2：验证环境与声明的安装环境不相同

- `requirements.txt:3` 固定 `tinker==0.26.1`，当前实验 Python 环境实际为 **0.29.0**。
- `requirements.txt:22` 声明 `imageio-ffmpeg>=0.4.9`，当前解释器未安装。其他声明的依赖版本均满足。
- `pip check` 通过，只能说明已安装包的依赖没有报告冲突；README 对这一点的说明是正确的。
- 影响：不能用本机已通过的 smoke 证明“新人按 requirements 安装”得到了同一环境。
- 尚未证明 Tinker 0.26.1 不兼容，也未对活动环境执行降级或安装。
- 建议：选定要支持的版本，在独立干净环境验证安装和代表路径；保存实际依赖版本。不要直接把活动实验环境改掉。
- 证据：`environment.json`。

### 7. P2：mini CTF 的 readiness 说明存在同一字段内的矛盾

- 将路径前缀 `data/mini_data/` 归一化为 `data/` 后，对照 mini 的全部 109 条记录与主库同 ID 记录。
- `problem_description`、`gold_label`、`metadata`、`source_review` 在所比较字段中一致；**15 条**记录的 `evaluation` 不同，涉及 Cybench 8 条、NYU CTF 7 条。
- 版本快照不同本身不是错误。具体问题是 mini 的 `limitations` 同时保留“没有环境/尚未验证”和“2026-09-16 mini Docker 启动、TCP、exact flag grading 已验证”的说明，缺少明确的历史/当前分层。
- 主库当前记录已使用新的 runtime validation 报告及更精确的“启动检查不保证解题成功”说明。
- 影响：新人无法从单条记录判断到底是缺环境、只做了启动验证，还是已经确认评分接口可用。
- 建议：保留来源与历史，但给出单一明确的当前状态及验证边界；若同步新快照，重新生成 hash/derived 包并保留旧实验身份，不能直接覆盖历史证据。
- 证据：`mini_main_row_comparison.json`；两个 catalog 的 CTF `evaluation` 字段。

## 数据检查的实际覆盖

| 检查 | 本次结果 | 能证明什么 |
|---|---|---|
| 主库活跃目录 | 39 tracks / 984 records | 当前 catalog 数量，非历史统计 |
| 主库 readiness | ready 441；ready_with_limitations 276；remote_judge_ready 158；not_ready 109 | 分类存在，不能把全部记录称为可直接运行 |
| 主库文件与派生包审计 | 11,700 个独立文件哈希；1,225 个声明 PDF 文件头；0 个结构问题 | 文件、声明哈希、scorecard、base/last_exam 成员与投影一致 |
| mini 目录 | 39 tracks / 109 records / 89 sessions | mini 不是每类只有一道最小子题 |
| mini 离线准备 | 89 sessions × 5 baselines = 445，全为 prepared | 当前环境下命令与准备阶段可通过，不等于 445 次模型运行 |
| mini 资产 | 479 次资产检查；0 缺失/越界/hash 错误；0 越界读取主 data | 这条离线准备路径的依赖隔离 |
| mini dependency snapshot | 0 drift | mini 自身绑定一致；不代表与主库永远同步 |
| main package membership | 0 issues | main 与派生包成员一致 |

主库审计结果在 `output/newcomer_inspection_20260917/catalog/before.json`；`before` 是该脚本要求的标签，不是拿旧报告充当本次结果。审计结束后重新比较其 `source_snapshot`，未发现这些 benchmark 文件随后发生变化。

还剩两类自动审计候选不能机械计为 bug：

- 12 个 HMMT Team 总分与 gold 子集权重不等：抽查显示采用 `gold_else_llm_v1`，另一些题由 proof rubric 评分，不能要求 gold 子集本身等于整场总分。
- 9 条 CTF 存在 public/judge 资产相同字节的候选：相同哈希本身不能证明泄漏答案，需要按共享资产内容判断。本轮没有逐个做语义裁定。

本轮没有逐页校对全部 PDF 的公式，也没有对全部 ready 项做真实解题/评分。因此 0 个结构问题不能表述成“所有题面、规则和评分都完全正确”。IIOT 静态代码审阅、开放报告 rubric 等 proxy 路径也不能解释成原赛事官方测试成绩。

## 测试结果如何解读

原始命令：

```powershell
& E:\agent_olympiad\.venv\Scripts\python.exe -m pytest tests -q --junitxml=results/newcomer_inspection_20260917/tests.xml
```

收集 1,153 项；pytest 原样汇总：`12 failed, 1142 passed, 1139 subtests passed`，181.24 秒。失败数字包含 1 个 subtest failure，不能把两列简单相加当作收集数量。

| 失败类别 | 数量 | 本次定位 |
|---|---:|---|
| CTF / HMMT 流程 | 9 | 导入时数据根污染；独立复跑通过 |
| Odyssey 数据断言 | 1 | 测试仍 `next()` 查找已经移除的非 synopses 练习项，触发 StopIteration；此前逐条来源/rubric 断言均通过 |
| pending report fixture | 1 | fixture 缺少 `evaluation_pending=True`，进入“已完成评测、再验证”路径；仅在内存补上此字段后通过，未改生产代码 |
| engine 结构约束 | 1 subtest | `_build_result` 长度 263 行，超过测试约定 260 行；是维护性约束失败，不能当作运行失败 |

独立复跑日志为 `isolated_failures.log`（12 passed / 1 failed）；pending fixture 定位见 `pending_fixture_probe.log`。测试绿色不是全新账号可用证明；public provider 测试使用 mock，这一点现有 interface 文档写得准确。

为排除导入串扰影响，还运行了 `pytest tests --ignore=tests/test_reviewed_pdf_judge_repair.py -q`：`3 failed, 1149 passed, 1206 subtests passed`，167.10 秒。剩下的正是两个过时 fixture 和一个函数长度 subtest；9 项 CTF/流程失败消失。结果另存 `tests_without_import_side_effect.log` / XML。此对照排除了一个模块，不能冒充完整套件全绿，也不会覆盖原始失败结果。

## 已有且值得保留的边界

- 新 provider 复用既有 `LLMRequest` / `LLMResponse` / `LLMToolCall` 和动作派发；没有必要为了修接口重新定义竞赛动作。
- 多动作整批拒绝、截断时零动作执行、agent-visible 与 judge-only 附件隔离已有明确检查。
- 模型名需显式指定，provider 的凭据隔离；endpoint 参与运行身份，避免不同服务混入同一实验。
- mini wrapper 明确选择仓库内 `data/mini_data`；离线依赖隔离检查通过。
- resume 使用配置与源码身份校验；当前文档明确源码变化需要新输出。这样的保守拒绝不能当成“断点坏了”。
- contestant 完成与 evaluation 完成分开；已有保存评测与只补缺失评测的机制。本轮没有复现“每次都必须重新跑 contestant / 全量重评”的结论。
- public interfaces 文档明确这里是模型适配器，并非 HTTP benchmark 服务或可安装的完整 benchmark SDK。应按这个真实范围介绍给新用户。

## 建议的后续顺序

1. 修 provider 结束原因、usage 和解析错误边界，增加上述最小复现对应的回归测试；保留 Tinker 的独立续写机制及全局预算约束。
2. 去掉可导入脚本的环境副作用，更新两个过时 fixture，处理既有函数长度约束，再取得可信的全量测试结果。
3. 合并当前 quickstart、验证干净安装环境、整理 mini CTF 的当前状态说明。继续保留历史实验与历史文档来源，不通过修改历史结果制造“全绿”。

这三步属于机械边界、验证和可用性整理；不需要改已经定义的竞赛、baseline、动作权限或评分目标。
