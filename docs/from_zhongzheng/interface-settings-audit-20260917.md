# 接口与设置复查

后续状态：下述四处问题已修复。模型规则按用户要求升级为正式运行必须显式传 `--model`；同时支持运行时 API key 参数。参数与示例见 [运行时供应商配置](explicit_provider_parameters.md)。下文保留修复前证据。

本轮仅检查与复现，未修改生产代码。范围为 CLI、原生／artifact 参数解析与预检、pipeline 转发、provider 适配、公共规则入口和预算。

## 已复现的问题

1. **负预算未在入口拒绝。** 原生 `_prepare_contest_run` 和 `prepare_artifact_run` 都接受 `max_api_calls=-1`、总 token 上限为 -1。无效预算进入运行配置，可能导致一开始就耗尽，而不是给出明确参数错误。应统一规定可选预算的合法范围并在预检与执行共用的解析层校验。

2. **温度预检与正式入口不一致。** 原生 `_prepare_contest_run` 接受 `--temperature -1`，但 `main` 会拒绝。pipeline 调用的 identity 预检与实际子进程因此可能得到不同结论。NaN 在两条路线最终都会被身份 JSON 序列化拒绝，但错误来自较晚的序列化层，而非温度校验。

3. **公共规则路径仍受旧 OTC 开关限制。** 原生 single_agent／centralized／decentralized 的 rules_mode 必须 off；同时代码禁止 off 配合 `--rules-root`，即使指定的就是现有 `data/rules`。现在人数和公共规则都读取 competition.json，这项旧限制阻碍普通 baseline 使用显式规则目录。artifact 入口没有这项限制。默认目录和 mini wrapper 的数据根目录方式仍可用。

4. **直接入口的默认 OpenAI 模型不同。** 设置临时 `OPENAI_MODEL=fixture-model-from-env`，原生 `_resolve_model` 返回该模型，artifact `prepare_artifact_run` 仍返回 `gpt-4.1`。这影响直接省略 `--model` 的 artifact 调用；统一 pipeline 已先解析并显式转发 model，因此该路径不受此复现影响。

建议将合法性校验、模型默认值和公共规则路径解析集中到共享解析层，保留普通 baseline 不启用 OTC 协作卡的边界。

## 证据与验证

- 数值与规则目录复现：`tmp/interface_audit_repro.json`。
- 默认模型复现：`tmp/interface_audit_model_repro.json`。使用临时假模型环境变量，没有读取或展示凭据。
- 14 个相关测试模块，122 项全部通过，覆盖 provider、调用协议、接口污染、pipeline、规则注入和 artifact 流程。上述边界案例不在现有测试覆盖内。
- 日志：`tmp/interface_audit_tests.log`。
- 未调用付费模型，未修改实验输出或数据。
