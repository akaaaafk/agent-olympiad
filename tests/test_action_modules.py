"""Independent ownership/execution kinds; legacy argument schemas stay stable."""
import dataclasses
import hashlib
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from action_modules import MODULE_SPECS
from action_modules.competition_flow import ACTION_NAMES as FLOW_ACTIONS
from action_modules.competition_tools import ACTION_NAMES as PREPARATION_ACTIONS
from tool_registry import (ACTION_REGISTRY, MODULE_ACTION_NAMES, TOOL_ACTION_NAMES,
                           render_function_tools, validate_registry, actions_for_runtime)


class ActionModuleTests(unittest.TestCase):
    def test_exact_partition(self):
        self.assertEqual({k: len(v) for k, v in MODULE_ACTION_NAMES.items()},
                         {'common': 25, 'memory': 3, 'coach': 0, 'task_specific': 51})
        seen = set()
        for name, specs in MODULE_SPECS.items():
            for spec in specs:
                self.assertEqual(spec.module, name)
                self.assertNotIn(spec.name, seen)
                seen.add(spec.name)
                self.assertIs(ACTION_REGISTRY[spec.name], spec)
        self.assertEqual(seen, set(ACTION_REGISTRY))
        self.assertEqual(validate_registry(), ())

    def test_tools_are_a_view_of_actions(self):
        self.assertEqual(TOOL_ACTION_NAMES,
                         frozenset(n for n, s in ACTION_REGISTRY.items() if s.is_tool))
        self.assertEqual(MODULE_ACTION_NAMES['memory'], {'remember', 'recall', 'share_note'})
        self.assertIn('propose', MODULE_ACTION_NAMES['common'])
        self.assertNotIn('query_rules', MODULE_ACTION_NAMES['memory'])
        self.assertEqual(actions_for_runtime('env'), actions_for_runtime('session') - FLOW_ACTIONS - {'read_problem_pdf'})

    def test_original_contract_is_preserved_except_documented_v11_changes(self):
        specs = []
        original = {n: s for n, s in ACTION_REGISTRY.items() if n not in {'render_pdf', 'read_problem_pdf'} and n not in PREPARATION_ACTIONS and n not in FLOW_ACTIONS}
        # Preserve the historical contract hashes instead of blessing an
        # arbitrary new hash. Assert each intentional change before normalising:
        # v10 recall; v11 zero-turn memory, activation and answer-format help.
        activation = json.loads((Path(__file__).parent / "fixtures" /
            "contest_engine_replay_memory_activation_v11.json").read_text(encoding="utf-8"))
        historical_descriptions = {
            "remember": "Store a private note that survives outside the visible transcript, "
                        "optionally tagged to one problem. Use work for candidate answers, "
                        "remember for intermediate results, dead ends, and reminders.",
            "recall": "Search your own notes and notes teammates have shared, ranked by "
                      "problem tag, query match, and recency.",
            "share_note": "Publish one of your stored notes to the whole team.",
        }
        for name in MODULE_ACTION_NAMES['memory']:
            spec = original[name]
            self.assertEqual(spec.budget.turns, 0)
            if name == "recall":
                self.assertEqual(spec.description,
                    "Zero-turn auxiliary: search your own notes and team-shared notes when "
                    "needed prior information is missing from context. "
                    "Nonempty query requires a whole-keyword match; omit query only to browse. "
                    "An explicit problem_id restricts results to that task; omit it for "
                    "cross-task methods. Results rank by keyword hits and recency.")
            else:
                self.assertEqual(spec.description, activation["memory_descriptions"][name])
            original[name] = dataclasses.replace(
                spec, budget=dataclasses.replace(spec.budget, turns=1),
                description=historical_descriptions[name])
        work_description = (
            "Record durable work for the team: a candidate answer or draft for "
            "one problem. Pass problem_id to record against a specific problem "
            "(and make it your current one); without it the work goes to your "
            "current problem."
        )
        self.assertEqual(original['work'].description, work_description + (
            " For short-answer tasks, keep reasoning above a "
            "separate final line: Final answer: <value>. Never substitute a "
            "different problem's answer for this problem. For non-programming "
            "cross-task work, start content with 'Problem <target id>:' or include "
            "a matching problem_id in JSON content; otherwise select_problem "
            "first and read that task before writing."
        ))
        original['work'] = dataclasses.replace(
            original['work'], description=work_description)
        recall = original['recall']
        self.assertEqual(next(arg.description for arg in recall.arguments if arg.name == 'problem_id'),
            'Optional exact problem id to filter; omit to search across tasks.')
        original['recall'] = dataclasses.replace(
            recall, description='Search your own notes and notes teammates have shared, ranked by '
                                'problem tag, query match, and recency.',
            arguments=tuple(dataclasses.replace(arg, description=(
                'Optional keywords to match.' if arg.name == 'query' else 'Optional problem tag to prioritise.'))
                for arg in recall.arguments))
        # The old note_id help advertised comma-separated ids, but the action
        # accepts exactly one. Check the correction without replacing hashes.
        share = original['share_note']
        self.assertEqual(share.arguments[0].description,
                         'Id of one of your private notes returned by remember or recall.')
        original['share_note'] = dataclasses.replace(share, arguments=(
            dataclasses.replace(share.arguments[0], description=(
                'Id of the note returned by remember or recall '
                '(several ids may be comma-separated).')),))
        for _, spec in sorted(original.items()):
            value = dataclasses.asdict(spec)
            value.pop('module')
            value.pop('is_tool')
            specs.append(value)
        encoded = json.dumps(specs, sort_keys=True,
                             default=lambda x: sorted(x) if isinstance(x, (set, frozenset)) else dict(x))
        self.assertEqual(hashlib.sha256(encoded.encode()).hexdigest(),
                         '6183aea6cb630dc5682132bfa58ea67ba5fc4a4bdde11d2ab708c21e326adf90')
        tools = json.dumps(render_function_tools(original.values()), sort_keys=True)
        self.assertEqual(hashlib.sha256(tools.encode()).hexdigest(),
                         '8a836229249fd171ce360e0eeda9f922dd5b629893d694c226537eecb1937c64')


if __name__ == '__main__':
    unittest.main()
