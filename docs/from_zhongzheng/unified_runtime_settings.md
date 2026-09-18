# 统一运行设置

当前 native 和 artifact（PDF、文档、幻灯片）入口共用 `src/contest_budget.py`。

- 轮数：`min(90, max(10, ceil(比赛分钟数 / 5)))`；没有登记时长的比赛默认 90 轮。
- 显式 `--max-turns` 同样限制在 10–90：传 3 得到 10，传 100 得到 90。
- 每轮推进 5 分钟模拟时间。轮数是可用预算，不要求已经完成的比赛强行跑满 10 轮。
- 人数：single_agent 为 1；其他四种 baseline 固定使用各比赛 `competition.json` 的 `team.active_default`。
- 默认不设置总 API 次数或总 token 上限；可通过参数显式限制。每次输出默认 8192，ICPC/IIOT 的比赛默认上限为 4096。
- solver temperature 默认 0.2，可覆盖；artifact 的实际值写入运行身份。artifact judge temperature 明确保留 0.2 并记录。
- 旧规则卡中的 simulation 轮数不再决定运行入口的默认轮数。官方比赛时长与实验轮数是不同概念。

Pipeline 将以下参数同时传给实际子进程与运行身份预检，两条路线含义一致：

```powershell
python scripts/run_mini_dataset.py all `
  --provider tinker --model Qwen/Qwen3.6-35B-A3B `
  --system-variant otc `
  --max-turns 30 `
  --max-total-tokens 220000 `
  --max-output-tokens 8192 `
  --temperature 0.2 `
  --output results/mini_otc_new_settings
```

省略上述预算覆盖参数即可使用各比赛的新默认设置；`--max-api-calls` 也是可选参数。artifact 原来的 `--max-tokens` 保留为 `--max-total-tokens` 的别名。

设置变更后使用新的输出目录。历史输出保留原身份，不能作为新设置下的实验结果直接恢复或混用。

验证：157 项离线回归通过，包含轮数边界、artifact 运行／恢复、固定人数、公共规则注入、pipeline 参数传递、预算计费及 baseline 边界。日志为 `tmp/unified_settings_tests.log`。未运行付费实验。
