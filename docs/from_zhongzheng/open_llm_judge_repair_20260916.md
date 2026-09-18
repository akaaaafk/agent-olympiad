# 开放任务与代码审阅：自动 LLM 评分接入

更新：下文保留当时的六项修复记录。其余五项现已接通，Mystery Hunt 改为 2012 纯文本题；最新状态见[剩余五项修复](remaining_five_mini_repair_20260917.md)。

本轮已接入主数据中对应的选中记录及独立 mini_data，共 6 个赛道、17 条记录。其他年份没有因此自动变为可运行。任务分、分项证据和理由自动保存；团队继续必算 Communication、Planning、CS，single_agent 只跳过协作评分。

| 赛道 | mini 记录 | 当前交付与评分 | 分值来源 |
|---|---:|---|---|
| IIOT 2021 | 8 | 完整 C++ 源码及说明；逐 subtask 审阅正确性、边界和复杂度 | 每题 100；沿用题面 subtask 权重，部分分锚点为 benchmark 代码审阅尺度 |
| CCDC 2025 | 1 | 基于原始网络题包的书面防御、业务响应和事件报告方案 | 2 × 50；benchmark 权重，不能读作 uptime 或实测 inject 分 |
| DebateBench 2022 | 5 | 一个 Opening Government 队伍的 PM、DPM 两份新生成书面发言 | 每份 100，总分 200；使用已有 WUDC 说服力尺度，空缺发言按 benchmark 记零；不生成对手、不算房间名次 |
| GCCH Harvard 2021 | 1 | 案例方案 slide deck，经真实渲染后评分 | 5 × 20；将原始 2021 case 的建议分析主题转成 benchmark 维度与等权尺度 |
| IOAI 2025 | 1 | 仓储机器人控制代码及说明；审阅导航、定位、操作和整合 | 4 × 25；从原任务要求整理的 benchmark 审阅标准，不是 simulator/referee 分 |
| Wharton 2021 | 1 | 原始客户案例对应的投资政策与策略报告 | 4 × 25；复用同竞赛公开的定性考虑项，等权尺度为 benchmark 选择，未声称历史官方等价 |

## 自动输出

- 参赛生成结果保存在各 session 的 `contest_session.json`；GCCH 另有渲染后的提交 PDF。
- 任务 judge 保存 `criteria`、分项 `score/max_score`、`evidence`、`justification`、`confidence` 和限制说明。
- `required_metrics.json`、`required_metrics.csv` 保存必算指标。团队 CS = (Communication + Planning) / 2。
- 没有提交时任务得零分，不调用任务 judge；评分失败保持待评状态，续跑补评，不能把缺分当零分。
- LLM 作品评分明确记录 `official_score_equivalent=false`。IIOT 另有 `source_review_llm_v1`、`execution_verified=false`，没有伪造的官方测试通过率。
- 代码参考只在 judge 阶段读取，检查角色和文件哈希并绑定运行身份。开放作品启用 `rubric_only` 时不再隐式加载历史获奖作品。

## PowerShell

完整逐赛道 decentralized / centralized 命令： [mini_dataset_commands_20260916.md](mini_dataset_commands_20260916.md)。六个新增评分赛道使用同一个 mini 入口；例如先跑 IIOT：

```powershell
Set-Location E:\agent_olympiad\agent-olympiad
$py = "E:\agent_olympiad\.venv\Scripts\python.exe"
$runTag = Get-Date -Format "yyyyMMdd_HHmmss"
& $py -u scripts\run_mini_dataset.py all `
  --competitions iiot `
  --system-variant decentralized `
  --provider tinker `
  --model "Qwen/Qwen3.6-35B-A3B" `
  --judge-provider tinker `
  --judge-model "Qwen/Qwen3.6-35B-A3B" `
  --output "results\mini_iiot_decentralized_$runTag"
```

将 `iiot` 换为 `ccdc`、`debatebench`、`gcch_harvard`、`ioai_team`、`wharton_investment` 即对应其他赛道。centralized 改 baseline 和输出名，按顺序运行。该命令会调用模型产生费用；本轮修复没有启动付费运行。

## 验证范围

- 70 项相关单元与集成测试通过，涵盖评分输出、私有参考、空提交、错误评分格式、结果绑定、续跑、协作指标和 artifact pipeline。
- 六个赛道各取一个 session，五种 baseline 共 30 次真实流程 smoke 通过；使用确定性 mock agent/judge，不是模型质量实验。GCCH 使用真实 PDF 渲染。
- IIOT 全 8 题与 DebateBench 全 5 条记录另有 rubric/评分接入检查；全 mini 的五 baseline 预检由 `verification.json` 记录。
- CCDC 20 页题包已核对、登记可读页码；第 14 页网络图有人工核对的文字转录，保留图与正文中的原始差异。
- 主数据、base、last_exam 的相关赛道已同步；原始材料和历史实验结果保留。独立 mini 的测试输入、rubric 和依赖绑定已更新。

## 仍需后续处理的五个赛道

这些没有被直接标成已修完：

| 赛道 | 当前具体问题 |
|---|---|
| CFA 2016 | 已有报告 rubric，但原记录仅有获奖作品和公司名称；原始研究输入及历史信息边界未补齐。获奖报告不能转成参赛输入。 |
| EOES 2021 | 4 条记录包含题册与答案表，需对齐同场附件；多项分值对应现场测量，不能捏造观测数据。可以评方法与推理，但还需明确逐项可观察评分范围。 |
| Mystery Hunt 2011 | 属于标准答案谜题；仍需接通答案判分、校准共享题目的多个答案目标，并处理媒体输入。Pattern Recognition 的 18 个视频链接尚未验证。 |
| Odyssey 2019 | 当前是公开 synopsis，缺完整问题专属要求与评分细则；总分计算公式不能替代这些缺失条件。 |
| Science Olympiad 2018 | 属于带 100 条参考答案的样例考试，需要按参考处理集合、顺序、范围和答案变体，并完成图像交付验证；不把它改成自由作品评分。 |

本轮没有把上述五项宣称为可完整运行，也没有将作品审阅成绩冒充实测或官方比赛成绩。
