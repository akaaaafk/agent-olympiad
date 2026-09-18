# v12 代码复审

当前执行协议的唯一常量为 `src/contest_config.py::PROTOCOL_VERSION = contest_session_v12`。
本次复审以当前代码和测试为依据，不重新运行历史付费比赛。

## 新发现与修复

1. 多行动响应的纠正重试未检查剩余输出预算。现输出预算耗尽时不再调用模型，
   有余额时重试上限不超过余额，所有被拒绝的行动仍保持未执行状态。
2. Perplexity caller 未消费 `max_output_tokens_override`。现将实际重试上限传入
   API，并在 usage 中记录该上限；避免只在调度层计算限制、请求端却忽略。
3. 完整聊天导出模块和脚本缺失。新增 `src/contest_transcript.py` 与
   `scripts/export_otc_chat.py`，主比赛和 artifact 路径均生成 `chat.json` / `chat.md`。
   OTC 两种预设另外生成兼容名称 `otc_chat.json` / `otc_chat.md`。
   导出保存完整本地事件，包括私有记录和缺失轮次标记；它不是参赛 agent 的观察输入。
   测试验证导出不会改写 `contest_session.json`，在线保存与离线导出内容一致。
4. OpenAgents key 未加入已有错误日志脱敏名单。现已加入并通过回归测试。
5. 代表性 smoke 的说明硬编码 v10。现直接读取唯一协议常量。
6. 代表性 artifact schema 测试还给普通 baseline 附带规则卡。修正 fixture，
   保留五 baseline 工具名唯一性与 render_pdf 可用性断言。

## 版本边界

- 五 baseline、原生比赛、artifact 执行与 run identity 共用 v12 配置定义。
- 生产原生入口的 submission_turn、直接提交门控、预算定义保持上轮修复的 v12 合约。
- 20 个数学/编程、新跑/恢复场景继续验证原有 v12 完整回放快照。
- `contest_session_v1` 在 `contest_adapters.py` 中是评分方法 ID，不是执行协议。
  action set、memory module 和 evaluator 有自己的版本号，不统一替换为 12。
- 历史结果与旧快照保留；不把历史运行改标签冒充当前 v12。

## 验证与范围

复审前的 482 项运行时测试通过，随后扩大到代表性 smoke、聊天导出、Tinker、
阶段控制、OTC 合约和规则测试，并加入新增预算与脱敏回归。
最终结果见 `tmp/v12_reaudit_final_20260914.json` / `.log`。
最终执行 **535 项运行时测试，0 failures、0 errors、0 skipped**，耗时约 102 秒。
最后调整导出事件分类以复用 canonical registry 后，6 项聊天导出测试再次通过。

```powershell
E:\agent_olympiad\.venv\Scripts\python.exe .codex_tmp\audit_runtime_settings_20260914.py --output-stem tmp/v12_reaudit_next
```

这是一组明确列出的运行时审计，不等同于所有数据修复脚本、所有比赛真实模型评测或
远程评测平台的端到端验证。没有切换仓库，也没有改写历史实验。
