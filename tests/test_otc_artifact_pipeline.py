import json
import sys
import tempfile
import unittest
from pathlib import Path
from dataclasses import replace
from unittest.mock import Mock, patch
from pypdf import PdfWriter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from artifact_contract import contract_for, delivery_route, ArtifactContract
from artifacts.contest_delivery import ArtifactRenderer, validate_source
from artifacts.assets import file_sha256
from otc_artifact_pipeline import prepare_artifact_run, run_artifact_contest
from llm import LLMResponse, LLMToolCall
from evaluation.models import load_rubric
from rules.loader import load_rule_card, DEFAULT_RULES_ROOT
from rules.storage import iter_rule_card_ids
from contest_config import BASELINE_NAMES, ContestRunConfig


class MockTeam:
    def __init__(self, source, approve=True, draft_action='work'):
        self.source, self.approve, self.requests = source, approve, []
        self.draft_action = draft_action
    def __call__(self, request):
        self.requests.append(request)
        if not request.tools:
            return LLMResponse('Coordinate, verify and reconcile.', 'mock', 'mock')
        names = {x['name'] for x in request.tools}
        marker = 'YOUR ELIGIBLE PENDING REVIEWS\n'
        pending = json.JSONDecoder().raw_decode(request.user_prompt.split(marker)[1])[0] if marker in request.user_prompt else []
        if pending and 'review_answer' in names:
            row = pending[0]
            name, args = 'review_answer', dict(problem_id=row['problem_id'],
                version_hash=row['version_hash'], content='Checked the source and rendered pages.',
                decision='approve' if self.approve else 'reject')
        elif self.draft_action in names and 'Agent_1' in request.system_prompt.split('\n')[0]:
            name, args = self.draft_action, {'content': self.source}
        elif 'submit' in names and len(names) == 1:
            name, args = 'submit', {}
        else:
            name, args = 'rest', {'reason': 'Awaiting reconciliation'}
        return LLMResponse('', 'mock', 'mock', tool_calls=(LLMToolCall(name, args),))


