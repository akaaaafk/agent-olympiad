import csv
import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
from concurrent.futures import ThreadPoolExecutor

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
import llm
import vjudge_gateway as gateway
from env import OlympiadEnvironment
import runtime_resources


class InterfacePollutionRepairs(unittest.TestCase):
    def test_resource_selector_hash_containment_and_shared_resolution(self):
        from action_modules.task_specific import _has_resource
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            assets = []
            for name in ('lab_a.txt', 'lab_b.txt'):
                path = root / name
                path.write_text(name, encoding='utf-8')
                assets.append(dict(role='agent_visible', path=name,
                                   sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
            data = {'assets': assets}
            env = object.__new__(OlympiadEnvironment)
            env.problem_data = data
            with patch.object(runtime_resources, 'REPO_ROOT', root):
                self.assertTrue(_has_resource(data, 'read_lab_equipment'))
                self.assertTrue(env._tool_has_runtime_resource('read_lab_equipment'))
                self.assertEqual(env._tool_asset_text('lab', 'lab_b.txt'), 'lab_b.txt')
                self.assertIsNone(env._tool_asset_text('lab', 'unknown'))
                self.assertIsNone(env._tool_asset_text('lab', 'lab'))
                assets[0]['sha256'] = 'bad'
                self.assertIsNone(env._tool_asset_text('lab', 'lab_a.txt'))
                assets[1]['path'] = str(root.parent / 'lab_outside.txt')
                self.assertFalse(_has_resource(data, 'read_lab_equipment'))

    def test_submission_scope_survives_checkpoint_and_separates_runs(self):
        from contest_session import ContestSession, ContestBudgetState, TaskUnit
        from submission_policy import SubmissionPolicy
        def new():
            return ContestSession(tasks=[TaskUnit('code', kind='programming')],
                                  budget=ContestBudgetState(max_turns=2),
                                  submission_policy=SubmissionPolicy())
        first, second = new(), new()
        restored = ContestSession.from_checkpoint(first.checkpoint())
        self.assertEqual(first.submission_run_id, restored.submission_run_id)
        self.assertNotEqual(first.submission_run_id, second.submission_run_id)

    def test_actual_remote_submit_key_is_stable_and_source_bound(self):
        import os
        envs = [object.__new__(OlympiadEnvironment) for _ in range(3)]
        for index, env in enumerate(envs):
            env.problem_data = {'evaluation': {'vjudge_prob_num': '4A', 'vjudge_oj': 'CodeForces'}}
            env.competition_id, env.problem_id = 'icpc', 'task'
            env.submission_run_id = 'restored-run' if index < 2 else 'different-run'
            env.submission_attempts = index + 1
        keys = []
        with patch.dict(os.environ, {}, clear=True), patch('judge.vjudge_gateway_client.gateway_enabled', return_value=True), patch('judge.vjudge_gateway_client.submit_via_gateway', side_effect=lambda **kwargs: keys.append(kwargs['idempotency_key'])):
            for env in envs:
                env._maybe_vjudge_remote_submit('print(1)', local_language='python3')
            envs[0]._maybe_vjudge_remote_submit('print(2)', local_language='python3')
        self.assertEqual(keys[0], keys[1])
        self.assertNotEqual(keys[0], keys[2])
        self.assertNotEqual(keys[0], keys[3])

    def test_judge_only_resource_is_never_readable(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'lab_judge_only.txt'
            path.write_text('SECRET_GOLD', encoding='utf-8')
            env = object.__new__(OlympiadEnvironment)
            env.problem_data = {'assets': [{'role': 'judge_only', 'path': str(path)}]}
            self.assertFalse(env._tool_has_runtime_resource('read_lab_equipment'))
            self.assertIsNone(env._tool_asset_text('lab', 'lab'))

    def test_blocked_report_cannot_publish_a_foreign_score(self):
        spec = importlib.util.spec_from_file_location('pipeline_repair', ROOT / 'scripts/run_pipeline.py')
        pipeline = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pipeline)
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            pipeline.write(out / 'runs/foreign/contest_session.json', {'grade': {'score': 999}})
            job = dict(id='foreign', competition='arml_local', session='foreign', route='native', blockers=[])
            pipeline.report(out, {'jobs': [job]}, {'foreign': {'status': 'blocked', 'reason': 'identity mismatch'}})
            with (out / 'summary.tsv').open(encoding='utf-8', newline='') as stream:
                self.assertEqual(next(csv.DictReader(stream, delimiter='\t'))['score'], '')

    def test_tinker_cannot_retry_after_exhausting_output_budget(self):
        caller = Mock(side_effect=['invalid' * 200, '{"name":"rest","arguments":{}}'])
        with patch.object(llm, 'make_tinker_caller', return_value=caller):
            fn = llm.make_tinker_request_fn('mock')
            result = fn(llm.LLMRequest('s', 'u', tools=({'type': 'function', 'name': 'rest', 'parameters': {'type': 'object', 'properties': {}}},), tool_choice='required', metadata={'max_transport_output_tokens': 1, 'max_output_tokens_override': 1, 'max_transport_attempts': 2}))
        self.assertEqual(caller.call_count, 1)
        self.assertFalse(result.tool_calls)

    def test_gateway_rejects_reused_key_with_different_payload(self):
        data = dict(contest_id='', oj='CodeForces', problem='NEW', language='python3', source='wrong', idempotency_key='same')
        existing = dict(idempotency_key='same', contest_id='', oj='CodeForces', problem='OLD', language='python3', verdict='AC', request_sha256='old')
        replies = []
        with patch.dict(gateway._RUNS, {'old': existing}, clear=True), patch.object(gateway, '_read_json', return_value=data), patch.object(gateway, '_json_response', side_effect=lambda _, status, value: replies.append((status, value))), patch.object(gateway, '_remote_client') as client:
            gateway.GatewayHandler.do_POST(SimpleNamespace(path='/v1/submit'))
        self.assertEqual(replies[0][0], 409)
        client.assert_not_called()

    def test_concurrent_identical_gateway_retries_submit_once(self):
        import threading
        import time
        data = dict(oj='CodeForces', problem='4A', language='python3', source='print(1)', idempotency_key='run:task:source')
        remote = SimpleNamespace(run_id='remote', to_dict=lambda: {'run_id': 'remote', 'verdict': 'AC', 'status': 'done'})
        client = Mock()
        both_read = threading.Barrier(2)
        def read(_):
            both_read.wait(timeout=3)
            return data
        def submit(_):
            time.sleep(0.05)  # Keep the side effect in flight during the retry.
            return remote
        client.submit_and_poll.side_effect = submit
        replies = []
        with patch.dict(gateway._RUNS, {}, clear=True), patch.object(gateway, '_read_json', side_effect=read), patch.object(gateway, '_remote_client', return_value=client), patch.object(gateway, '_json_response', side_effect=lambda _, status, value: replies.append((status, value))):
            with ThreadPoolExecutor(max_workers=2) as workers:
                futures = [workers.submit(gateway.GatewayHandler.do_POST, SimpleNamespace(path='/v1/submit')) for _ in range(2)]
                for future in futures:
                    future.result(timeout=5)
        self.assertEqual(client.submit_and_poll.call_count, 1)
        self.assertEqual([status for status, _ in replies], [200, 200])
        self.assertEqual(replies[0][1]['gateway_run_id'], replies[1][1]['gateway_run_id'])

    def test_gateway_receipts_restore_binding_without_source_or_credentials(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'receipts.json'
            row = dict(gateway_run_id='g', request_sha256='a' * 64,
                       idempotency_key='intent', verdict='AC', status='done',
                       raw={'cookie': 'DO_NOT_PERSIST'}, source='DO_NOT_PERSIST')
            with patch.dict(gateway._RUNS, {'g': row}, clear=True), patch.object(gateway, '_RECEIPTS_PATH', path):
                gateway._save_receipts()
                self.assertNotIn('DO_NOT_PERSIST', path.read_text(encoding='utf-8'))
                gateway._RUNS.clear()
                gateway._load_receipts(path)
                self.assertEqual(gateway._RUNS['g']['request_sha256'], 'a' * 64)
                self.assertEqual(gateway._RUNS['g']['verdict'], 'AC')

    def test_real_tinker_sampler_caps_tokens_and_preserves_stop_reason(self):
        from test_tinker_provider import _native_sdk
        import os
        sdk, _, client, _, _ = _native_sdk([1, 2], decoded='{"name":"rest","arguments":{}}', sequences=[SimpleNamespace(tokens=[7, 8], stop_reason='length')])
        with patch.dict(os.environ, {'TINKER_API_KEY': 'mock'}, clear=True), patch.dict(sys.modules, {'tinker': sdk}):
            fn = llm.make_tinker_request_fn('Qwen/Qwen3.6-35B-A3B')
            result = fn(llm.LLMRequest('s', 'u', tools=({'type': 'function', 'name': 'rest', 'parameters': {'type': 'object', 'properties': {}}},), tool_choice='required', metadata={'max_transport_output_tokens': 2, 'max_transport_attempts': 1}))
        self.assertEqual(sdk.SamplingParams.call_args.kwargs['max_tokens'], 2)
        self.assertEqual(client.sample.call_count, 1)
        self.assertEqual(result.usage['output_tokens'], 2)
        self.assertEqual(result.usage['input_tokens'], 2 + len('{"name":"'))
        self.assertEqual(result.usage['finish_reason'], 'length')
        self.assertFalse(result.tool_calls)

    def test_native_report_consumes_validated_snapshot(self):
        spec = importlib.util.spec_from_file_location('pipeline_snapshot_repair', ROOT / 'scripts/run_pipeline.py')
        pipeline = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pipeline)
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            pipeline.write(out / 'runs/a/contest_session.json', {'grade': {'score': 999}})
            job = dict(id='a', competition='arml_local', session='a', route='native', blockers=[])
            with patch('contest_run_identity.read_completed_contest_result', return_value={'grade': {'score': 7}}) as validated:
                pipeline.report(out, {'jobs': [job]}, {'a': {'status': 'complete', 'run_identity': {'fingerprint': 'expected'}}})
            validated.assert_called_once()
            with (out / 'summary.tsv').open(encoding='utf-8', newline='') as stream:
                self.assertEqual(next(csv.DictReader(stream, delimiter='\t'))['score'], '7')

    def test_empty_tinker_sample_still_charges_native_usage(self):
        from test_tinker_provider import _native_sdk
        import os
        sdk, *_ = _native_sdk([1, 2], decoded='', sequences=[SimpleNamespace(tokens=[7], stop_reason='length')])
        with patch.dict(os.environ, {'TINKER_API_KEY': 'mock'}, clear=True), patch.dict(sys.modules, {'tinker': sdk}):
            fn = llm.make_tinker_request_fn('mock')
            result = fn(llm.LLMRequest('s', 'u', metadata={'max_transport_output_tokens': 1}))
        self.assertEqual(result.usage['output_tokens'], 1)
        self.assertEqual(result.usage['api_calls'], 1)
        self.assertEqual(result.usage['finish_reason'], 'length')
        self.assertFalse(result.tool_calls)

    def test_memory_off_pdf_does_not_leak_across_rounds(self):
        from pypdf import PdfWriter
        from artifacts.pdf_ingest import extract_pdf_text
        from otc_artifact_pipeline import prepare_artifact_run, run_artifact_contest
        from test_otc_artifact_pipeline import ArtifactPipelineTests
        import otc_artifact_pipeline as artifact
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            task = root / 'task.pdf'
            writer = PdfWriter()
            writer.add_blank_page(width=720, height=540)
            with task.open('wb') as stream:
                writer.write(stream)
            prepared = prepare_artifact_run(competition='vis_moot', task_pdf=task, output=root / 'run', max_turns=3, provider='openai', model='mock', judge_model='mock-judge', system_variant='vallina_otc')
            counts, observations = {}, []
            def agent(request):
                if not request.tools:
                    return llm.LLMResponse('Coordinate independently.', 'mock', 'mock')
                who = request.metadata['agent']
                counts[who] = counts.get(who, 0) + 1
                pdf_canary = any('OLD_DRAFT_CANARY' in extract_pdf_text(a.path)[0] for a in request.attachments[1:])
                observations.append((counts[who], pdf_canary))
                call = llm.LLMToolCall('render_pdf', {'content': 'OLD_DRAFT_CANARY'}) if who == 'Agent_1' and counts[who] == 1 else llm.LLMToolCall('rest', {'reason': 'wait'})
                return llm.LLMResponse('', 'mock', 'mock', tool_calls=(call,))
            snapshots = []
            original_write = artifact._write
            def capture(path, data):
                original_write(path, data)
                if path.name == 'contest_checkpoint.json' and data['session']['budget']['turns_used'] == 2 and data['session']['final_summary'] is None:
                    snapshots.append(json.loads(json.dumps(data)))
            with patch.object(artifact, '_write', side_effect=capture):
                result = run_artifact_contest(prepared, agent_request=agent, judge_request=ArtifactPipelineTests().judge(prepared))
            self.assertEqual(result['status'], 'complete')
            self.assertTrue(any(canary for turn, canary in observations if turn == 1))
            self.assertTrue(all(not canary for turn, canary in observations if turn > 1))
            self.assertTrue(snapshots)
            (root / 'run/result.json').unlink()
            (root / 'run/contest_session.json').unlink()
            original_write(root / 'run/contest_checkpoint.json', snapshots[0])
            observations.clear()
            resumed = run_artifact_contest(prepared, resume=True, agent_request=agent, judge_request=ArtifactPipelineTests().judge(prepared))
            self.assertEqual(resumed['status'], 'complete')
            self.assertTrue(observations)
            self.assertTrue(all(not canary for _, canary in observations))
