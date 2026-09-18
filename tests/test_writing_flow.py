"""Writing stage/privacy, submission and strict memory-ablation regressions."""
from dataclasses import replace
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from competition_flow import bind_competition_flow
from contest_actions import _apply_action
from contest_config import ContestRunConfig
from contest_engine import _ContestEngine
from contest_manifest import ContestManifest, ManifestTask
from contest_memory import ContestMemory
from contest_policy import _actions_for_agent, _resolved_actions
from contest_session import ContestSession, ContestBudgetState, TaskUnit
from rules.loader import load_rule_card
from strategy import StrategicPolicy


class WritingTests(unittest.TestCase):
    def setup_flow(self, variant='decentralized', deadline=True):
        self.manifest = ContestManifest('writing_test', 'wsc_writing', tuple(
            ManifestTask(f'q{i}', f'q{i}', None, f'Prompt {i}', 'collaborative_writing_discussion',
                         100, False, {}) for i in range(3)), {'competition_flow': 'collaborative_writing_v1'})
        self.config = ContestRunConfig(variant, 1 if variant == 'single_agent' else 3, 20, deadline_submit=deadline,
            rule_card=load_rule_card('wsc_writing') if variant in {'otc', 'vallina_otc'} else None)
        self.session = ContestSession([TaskUnit(t.task_id, kind='non_programming') for t in self.manifest.tasks],
                                      ContestBudgetState(max_turns=20))
        self.memory = ContestMemory(run_id='test', session_id='writing_test', competition_id='wsc_writing')
        self.flow = bind_competition_flow(self.manifest, self.session, self.config)
        self.session.select_task('q0')

    def apply(self, action, args=None, agent='Agent_1'):
        return _apply_action(action=action, arguments=args or {}, agent=agent, manifest=self.manifest,
            session=self.session, memory=self.memory, config=self.config, strategic_policy=StrategicPolicy(),
            task_action_executor=Mock(side_effect=AssertionError('no external tool')))

    def write_three(self):
        self.apply('start_independent_writing')
        for i in range(3):
            self.apply('write_writing_response', {'problem_id': f'q{i}', 'content': f'SECRET_DRAFT_{i}'}, f'Agent_{i+1}')

    def test_stages_private_content_and_three_submissions(self):
        self.setup_flow()
        self.write_three()
        self.assertFalse(any(t.versions for t in self.session.tasks))
        self.assertNotIn('SECRET_DRAFT_0', json.dumps(self.flow.public_state()))
        self.assertNotIn('SECRET_DRAFT_0', str(self.memory.view('Agent_2')))
        self.assertIn('SECRET_DRAFT_0', str(self.memory.view('Agent_1')))
        self.assertIn('SECRET_DRAFT_1', str(self.memory.view('Agent_2', task_id='q1')))
        for forbidden in ['speak', 'share_note', 'work', 'submit']:
            with self.assertRaises(ValueError):
                self.apply(forbidden, {'content': 'leak'})
        with self.assertRaises(ValueError):
            self.session.create_answer('bypass', author='Agent_1')
        self.apply('start_peer_review')
        for i in range(3):
            editor = f'Agent_{(i+1)%3+1}'
            self.apply('read_writing_response', {'problem_id': f'q{i}'}, editor)
            self.apply('review_writing_response', {'problem_id': f'q{i}', 'content': f'EDITED_{i}'}, editor)
        self.apply('submit_writing_packet')
        self.assertEqual(self.flow.state['phase'], 'complete')
        self.assertEqual([t.versions[-1].content for t in self.session.tasks], ['EDITED_0', 'EDITED_1', 'EDITED_2'])
        self.assertEqual([len(t.submissions) for t in self.session.tasks], [1, 1, 1])

    def test_wrong_author_and_early_transitions_are_atomic(self):
        self.setup_flow()
        self.apply('start_independent_writing')
        before = self.flow.checkpoint()
        for action, args, agent in [('write_writing_response', {'problem_id': 'q0', 'content': 'bad'}, 'Agent_2'),
                                    ('start_peer_review', {}, 'Agent_1'), ('submit_writing_packet', {}, 'Agent_1')]:
            with self.assertRaises(ValueError):
                self.apply(action, args, agent)
            self.assertEqual(self.flow.checkpoint(), before)

    def test_solo_writes_edits_and_submits_all_three_without_other_seats(self):
        self.setup_flow('single_agent')
        self.assertEqual(set(self.flow.public_state()['authors'].values()), {'Agent_1'})
        self.assertEqual(set(self.flow.public_state()['peer_editors'].values()), {'Agent_1'})
        self.assertEqual(self.flow.public_state()['review_mode'], 'self_edit')
        self.apply('start_independent_writing')
        with self.assertRaises(ValueError):
            self.apply('write_writing_response', {'problem_id': 'q0', 'content': 'invalid'}, 'Agent_2')
        for i in range(3):
            self.apply('write_writing_response', {'problem_id': f'q{i}', 'content': f'DRAFT_{i}'})
        restored = ContestSession.from_checkpoint(self.session.checkpoint())
        rebound = bind_competition_flow(self.manifest, restored, self.config)
        self.assertEqual(rebound.checkpoint(), self.flow.checkpoint())
        self.apply('start_peer_review')
        with self.assertRaises(ValueError):
            self.apply('submit_writing_packet')
        for i in range(3):
            self.apply('review_writing_response', {'problem_id': f'q{i}', 'content': f'EDITED_{i}'})
        self.apply('submit_writing_packet')
        self.assertEqual([t.versions[-1].author for t in self.session.tasks], ['Agent_1'] * 3)
        self.assertEqual([t.versions[-1].content for t in self.session.tasks], ['EDITED_0', 'EDITED_1', 'EDITED_2'])
        self.assertEqual([len(t.submissions) for t in self.session.tasks], [1, 1, 1])

    def test_team_writing_still_requires_three_seats(self):
        self.setup_flow()
        config = replace(self.config, team_size=2)
        with self.assertRaisesRegex(ValueError, 'three'):
            bind_competition_flow(self.manifest, self.session, config)

    def test_deadline_collects_latest_available_draft_once(self):
        self.setup_flow()
        self.apply('start_independent_writing')
        self.apply('write_writing_response', {'problem_id': 'q0', 'content': 'old'})
        self.apply('write_writing_response', {'problem_id': 'q0', 'content': 'latest'})
        self.flow.close()
        self.flow.close()
        self.assertEqual(self.session.task('q0').versions[-1].content, 'latest')
        self.assertEqual([len(t.submissions) for t in self.session.tasks], [1, 0, 0])
        self.setup_flow(deadline=False)
        self.write_three()
        self.flow.close()
        self.assertFalse(any(t.submissions for t in self.session.tasks))

    def test_memory_off_cannot_read_previous_round_draft(self):
        self.setup_flow('vallina_otc')
        self.write_three()
        self.session.budget.turns_used += 1
        with self.assertRaises(ValueError):
            self.apply('read_writing_response', {'problem_id': 'q0'})
        self.apply('start_peer_review')
        self.apply('read_writing_response', {'problem_id': 'q0'}, 'Agent_2')
        self.session.budget.turns_used += 1
        with self.assertRaises(ValueError):
            self.apply('read_writing_response', {'problem_id': 'q0'}, 'Agent_2')

    def test_checkpoint_and_canonical_action_surface(self):
        for variant in ['decentralized', 'centralized', 'otc', 'vallina_otc']:
            self.setup_flow(variant)
            offered = {s.name for s in _actions_for_agent(_resolved_actions(self.manifest, self.config),
                       self.session, self.config, 'Agent_1', memory=self.memory)}
            self.assertIn('start_independent_writing', offered)
            self.assertNotIn('work', offered)
            self.write_three()
            restored = ContestSession.from_checkpoint(self.session.checkpoint())
            rebound = bind_competition_flow(self.manifest, restored, self.config)
            self.assertEqual(rebound.checkpoint(), self.flow.checkpoint())
            self.assertFalse(any(t.versions for t in restored.tasks))

    def test_real_engine_collects_three_distinct_responses(self):
        self.setup_flow()
        sequence = [('start_independent_writing', {}),
                    ('write_writing_response', {'problem_id': 'q1', 'content': 'SECRET_1'}),
                    ('write_writing_response', {'problem_id': 'q2', 'content': 'SECRET_2'}),
                    ('write_writing_response', {'problem_id': 'q0', 'content': 'SECRET_0'}),
                    ('rest', {}), ('rest', {}), ('start_peer_review', {}),
                    ('review_writing_response', {'problem_id': 'q0', 'content': 'EDIT_0'}),
                    ('review_writing_response', {'problem_id': 'q1', 'content': 'EDIT_1'}),
                    ('review_writing_response', {'problem_id': 'q2', 'content': 'EDIT_2'}),
                    ('rest', {}), ('rest', {}), ('submit_writing_packet', {})]
        query = Mock(side_effect=[json.dumps(dict(action=a, arguments=b)) for a, b in sequence])
        result = _ContestEngine(self.manifest, query, self.config).run()
        self.assertEqual(query.call_count, len(sequence))
        self.assertEqual(result['submissions'], {'q0': 'EDIT_0', 'q1': 'EDIT_1', 'q2': 'EDIT_2'})
        self.assertEqual(result['competition_flow']['phase'], 'complete')
        # Agent_2's prompt during writing must not contain Agent_3's draft.
        self.assertNotIn('SECRET_2', str(query.call_args_list[4]))

    def test_canonical_wsc_and_pumac_judges_use_verified_maxima(self):
        from contest_task_judge import judge_task
        from llm import LLMResponse
        root = Path(__file__).resolve().parents[1]
        calls = []
        def judge(request):
            schema = json.loads(request.user_prompt.split('STRUCTURED RUBRIC:\n\n')[1].split('\n\n')[0])
            calls.append(schema)
            return LLMResponse(json.dumps(dict(criteria=[dict(id=c['id'], score=c['max_score'],
                max_score=c['max_score'], evidence=['fixture'], justification='fixture', confidence=1,
                observable=c['observable']) for c in schema['criteria']],
                total_score=schema['total_points'], max_score=schema['total_points'])), 'mock', 'mock')
        rows = json.loads((root/'data/benchmarks/wsc_writing/benchmark.json').read_text(encoding='utf8'))[:3]
        rows += [r for r in json.loads((root/'data/benchmarks/pumac_power/benchmark.json').read_text(encoding='utf8'))
                 if r['year'] in {2012, 2016, 2019}]
        scores = []
        for row in rows:
            task = ManifestTask(row['problem_id'], row['problem_id'], None, row['problem_description'],
                                row['task_type'], row['total_points'], False, row)
            value = judge_task(task, 'Mock complete written response/proof packet', judge)
            self.assertEqual(value['max_score'], row['total_points'])
            self.assertEqual(value['score'], row['total_points'])
            scores.append(value['score'])
        self.assertEqual(scores, [100, 100, 100, 110, 350, 1025])


if __name__ == '__main__':
    unittest.main()
