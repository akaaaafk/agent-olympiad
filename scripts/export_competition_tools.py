"""Export the implemented, card-permitted competition preparation interface."""
from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from action_modules.competition_tools import PROFILES
from rules.loader import DEFAULT_RULES_ROOT, load_rule_card
from rules.storage import iter_rule_card_ids
from tool_registry import ACTION_REGISTRY, ACTION_SET_VERSION, render_function_tools, resolve_action_names


def export(destination=None):
    directory = Path(destination) if destination else ROOT / "docs" / "from_zhongzheng"
    directory.mkdir(parents=True, exist_ok=True)
    stem = "competition-specific-tools-20260913"
    cards = set(iter_rule_card_ids(DEFAULT_RULES_ROOT))
    if cards != {p.competition for p in PROFILES}:
        raise ValueError("Tool profiles must exactly cover the rule-card catalog")
    rows = []
    for profile in sorted(PROFILES, key=lambda p: p.competition):
        permitted = profile.name in load_rule_card(profile.competition).allowed_tools
        runtime_names = {runtime: profile.name in resolve_action_names(profile.competition, runtime=runtime)
                         for runtime in ("env", "session")}
        if not permitted or not all(runtime_names.values()):
            raise ValueError(f"Profile not callable: {profile.competition}")
        rows.append({**asdict(profile), "status": "implemented_preparation_tool",
                     "rule_card": f"data/rules/{profile.competition}/competition.json",
                     "permission": "explicit_card_allowlist", "runtimes": runtime_names,
                     "schema": render_function_tools([ACTION_REGISTRY[profile.name]])[0]})
    report = {"action_set_version": ACTION_SET_VERSION, "competition_count": len(rows),
              "new_tool_count": len(rows), "scope": "preparation_and_structure_checks",
              "live_contest_simulators_added": False, "competitions": rows}
    (directory / f"{stem}.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# 43 个比赛的专用 tools（2026-09-13）", "",
        "已为当前 43 个比赛各实现 1 个专用工具，共 43 个；它们归属 task_specific，使用同一个 ActionSpec 注册表，env 与 contest-session 都能执行。ACTION_SET_VERSION 从 8 升至 9，原有 30 个 action 的参数契约保留。", "",
        "后续 v10 更新：Guts 与 Science Bowl 已加入显式启用的状态动作，见 [两个状态试点](competition-flow-pilots-20260913.md)。本文及原验证记录描述的是 43 个准备工具这一层；普通静态任务不会自动启用新赛制。", "",
        "本次实现范围是赛题准备、输入检查、候选答卷/报告组装和结构检查。工具返回 format_ok、issues、warnings、candidate_text 和领域数据；不判断答案正确性，也不自动写入或提交候选。要保存候选仍调用 work，交卷仍走现有 submit/submit_code 与相应权限和 review gates。", "",
        "这些是本 benchmark 新增的辅助接口，不是对官方允许使用软件的主张。规则卡的 allowed_tools 显式加入对应名称；现有官方规则、计算器/联网权限以及来源文本未更改。实验比较需要使用新 action_set_version 和新输出目录。", "",
        "专用工具对五个 baseline 使用同样的比赛定义。它们不调用 LLM、网络、外部评判或文件读取，不接触 gold；返回结果只对调用者可见。一次调用计 1 个 action turn 和 1 个工具调用，沿用现有预算；memory-on/off 差异保持不变。", "",
        "以下每一行均为已实现工具。相近比赛共用底层检查实现，但比赛归属、字段、说明、年份选择和权限独立。", "",
        "| 比赛 | 专用工具 | 针对的特性及行为 | 参数 |",
        "| --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(f"| [{row['competition']}](../../{row['rule_card']}) | `{row['name']}` | {row['feature']} | {', '.join('`' + f + '`' for f in row['fields'])} |")
    lines += ["", "## 输入与结果示例", "",
        "Purple Comet 的 `prepare_purple_comet_answers(problem_ids=[\"q1\"], answers=[\"17\"])` 生成 `q1. 17`；`2+3`、负数、小数会被报告为格式不合格。题号必须来自当前公开 packet，部分答卷会列出尚未填写的题号。", "",
        "HMMT Guts 从当前任务的 season 选择 nov/feb。November 的 3 个答案可形成一组；同样的输入在 February 会报告需要 4 个答案。缺少 season 时明确报出缺失，不根据队伍大小推测。它不解锁下一组、不锁定已交卷答案，也不模拟现场成绩。", "",
        "Power 的 `dependencies=[\"\", \"a\"]` 表示第一部分无依赖、第二部分使用 a；引用不存在的部分、向后引用和依赖成环都会报告。检查图结构不等于验证数学证明。", "",
        "Mystery Hunt 的 `answers=[\"CAT\", \"DOG\"], indices=[2,2]` 提取 `AO`，按原字符串的一基字符位置处理，保留大小写、空格。它不确认 feeder 或 meta 答案正确。", "",
        "Wharton 的 60%+50% 配比报告超额配置；WSC 重复作者或重复题目会报告不符合三人分题结构；实验测量检查数组对齐、有限数值、单位与非负不确定度，保留选手输入来源。", "",
        "## 单队范围与尚需的任务环境", "",
        "所有比赛统一遵循[单队运行范围](single-team-scope.md)：对手生成、两队竞争和跨队联盟不在实现范围内，不作为待补功能或运行阻塞项。下方工具说明中的“不模拟对手”只说明边界。", "",
        "本队确实需要的任务环境仍按实现状态记录：Physics Brawl/Mystery Hunt 的放题状态，问答的本队回答资格与阶段，CTF 容器、CCDC 服务、WRO 机器人接口、辩论的本队角色与发言，以及 WSC 的独立写作阶段。Guts 放题和 Science Bowl 本队回答阶段已在显式启用的状态试点中实现，准备工具本身不承担这些状态变化。", "",
    ]
    for row in rows:
        if row["limitation"] != "Checks structure and supplied evidence only, not correctness.":
            lines.append(f"- **{row['competition']}**：{row['limitation']}")
    lines += ["", "## 代码与复现", "",
        "- 注册与逐比赛契约：`src/action_modules/competition_tools.py`。",
        "- 确定性执行：`src/competition_tool_runtime.py`；只接收白名单公开 selector 和选手输入。",
        "- env、session 与 adapter 均执行同一实现；规则卡、比赛归属、active task/lock 和分工仍参与 gating。",
        "- 生成清单：`python scripts/export_competition_tools.py`。",
        "- 专项检查：`python -m unittest discover -s tests -p test_competition_tools.py`。",
        "- JSON 清单包含每个工具完整 native function schema。", "",
        "验证结果见 [validation.json](competition-specific-tools-20260913-validation.json)，包括全量单元测试、43×5 离线 smoke、双运行入口与规则卡保留检查。", "",
    ]
    (directory / f"{stem}.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"competitions": len(rows), "tools": len(rows), "output": str(directory / f"{stem}.md")}))
    return report


if __name__ == "__main__":
    export()
