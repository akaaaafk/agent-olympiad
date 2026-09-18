# Tinker 图片输入接入

当前配置 `Qwen/Qwen3.6-35B-A3B` 自动启用图片输入。Qwen3.5 / Qwen3.6 家族使用官方 `qwen3_5_disable_thinking` renderer，保持现有关闭 thinking 的行为。其他尚未配置视觉 renderer 的模型保留原文字通路，图片明确拒绝，不能静默丢弃。

实现参照 [Tinker 官方 rendering 文档](https://tinker-docs.thinkingmachines.ai/tutorials/core-concepts/rendering/)。新增并安装 `tinker-cookbook==0.5.7`；SDK 保持 `tinker==0.29.0`。依赖解析同步调整 transformers/tokenizers 到 cookbook 支持版本；`pip check` 通过。

## 交付流程

- `read_problem_pdf` 的页面图片经过 `LLMRequest` 传入官方 renderer，再作为真实 SDK `ImageChunk` 进入采样请求。
- 直接 PDF 附件仅渲染已指定页码，保留页序；图像、PDF 不再先转为纯文字。透明图像使用白底，动画文件要求显式选帧。
- 动作选择、元数据、正文生成、续写和重试均携带同一组图片。动作权限、预算和完整调用验证沿用原流程。
- 上下文计算包含图片 token、assistant prefix 和续写 token；超出预算明确失败，不截断题目。
- 判题侧资源隔离保持；文档流程和评分请求也按具体模型选择图片或文字路径。

## 验证范围

`scripts/check_tinker_vision_offline.py --output <新报告路径>` 使用真实 tokenizer、官方图片处理器、renderer 和 SDK 序列化，替换远端采样，不使用真实凭证。

本次输出 `tmp/tinker_vision_offline_20260917.json`：Conquering the World、Box Sets、The Arena、Thirteen at Dinner 四题共 12 页，7 组请求均含真实图片 chunk，图片 token 计数一致。

`tests/test_tinker_vision.py` 覆盖页码/顺序/角色隔离、多阶段及续写图片保留、真实 SDK 请求结构、图片上下文预算、纯文字模型拒绝图片，以及实际文档渲染评分循环。既有 Tinker、动作运输、PDF 和运行流程回归同时验证。

未进行付费远端推理。因此本次确认的是本地完整请求构建及传递，不宣称服务端已返回图像理解结果或模型独立解出了上述题目。未修改历史实验结果或 last_exam。
