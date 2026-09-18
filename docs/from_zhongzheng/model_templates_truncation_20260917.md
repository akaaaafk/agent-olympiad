# 按模型选择模板及截断恢复

当前修复覆盖 Tinker 模型模板、推理/正文通道、动作选择及参数续写、普通生成和判题的截断恢复。GLM-5.3 与 GPT-OSS 已通过小规模真实工具执行验证；没有声称所有模型都经过真实远端推理，也不保证有限预算下任何输出都能完成。

## 模板

| 模型 | 本地模板 | 动作前缀 |
| --- | --- | --- |
| 已登记且支持关闭 thinking 的 Qwen3 / Qwen3.5 / Qwen3.6 | 所选模型自身 tokenizer 的 chat template，显式 `enable_thinking=False`；已接入的 Qwen3.5/3.6 图像路径用官方 `qwen3_5_disable_thinking` | 支持 |
| Qwen3-Instruct / Qwen3.8 | 官方 instruct / `qwen3_8_disable_thinking` renderer | 支持 |
| DeepSeek-V3.1 | 官方 `deepseekv3` renderer（关闭 thinking） | 支持 |
| Kimi-K2.6 | 官方 `kimi_k26_disable_thinking` renderer | 支持 |
| Llama-3.1-Instruct | 官方 `llama3` renderer | 支持 |
| GLM-5.3（含 peft 后缀） | 官方 `glm5_3_low_reasoning`；不可假装关闭 thinking，解析时剔除推理通道 | 不支持 |
| GPT-OSS | 官方 `gpt_oss_low_reasoning`，解析 Harmony 通道 | 不支持 |
| Kimi-K2-Thinking | 官方 `kimi_k2`，解析 thinking / text | 不支持 |
| Nemotron 3 Nano / Ultra | 官方对应 `disable_thinking` renderer | 支持 |
| 其他已在 cookbook 登记的 chat 模型 | 对应模型的推荐 renderer，优先采用已声明的关闭 thinking 版本，其次 low reasoning | 只有已确认的模板启用 |
| 未登记模型 | 必须由其 tokenizer 提供 chat template，不套用 Qwen 参数 | 默认关闭 |

映射来源为安装的官方 `tinker-cookbook==0.5.7` 的 model_info 和 renderers，参照 [官方 Rendering 文档](https://tinker-docs.thinkingmachines.ai/tutorials/core-concepts/rendering/)。非 Tinker 的托管 Messages/Chat API 仍交给服务端应用模型模板，不在客户端重复包裹。

模型结束符与动作短字符串停止符同时保留。运行 usage 记录模板及模型。Qwen3.6 当前部署使用已核实的 65536 上下文覆盖值；其他模型读取自己的 tokenizer 限制，未知上限不伪装为已核实的服务端上限。

## 截断

- 动作：协议升级为 `staged_raw_arguments_v4_channels`。保留原子校验和分阶段生成；模型策略控制是否能使用 assistant 前缀。未完成的选择、参数、正文不执行。只有已验证非推理前缀的短元数据使用 512 token 上限；推理模型使用配置的采样上限（仍受剩余预算约束）。
- 截断的动作选择与正文一样，在原始 prompt 后追加精确 token IDs 续写，不再每次重开推理。私有检查点保存未执行的 token 缓冲；选择缓冲仅能在相同会话、角色、题目、观察、schema、参数限制下恢复。
- GLM 的开放 `<think>` 和 GPT-OSS 的 analysis 通道不再进入动作 JSON。解析用结束符不会写进采样 token，也不会把 `length` 变成成功；多调用、重复 JSON 键、越权参数仍拒绝。
- 普通回答与判题：原来单次生成截断便结束；现在在同一 system/user/图片条件下追加原始 token 续写，统一扣减调用次数和输出预算。
- 达到恢复次数或 token 预算后仍未完成：返回空成功正文并设置 `tool_error`，只在诊断字段保留未完成文本，避免把残缺答案送去当完整结果。
- 上下文计数包含图片、前缀与原始续写 token。不剪掉题目以强行容纳输出。
- 同一 provider/model 连续 3 次动作请求耗尽恢复仍失败，保存已计费的检查点并报传输故障；不继续截止提交、不生成正常终态成绩，恢复同一故障检查点也不会继续扣费。
- 已知 base 模型提前明确拒绝；未知型号不靠家族名称猜测关闭推理能力。没有配置视觉 renderer 的模型仍遵守原来的 PDF 文本审核/图片拒绝边界。

## 验证边界

`tests/test_tinker_model_policy.py` 分别覆盖 Qwen3.6、DeepSeek-V3.1、Kimi-K2.6、Llama-3.1 的策略、结束符、原始 token 续写和预算耗尽；官方 renderer 使用确定性 tokenizer 测试夹具检查各自角色标记，不冒充这些模型的真实分词或线上结果。

早期版本的 65 项测试不能证明 GLM 已适配；本次补充 `tests/test_tinker_reasoning_transport.py`，先复现失败再修复，覆盖实际 SDK → renderer → 动作装配 → 执行/检查点边界。原始付费整场结果和 last_exam 均未改写。

最终定向回归：**219 项测试、82 个子测试通过**。涵盖 Tinker、公共服务商、OpenAgents、VectorEngine、动作原子性、预算、视觉输入、检查点恢复、比赛执行器与运行身份。JUnit 结果保存在 `results/transport_v4_offline_20260917.xml`。这不是全仓库全部测试，也不是所有远端模型的实测。

真实小探针使用 `scripts/probe_tinker_tool_execution.py`，每次最多 4 次动作采样，每次最多 6144 输出 tokens。真实模型生成动作，真实本地执行器写 work；辅助文本明确使用离线 stub，没有判题，不是比赛分数。

| 模型 | 实际动作 API 次数 | 输出 tokens（含推理） | 执行结果 | 证据 |
| --- | --- | --- | --- | --- |
| zai-org/GLM-5.3:peft:262144 | 1 | 29 | work 执行一次，生成 1 个版本 | `results/transport_v4_glm_verified_probe_20260917/summary.json` |
| openai/gpt-oss-20b | 1 | 45 | work 执行一次，生成 1 个版本 | `results/transport_v4_gptoss_verified_probe_20260917/summary.json` |

复查时这两个探针的 `identity.json` 中顶层 `src/*.py` 哈希与当前文件一致，`result.json` 中 `action_transport_log.executed` 均确认 work 已执行。每次探针使用新目录，先前探针也保留，不伪装为同一次运行。已运行的其他进程不会自动热加载这些修复；旧协议整场不能直接续跑为新协议成绩。

新模型正式跑整场前，应先运行相同的小探针；模板/协议离线通过不等于真实模型行为已验证。托管服务商不支持原始 token 续写时，只能在预算内重新生成完整调用，不能声称与 Tinker 的精确续写等价。有限上下文/输出预算仍可能耗尽，保证的是明确失败且不执行残缺调用，而不是消除服务端长度限制。
