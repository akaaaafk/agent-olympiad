# 工具命令误存为答案：修复与验证

## 已确认的故障

历史运行：`results/tinker_qwen_15easy_full_20260918_011924/single_agent/arml_national_power/runs/arml_national_power_216cf82255552940`。

ARML National Power 2023 的最终正文是：

```text
read_problem_pdf(problem_id="deliverable", pages=[1, 2], document=2)
```

日志显示模型先选择 `work` 或 `render_pdf`，再把阅读命令输出到 `content` 字段。之前的类型、长度和 PDF 渲染校验都接受了这个非空短字符串，因而生成了 PDF；评分器给出 0/50。不是评分器把正常解答误判成命令。

只读复核历史文件：

- source SHA256：`390d7451c590c43620d53385d0d44ccae8771d243ca874c71d255ae285a0617d`
- PDF SHA256：`384c6c195110269566fd325e72e766c72484846b02a125f92fa81edf37adaa8d`
- 原始结果和分数未修改；原样正文现在会被拦截。

## 修改

1. 新增 `src/answer_content.py`：从 canonical action registry 识别整段工具调用、调用批次及 JSON 工具调用封装；只解析，不执行正文。
2. `work.content`、`render_pdf.content`、`submit.answer` 在公共 transport、动作保存入口检查；artifact renderer 也在创建文件前独立检查。
3. 原生调用和 Tinker 都在原有 API/token 预算内重新选择动作。命令不送入“缩短答案”的重写流程，不从正文推断并执行工具，不凭空补出答案。预算耗尽则保留明确失败。
4. Tinker 重新选择阅读动作后，可保存并恢复其未完成的 metadata；拒绝的正文不会作为答案或已执行工具结果恢复。
5. PDF 提示改为说明如何通过动作接口阅读，去掉可直接被抄成正文的伪调用示例。
6. 普通正文中的引用、数学函数以及 source/programming 任务不按“工具命令型答案”拒绝。模型正确率、答案完整性仍由原有评估判定，不引入 gold 驱动筛选。

版本：`work_content=3`、`action_transport=3`、Tinker `staged_raw_arguments_v7_answer_command_guard`。源码和版本均进入已有 identity/checkpoint 检查；修复后的真实验证应使用新输出目录，不把旧实验混成新版本。

修改前快照：`tmp/answer_command_guard_before_20260918_0932`。

## 验证

遵循 diagnosing-bugs 流程，先用日志中的原样字符串复现，再修改代码：

```powershell
E:\agent_olympiad\.venv\Scripts\python.exe -m pytest tests/test_answer_command_guard.py -q
```

- 修复前：3 failed（Tinker 将命令返回为合法 work；work/render_pdf 均接受并保存）。
- 修复后：50 passed。覆盖五种 baseline 的原子拒绝、原生/Tinker 恢复与预算、不可用工具拒绝、checkpoint、代码题豁免和正常引用。
- 完整 artifact 离线用例走真实 engine、PDF reader、renderer、提交和评分解析；模型/评分回答使用固定 fixture。断言错误命令未保存，实际 reader 执行并返回页面，唯一答案版本/PDF 包含 fixture 解答。
- 测试构造过程中修正过 fixture：ArtifactContract 必须指定 kind，比赛实际轮数/终局动作由规则约束，fixture 遵循规则等待 submit，不修改生产预算或权限。
- 全量回归：`python -m pytest tests -q`，**1756 passed, 1345 subtests passed in 276.78s**，退出码 0。

本次没有真实模型 API 调用、付费探针或重跑比赛。检测是保守的 command-only 格式校验，不承诺识别所有语义无效正文，也不保证模型在有限预算内一定恢复或解题正确。历史的 0/50 仍是历史结果；已经启动的进程不会自动热加载本修复。
