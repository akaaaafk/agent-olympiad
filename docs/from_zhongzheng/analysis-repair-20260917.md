# 分析配对修复与旧测试清理

`src/analyze_runs.py` 已修复不相同实验设置混合计算提升、混合求均值的问题。

- 比较 provider、model、temperature、轮数、总 API／token 上限、每次输出上限、协议、源码、评价配置和公共比赛规则。
- 优先读取保存的 `run_identity.settings`，不允许顶层显示字段覆盖真实运行预算；从公共规则注入区提取规则身份，不把不同 baseline 的规则卡哈希直接视为同一个控制变量。
- 若提供独立 `comparison_controls`，需完整记录上述控制变量。缺少配置的历史记录标记 `comparison_verified=false`，提升值为 null，原因包含 `unverified_settings`；缺少配置的记录也不会混合求均值。
- 不要求不同 baseline 的整个运行指纹相同。均值分组仍保留 baseline／condition、人数和已有运行指纹，避免把不同实验混为一组。
- 比较保持保守：身份里的执行／评价配置存在差异时会分开，即使用户认为某些差异可忽略，也不会自动合并。

原始错误案例现在不再产生 division_gain／cohesion_gain。修复后复现输出：`tmp/analysis_repair_repro.json`。

## 清理清单

从当前 `tests` 删除两组早期 collaboration runner 测试：

- `test_vanilla_team.py`
- `test_phase3_baselines.py`

这次只删除这两组旧入口的测试，并未删除生产兼容代码。当前五种 baseline 的边界测试、迁移拒绝、提交、评分及恢复测试保留；`test_phase4_judge.py` 等仍覆盖现用后端的测试也保留。

删除前备份及清单位于 `tmp/analysis_repair_backup_20260917_002252/`，不在活动测试目录内。

## 验证

修复相关 44 项测试通过，包含不同设置拒绝配对、缺配置拒绝聚合、真实身份优先、正常完整对照、baseline 边界和恢复身份。测试发现阶段可加载剩余 1057 项测试；本轮未重复执行全部测试。

日志：`tmp/analysis_repair_tests.log`。未修改历史实验输出，未调用付费模型。
