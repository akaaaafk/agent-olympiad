# 运行时指定供应商、模型与 API key

正式运行必须显式传 `--model`。不再使用内置默认模型，也不从 `OPENAI_MODEL`、`TINKER_MODEL` 等环境变量自动选择模型。省略 `--judge-model` 时，裁判使用本次显式指定的 solver 模型；同一次运行的 solver 和裁判仍使用同一供应商。

```powershell
Set-Location E:\agent_olympiad\agent-olympiad
$Provider = "tinker"
$Model = "YOUR_MODEL_NAME"
$env:RUN_API_KEY = "YOUR_API_KEY"

python scripts/run_mini_dataset.py all `
  --provider $Provider `
  --model $Model `
  --api-key-env RUN_API_KEY `
  --system-variant otc `
  --output results/mini_explicit_provider
```

也支持直接参数 `--api-key $Key`；它与 `--api-key-env` 二选一。未传这两个参数时，仍可以使用该供应商原来的专用环境变量／`.env` key。显式 key 优先，且不会写回 `.env`。

| provider | SDK 读取的 key 环境变量 |
|---|---|
| perplexity | PERPLEXITY_API_KEY |
| openai | OPENAI_API_KEY |
| openagents | OPENAGENTS_API_KEY |
| tinker | TINKER_API_KEY |
| vectorengine | VECTORENGINE_API_KEY |

供应商可用范围仍取决于原入口的能力；本次不新增 artifact provider。API key 通过子进程环境传递，不加入 pipeline 保存的子命令或运行身份。模型名会记录到运行身份，便于结果比较。

同样的参数可用于 `src/run_competition_batch.py --live` 和 `src/run_otc_artifact.py`。pipeline 的 register／report 阶段不调用模型，因此不要求 `--model`。

其他接口修复：显式 API／token 预算必须为正数；温度必须是有限的非负数；原生预检与执行使用共同校验。普通 baseline 可使用 `--rules-root` 指定公共比赛规则目录，仍不附带 OTC 协作卡。`--rules-strict` 仍要求启用规则卡模式。

验证：第一轮相关 121 项通过；全量 1064 项仅出现 7 处旧测试命令缺少模型的报错，已补上显式测试模型。最后针对这些测试与 pipeline 顶层参数校验复跑 41 项，全部通过。日志分别为 `tmp/interface_fix_tests.log`、`tmp/interface_fix_full.log`、`tmp/interface_fix_final.log`。本次未调用付费模型。