class ArtifactPipelineTests(unittest.TestCase):
    def test_iypt_shared_source_limit_matches_otc_work_limit(self):
        card = load_rule_card('iypt', required=True)
        contract = contract_for(card)
        self.assertEqual(contract.max_source_chars, 8000)
        validate_source('x' * 8000, contract)
        with self.assertRaisesRegex(ValueError, 'oversized'):
            validate_source('x' * 8001, contract)
        for variant in ('otc', 'vallina_otc'):
            config = ContestRunConfig(variant, card.team_size_default, 20, rule_card=card)
            self.assertEqual(config.otc_policy.char_limit('work'), contract.max_source_chars)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.task = self.root / 'task.pdf'
        from reportlab.pdfgen import canvas
        task_pdf = canvas.Canvas(str(self.task), pagesize=(720, 540))
        task_pdf.drawString(40, 500, 'Synthetic task: write a report explaining the supplied evidence and assumptions.')
        task_pdf.save()

    def test_artifact_uses_shared_budget_and_records_sampling(self):
        from contest_budget import resolve_contest_budget
        for requested in (None, 1, 91):
            prepared = prepare_artifact_run(competition='vis_moot', task_pdf=self.task,
                output=self.root / 'new', provider='openai', model='mock',
                max_turns=requested, temperature=0.6)
            budget = resolve_contest_budget('vis_moot', max_turns=requested)
            config = prepared['config']
            self.assertEqual(config.max_turns, budget.max_turns)
            self.assertEqual(config.minutes_per_turn, 5)
            self.assertEqual(config.max_simulated_minutes, budget.max_turns * 5)
            self.assertEqual(config.submission_turn, budget.max_turns)
            self.assertIsNone(config.max_tokens)
            self.assertEqual(prepared['identity']['settings']['execution']['temperature'], 0.6)
            self.assertEqual(prepared['temperature'], 0.6)

    def prepare(self, competition='vis_moot'):
        return prepare_artifact_run(competition=competition, task_pdf=self.task,
            output=self.root / 'run', max_turns=2, provider='openai', model='mock',
            judge_model='mock-judge')

    def judge(self, prepared):
        rubric = load_rubric(prepared['rubric'])
        payload = {'criteria': [dict(id=c.id, score=c.min_score, max_score=c.max_score,
            evidence=['Synthetic fixture only'], justification='Mock judge response for plumbing test.',
            confidence=1, observable=c.observable) for c in rubric.criteria],
            'total_score': sum(c.min_score for c in rubric.criteria),
            'max_score': rubric.total_points, 'warnings': [], 'limitations': []}
        def respond(request):
            if request.purpose.startswith('collaboration_'):
                return LLMResponse(json.dumps({'score': 4, 'justification': 'Synthetic collaboration judgment.'}),
                                   'mock', 'mock-judge')
            return LLMResponse(json.dumps(payload), 'mock', 'mock-judge')
        return Mock(side_effect=respond)

    def test_all_cards_configured_without_claiming_live_environment_support(self):
        ids = iter_rule_card_ids(DEFAULT_RULES_ROOT)
        entries = json.loads((ROOT / 'data/benchmarks/index.json').read_text(encoding='utf-8'))['olympiads']
        benchmark_ids = {entry['id'] for entry in entries}
        excluded = set(json.loads((ROOT / 'data/evaluation_access_policy.json').read_text(encoding='utf-8'))['excluded_tracks'])
        self.assertTrue(benchmark_ids.isdisjoint(excluded))
        self.assertTrue(benchmark_ids.issubset(set(ids)))
        for entry in entries:
            self.assertTrue((ROOT / entry['benchmark_path']).is_file(), entry['id'])
        for name in ids:
            card = load_rule_card(name)
            ContestRunConfig('otc', card.team_size_default, card.simulation['max_turns'], rule_card=card)
        with self.assertRaises(ValueError):
            contract_for(load_rule_card('wro'))
        with self.assertRaises(ValueError):
            contract_for(load_rule_card('cfa_research_challenge'))

    def test_missing_rubric_fails_before_model_calls_or_output(self):
        with self.assertRaisesRegex(ValueError, 'no rubric'):
            self.prepare('gcch_harvard')
        self.assertFalse((self.root / 'run').exists())

    def test_security_rejects_active_network_and_local_html(self):
        for content in ('<script>alert(1)</script>', '<img src="file:///C:/secret">',
                        '<style>@import "https://example.com";</style>',
                        '<style>p{background:url(secret)}</style>', '<body onload="x()">',
                        '<p style="background:&#117;rl(file:///secret)">text</p>'):
            with self.subTest(content=content), self.assertRaises(ValueError):
                validate_source(content, ArtifactContract('slides'))

    def test_document_runs_real_otc_renders_reviews_and_scores_same_pdf(self):
        prepared = self.prepare()
        team = MockTeam('A shared research note\n\nEvidence and reasoning for the supplied task.\nConclusion: verify assumptions.')
        judge = self.judge(prepared)
        result = run_artifact_contest(prepared, agent_request=team, judge_request=judge)
        self.assertEqual(result['status'], 'complete')
        self.assertEqual(file_sha256(Path(result['artifact']['pdf'])), result['artifact']['pdf_sha256'])
        rubric_calls = [c for c in judge.call_args_list if not c.args[0].purpose.startswith('collaboration_')]
        self.assertEqual(len(rubric_calls), 1)
        self.assertEqual(result['required_metrics']['CS'], 4.0)
        coach = [r for r in team.requests if r.purpose == 'coach']
        self.assertEqual(len(coach), 1)
        self.assertFalse(coach[0].attachments)
        reviews = [r for r in team.requests if r.tools and 'Checked' not in r.system_prompt
                   and any(t['name'] == 'review_answer' for t in r.tools)
                   and len(r.attachments) == 2]
        self.assertTrue(reviews)
        for request in team.requests:
            self.assertNotIn('STRUCTURED RUBRIC:', request.user_prompt)
            self.assertNotIn('rubric_path', request.system_prompt)
        submission = rubric_calls[0].args[0].attachments[-1]
        self.assertEqual(file_sha256(submission.path), result['artifact']['pdf_sha256'])
        same = run_artifact_contest(prepared, agent_request=Mock(side_effect=AssertionError()),
                                    judge_request=Mock(side_effect=AssertionError()), resume=True)
        self.assertEqual(same['artifact'], result['artifact'])

    def test_all_five_baselines_share_rendering_and_judge_delivery(self):
        for variant in BASELINE_NAMES:
            with self.subTest(variant=variant):
                prepared = prepare_artifact_run(competition='vis_moot', task_pdf=self.task,
                    output=self.root / variant, max_turns=2, provider='openai',
                    model='mock', judge_model='mock-judge', system_variant=variant)
                config = prepared['config']
                self.assertEqual(config.team_size == 1, variant == 'single_agent')
                team = MockTeam('Complete candidate for the writing task.', draft_action='render_pdf')
                judge = self.judge(prepared)
                def act(request):
                    response = team(request)
                    select = next((t for t in request.tools if t['name'] == 'select_problem'), None)
                    if select and response.tool_calls and response.tool_calls[0].name == 'rest':
                        choices = select['parameters']['properties']['problem_id'].get('enum') or ['deliverable']
                        return LLMResponse('', 'mock', 'mock', tool_calls=(
                            LLMToolCall('select_problem', {'problem_id': choices[0]}),))
                    return response
                result = run_artifact_contest(prepared, agent_request=act, judge_request=judge)
                self.assertEqual(result['status'], 'complete')
                if variant == 'single_agent':
                    self.assertFalse(result['coordination_required'])
                    self.assertFalse(prepared['identity']['settings']['evaluation']['judge_collab'])
                    self.assertFalse(any(c.args[0].purpose.startswith('collaboration_') for c in judge.call_args_list))
                    self.assertEqual(result['required_metrics']['CS'], 'N/A')
                    self.assertFalse((prepared['output'] / 'coordination_task.txt').exists())
                rubric_call = next(c for c in judge.call_args_list if c.args[0].attachments)
                self.assertEqual(file_sha256(rubric_call.args[0].attachments[-1].path),
                                 result['artifact']['pdf_sha256'])
                contest = json.loads(Path(result['contest_file']).read_text(encoding='utf-8'))
                self.assertEqual(contest['modules'], config.modules.as_dict())
                self.assertTrue(any(e['kind'] == 'render_pdf' for e in contest['memory']['events']))
                self.assertEqual(sum(r.purpose == 'coach' for r in team.requests), int(config.modules.coach))
                if not config.modules.coach:
                    self.assertTrue(all('BASIC OTC' not in r.system_prompt for r in team.requests))

    def test_rejected_document_is_collected_and_judged_at_deadline(self):
        prepared = self.prepare()
        self.assertIsNone(prepared['config'].max_api_calls)
        judge = self.judge(prepared)
        result = run_artifact_contest(prepared, agent_request=MockTeam('Complete draft.', False),
                                      judge_request=judge)
        self.assertEqual(result['status'], 'complete')
        self.assertEqual(sum(bool(c.args[0].attachments) for c in judge.call_args_list), 1)
        contest = json.loads(Path(result['contest_file']).read_text(encoding='utf-8'))
        self.assertTrue(any(r['decision'] == 'reject' for r in contest['session_checkpoint']['tasks'][0]['reviews']))
        collected = next(e for e in contest['memory']['events'] if e['kind'] == 'deadline_drafts_submitted')
        self.assertTrue(collected['payload']['review_gate_waived'])
        self.assertEqual(Path(result['artifact']['source']).read_text(encoding='utf-8'), 'Complete draft.')

    def test_explicit_render_pdf_records_reviewed_version_and_exact_judged_pdf(self):
        prepared = self.prepare()
        team = MockTeam('Explicit PDF tool\n\nComplete candidate and evidence.', draft_action='render_pdf')
        judge = self.judge(prepared)
        result = run_artifact_contest(prepared, agent_request=team, judge_request=judge)
        self.assertEqual(result['status'], 'complete')
        self.assertTrue(result['artifact']['previews'])
        contest = json.loads(Path(result['contest_file']).read_text(encoding='utf-8'))
        self.assertTrue(any(e['kind'] == 'render_pdf' for e in contest['memory']['events']))
        rubric_call = next(c for c in judge.call_args_list if c.args[0].attachments)
        self.assertEqual(file_sha256(rubric_call.args[0].attachments[-1].path), result['artifact']['pdf_sha256'])

    def test_rejected_explicit_pdf_is_submitted_at_deadline(self):
        prepared = self.prepare()
        judge = self.judge(prepared)
        result = run_artifact_contest(prepared,
            agent_request=MockTeam('Rejected explicit candidate.', approve=False, draft_action='render_pdf'),
            judge_request=judge)
        self.assertEqual(result['status'], 'complete')
        self.assertEqual(sum(bool(c.args[0].attachments) for c in judge.call_args_list), 1)
        rubric_call = next(c for c in judge.call_args_list if c.args[0].attachments)
        self.assertEqual(file_sha256(rubric_call.args[0].attachments[-1].path), result['artifact']['pdf_sha256'])

    def test_unreviewed_slides_are_collected_and_rendered_for_judging(self):
        prepared = self.prepare('ieo_business_case')
        source = '<html><body><section><h1>Final candidate</h1><p>Evidence and proposal.</p></section></body></html>'
        team = MockTeam(source)
        def without_review(request):
            response = team(request)
            if response.tool_calls and response.tool_calls[0].name == 'review_answer':
                return LLMResponse('', 'mock', 'mock', tool_calls=(LLMToolCall('rest', {'reason': 'No review completed'}),))
            return response
        judge = self.judge(prepared)
        result = run_artifact_contest(prepared, agent_request=without_review, judge_request=judge)
        self.assertEqual(result['status'], 'complete')
        contest = json.loads(Path(result['contest_file']).read_text(encoding='utf-8'))
        self.assertEqual(contest['session_checkpoint']['tasks'][0]['reviews'], [])
        self.assertEqual(Path(result['artifact']['source']).read_text(encoding='utf-8'), source)
        self.assertEqual(sum(bool(c.args[0].attachments) for c in judge.call_args_list), 1)

    def test_slide_candidate_is_html_then_pdf_and_reviewed_before_grading(self):
        prepared = self.prepare('ieo_business_case')
        html = '<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><style>body{font-family:Arial}h1{font-size:42px}</style></head><body><section><h1>Delivery fixture</h1><p>Evidence and proposal.</p></section></body></html>'
        team, judge = MockTeam(html), self.judge(prepared)
        result = run_artifact_contest(prepared, agent_request=team, judge_request=judge)
        self.assertEqual(result['status'], 'complete')
        self.assertEqual(result['artifact']['pages'], 1)
        self.assertEqual(Path(result['artifact']['source']).read_text(encoding='utf-8'), html)

    def test_changed_rubric_or_task_blocks_resume(self):
        prepared = self.prepare()
        team = MockTeam('Complete draft.')
        run_artifact_contest(prepared, agent_request=team, judge_request=self.judge(prepared))
        changed = dict(prepared, identity=dict(prepared['identity']))
        changed['identity']['settings'] = dict(prepared['identity']['settings'], extra='changed')
        from contest_run_identity import content_hash
        changed['identity']['fingerprint'] = content_hash(changed['identity']['settings'])
        with self.assertRaises(ValueError):
            run_artifact_contest(changed, agent_request=Mock(), judge_request=Mock(), resume=True)

    def test_tampered_pdf_is_not_silently_reused(self):
        renderer = ArtifactRenderer(self.root / 'versions', ArtifactContract('document'))
        receipt = renderer(None, 'render_pdf', {'content': 'Version one'})
        Path(receipt['pdf']).write_bytes(b'tampered')
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            renderer(None, 'render_pdf', {'content': 'Version one'})

    def test_judge_failure_resumes_without_rerunning_team(self):
        prepared = self.prepare()
        with self.assertRaisesRegex(RuntimeError, 'judge unavailable'):
            run_artifact_contest(prepared, agent_request=MockTeam('Approved complete draft.'),
                                 judge_request=Mock(side_effect=RuntimeError('judge unavailable')))
        result = run_artifact_contest(prepared, resume=True,
            agent_request=Mock(side_effect=AssertionError('Team must not run twice')),
            judge_request=self.judge(prepared))
        self.assertEqual(result['status'], 'complete')

    def test_invalid_judge_response_recovers_in_one_run_without_repeating_solver(self):
        from otc_artifact_pipeline import run_contest
        prepared = self.prepare()
        valid_judge = self.judge(prepared)
        task_attempts = []
        def judge(request):
            if request.purpose == 'evaluation':
                task_attempts.append(request)
                if len(task_attempts) == 1:
                    return LLMResponse('{"criteria":', 'mock', 'mock-judge',
                                       usage={'output_tokens': 7})
            return valid_judge(request)
        with patch('otc_artifact_pipeline.run_contest', wraps=run_contest) as solver:
            result = run_artifact_contest(prepared,
                agent_request=MockTeam('Approved complete draft.'), judge_request=judge)
        solver.assert_called_once()
        self.assertEqual(result['status'], 'complete')
        self.assertEqual(len(task_attempts), 2)
        self.assertEqual(task_attempts[0].attachments, task_attempts[1].attachments)
        self.assertEqual(result['task_evaluation_usage']['api_calls'], 2)
        raw = [json.loads(line) for line in
               (prepared['output'] / 'judge_responses.jsonl').read_text().splitlines()]
        self.assertEqual(len(raw), 2)
        self.assertEqual(raw[0]['text'], '{"criteria":')
        self.assertEqual(raw[1]['metadata']['evaluation_attempt'], 2)

    def test_evaluation_only_after_code_update_preserves_solver_and_raw_response(self):
        from contest_run_identity import content_hash
        from evaluation.models import EvaluationError
        prepared = self.prepare()
        malformed = LLMResponse('{"bad":', 'mock', 'mock-judge')
        with self.assertRaises(EvaluationError):
            run_artifact_contest(prepared, agent_request=MockTeam('Approved complete draft.'),
                                 judge_request=Mock(return_value=malformed))
        output = prepared['output']
        session_bytes = (output / 'contest_session.json').read_bytes()
        identity_bytes = (output / 'run_identity.json').read_bytes()
        raw = json.loads((output / 'judge_responses.jsonl').read_text().splitlines()[0])
        self.assertEqual(raw['text'], malformed.text)
        changed = dict(prepared)
        changed['identity'] = json.loads(json.dumps(prepared['identity']))
        changed['identity']['settings']['source_hashes']['evaluation/models.py'] = 'updated'
        changed['identity']['settings']['action_set_version'] += 1
        changed['identity']['settings']['evaluation']['rubric_override'] = True
        changed['identity']['fingerprint'] = content_hash(changed['identity']['settings'])
        forbidden_solver = Mock(side_effect=AssertionError('Solver must not run'))
        with self.assertRaises(ValueError):
            run_artifact_contest(changed, resume=True, agent_request=forbidden_solver,
                                 judge_request=self.judge(prepared))
        wrong_settings = json.loads(json.dumps(changed['identity']))
        wrong_settings['settings']['evaluation']['model'] = 'different-judge'
        wrong_settings['fingerprint'] = content_hash(wrong_settings['settings'])
        with self.assertRaises(ValueError):
            run_artifact_contest(dict(changed, identity=wrong_settings), resume=True,
                                 evaluation_only=True, agent_request=forbidden_solver,
                                 judge_request=self.judge(prepared))
        wrong_rubric = json.loads(json.dumps(changed['identity']))
        wrong_rubric['settings']['evaluation']['rubric_sha256'] = 'changed-rubric'
        wrong_rubric['fingerprint'] = content_hash(wrong_rubric['settings'])
        with self.assertRaises(ValueError):
            run_artifact_contest(dict(changed, identity=wrong_rubric), resume=True,
                                 evaluation_only=True, agent_request=forbidden_solver,
                                 judge_request=self.judge(prepared))
        unfinished = json.loads(session_bytes)
        unfinished['session_checkpoint']['final_summary'] = None
        (output / 'contest_session.json').write_text(json.dumps(unfinished), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'finalized'):
            run_artifact_contest(changed, resume=True, evaluation_only=True,
                                 agent_request=forbidden_solver, judge_request=self.judge(prepared))
        (output / 'contest_session.json').write_bytes(session_bytes)
        result = run_artifact_contest(changed, resume=True, evaluation_only=True,
                                     agent_request=forbidden_solver, judge_request=self.judge(prepared))
        self.assertEqual(result['status'], 'complete')
        forbidden_solver.assert_not_called()
        self.assertEqual((output / 'contest_session.json').read_bytes(), session_bytes)
        self.assertEqual((output / 'run_identity.json').read_bytes(), identity_bytes)
        audit = json.loads((output / 'evaluation_resume_identity.jsonl').read_text().splitlines()[0])
        self.assertEqual(audit['evaluation_identity'], changed['identity'])

    def test_oversized_source_is_not_silently_truncated_and_scored(self):
        prepared = self.prepare()
        judge = self.judge(prepared)
        result = run_artifact_contest(prepared,
            agent_request=MockTeam('x' * 60001), judge_request=judge)
        self.assertEqual(result['status'], 'unsubmitted')
        self.assertTrue(all(c.args[0].purpose.startswith('collaboration_') for c in judge.call_args_list))

    def test_required_cs_failure_resumes_judges_without_solver_render_or_rubric(self):
        prepared = self.prepare()
        rubric_judge = self.judge(prepared)
        failed = False
        def first(request):
            nonlocal failed
            if request.purpose == 'collaboration_planning_score' and not failed:
                failed = True
                raise RuntimeError('Synthetic transient judge failure')
            return rubric_judge(request)
        result = run_artifact_contest(prepared, agent_request=MockTeam('Complete research note.'), judge_request=first)
        self.assertEqual(result['status'], 'evaluation_pending')
        self.assertEqual(result['evaluation_pending'], ['coordination'])
        self.assertEqual(result['required_metrics']['CS'], 'N/A')
        saved_session = Path(result['contest_file']).read_bytes()
        artifact = result['artifact']
        retry_calls = []
        def retry(request):
            retry_calls.append(request.purpose)
            self.assertEqual(request.purpose, 'collaboration_planning_score')
            return rubric_judge(request)
        resumed = run_artifact_contest(prepared, agent_request=Mock(side_effect=AssertionError('Solver rerun')),
            judge_request=retry, renderer=Mock(side_effect=AssertionError('Render rerun')), resume=True)
        self.assertEqual(resumed['status'], 'complete')
        self.assertEqual(resumed['required_metrics']['CS'], 4)
        self.assertEqual(resumed['artifact'], artifact)
        self.assertEqual(Path(result['contest_file']).read_bytes(), saved_session)
        self.assertEqual(retry_calls, ['collaboration_planning_score'])

    def test_crash_after_rubric_cannot_leave_a_false_complete_result(self):
        prepared = self.prepare()
        with patch('saved_run_metrics.ensure_coordination', side_effect=ValueError('Synthetic pre-evaluation interruption')):
            with self.assertRaisesRegex(ValueError, 'interruption'):
                run_artifact_contest(prepared, agent_request=MockTeam('Complete report.'),
                                     judge_request=self.judge(prepared))
        saved = json.loads((prepared['output'] / 'result.json').read_text(encoding='utf-8'))
        self.assertTrue(saved['graded'])
        self.assertEqual(saved['status'], 'evaluation_pending')
        self.assertEqual(saved['evaluation_pending'], ['coordination'])
        resumed = run_artifact_contest(prepared, agent_request=Mock(side_effect=AssertionError('Solver rerun')),
                                      judge_request=self.judge(prepared), resume=True)
        self.assertEqual(resumed['status'], 'complete')

    def test_legacy_entry_delegates_to_canonical_runner(self):
        import run_presentation_artifact as legacy
        with patch.object(legacy, 'run_otc', return_value=0) as runner:
            legacy.main(['--competition', 'ieo_business_case', '--task-pdf', str(self.task),
                         '--rounds', '4', '--prepare-only'])
        argv = runner.call_args.args[0]
        self.assertIn('--prepare-only', argv)
        self.assertEqual(argv[argv.index('--max-turns') + 1], '4')


if __name__ == '__main__':
    unittest.main()
