# mini 剩余五项修复与 Mystery Hunt 替换

本次五项已接通输入、提交和自动评分。mini 当前共 39 个赛道、109 条任务记录、89 个运行 session。五种 baseline 的 445 条命令通过离线预检查，0 evaluator blocker、0 外部主数据读取、0 付费模型调用。

| 项目 | 当前 mini 选择 | 评分方式与范围 |
|---|---|---|
| Mystery Hunt | **2012 — Initial Public Offering**，1 题，7 组、46 条文本线索 | 官方答案的确定性判分，1 分；不依赖图片、视频、现场互动或其他题答案 |
| CFA | 2016 Canadian Tire 研究任务 | 100 分 LLM 书面报告；公司 2014 年报与 2015 Q3 报告提供历史输入，明确借用 2025–2026 同赛事报告评分权重 |
| EOES | 2021 Task 1、Task 2，共 2 题 | 各 100 分 LLM 书面实验分析；a1/a2 空白答题纸分别并入 t1/t2，不重复计作独立任务 |
| Odyssey | 2019 第 5 题 Opposites Distract | 100 分 LLM 剧本与舞台设计；按公开 synopsis 要求评分，非会员完整题包或现场演出成绩 |
| Science Olympiad | 2017–2018 Solar System 历史 example exam，100 问 | 100 个一分项；支持明确答案别名、无序集合、有序序列和数值范围 |

## Mystery Hunt 的替换

按用户要求，mini 不再选择 2011 年的 20 条记录。改为 2012 年 `mystery_hunt_01610`，完整文本位于 `data/mini_data/raw/mystery_hunt/text_2012/initial_public_offering.txt`。原始分组、线索顺序、标点和索引保留。

[官方题面](https://puzzles.mit.edu/2012/puzzles/mayan_fair_lady/initial_public_offering/)与[官方解答](https://puzzles.mit.edu/2012/puzzles/mayan_fair_lady/initial_public_offering/solution/)已核对。解答不作为参赛者输入。主数据保留 2011 历史记录；mini 的旧选择记录在 `selection_manifest.json` 的 `superseded_selections` 中。只运行当前选中的一题，不代表整届 Hunt。

## 开放任务的评分边界

- CFA：输入包包含 2014 年报原 PDF 第 7–13、65–69 页，以及完整 58 页的 2015 Q3 报告。2015-12-31 是本 benchmark 的信息截止约定，非声称的原赛题截止日。没有给出的股价、同业数据和预测必须标成假设；允许给出条件化买卖价格阈值。原获奖报告不作为输入。[2014 年报](https://s201.q4cdn.com/326551073/files/doc_financials/en/2014/annual/2014-Annual-Report-EN.pdf)、[2015 Q3 报告](https://s201.q4cdn.com/326551073/files/doc_financials/en/2015/q3/Q3-2015-Shareholder-Report.pdf)。
- EOES：100 分分为科学推理 30、实验方法 25、已有数据分析 30、不确定性与证据完整性 15。这些是明示的 benchmark 权重。未提供的实测值必须写 `NOT MEASURED`，并提供方法、公式与误差分析；不得伪造实验读数、实际操作或签字。
- Odyssey：公开梗概转为完整书面剧本。情节与结局、两次成功干扰、不同戏剧风格、吸引注意的效果、幽默与整体连贯性各 20 分。这是公开梗概的可执行写作 rubric，不是未取得的官方完整题目分值；不计算现场表演、即兴环节和 350 分赛会归一化。
- Science Olympiad：材料本身标注 example exam，未改名冒充正式比赛。以历史答案表为准；未登记的任意同义改写可能不匹配。图像仍通过审核后的 contestant PDF 提供。

## 自动输出与验证

团队 baseline 继续自动要求 task score、max_score、accuracy、Communication、Planning、CS、耗时和用量。`CS = (Communication + Planning) / 2`。single_agent 只跳过协作指标，仍计算任务成绩。

- 五项 × 五种 baseline：25 个离线路由 smoke 全部 PASS，实际走提交、任务评分、团队协作评分及缓存复用流程；模型和 judge 使用 mock。
- Science Olympiad 判分回归：正确答案表 100/100、空白和错误表 0/100；检查集合顺序、重复项、序列顺序、单位转换和范围边界，并验证重新构建会保留 Mystery Hunt 与 EOES 的明确选择。相关测试 24 passed、24 subtests passed。
- 全 mini 预检查：445 prepared、0 failed；479 个资产校验通过，0 主数据读取。该结果不代表已完成真实付费实验或验证 LLM 评分质量。

完整 PowerShell 命令见 [mini_dataset_commands_20260916.md](mini_dataset_commands_20260916.md)。Mystery Hunt 命令仍使用 `--competitions mystery_hunt`，会自动选择更新后的 2012 文本题。
