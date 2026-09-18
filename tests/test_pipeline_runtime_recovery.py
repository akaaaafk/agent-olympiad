import json
from pathlib import Path
import subprocess
import sys
import socket
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'scripts')]
from pipeline_process import PipelineLock, pid_alive, run_child
from evaluation.cce import _parse_json_object
from evaluation.models import load_judge_json
import run_pipeline as pipeline


class RuntimeRecoveryTests(unittest.TestCase):
    def test_auxiliary_json_repairs_only_invalid_escapes(self):
        raw = r'{"reason":"Use \sqrt{2}; line\nquote\"; \\alpha"}'
        for parser in (load_judge_json, _parse_json_object):
            result = parser(raw)
            self.assertEqual(result['reason'], 'Use \\sqrt{2}; line\nquote"; \\alpha')
            with self.assertRaises(json.JSONDecodeError):
                parser(r'{"reason":"\sqrt{2}","score":}')

    def test_dead_owner_recovers_but_live_child_and_unknown_lock_do_not(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'pipeline.lock'
            path.write_text(json.dumps({'pid': 123, 'host': socket.gethostname(), 'token': 'old',
                                        'child_pid': 456, 'launching': False}))
            with patch('pipeline_process.pid_alive', return_value=False):
                with PipelineLock(path):
                    self.assertNotEqual(json.loads(path.read_text())['pid'], 123)
                self.assertFalse(path.exists())
            for payload, alive in [({'pid': 123, 'host': socket.gethostname(), 'token': 'old',
                                    'child_pid': 456, 'launching': False}, lambda pid: pid == 456),
                                   ({'pid': 123, 'host': socket.gethostname(), 'token': 'old',
                                     'child_pid': None, 'launching': True}, lambda pid: False),
                                   ({'pid': 123}, lambda pid: False),
                                   (123, lambda pid: False)]:
                path.write_text(json.dumps(payload))
                before = path.read_bytes()
                with patch('pipeline_process.pid_alive', side_effect=alive):
                    with self.assertRaises(FileExistsError):
                        with PipelineLock(path):
                            self.fail('Unsafe lock recovery')
                self.assertEqual(path.read_bytes(), before)

    def test_coordination_and_ihs_accept_latex_in_real_judge_response(self):
        from evaluation.collaboration_score import score_coordination, score_interaction_helpfulness
        from llm import LLMResponse
        def request(_):
            return LLMResponse(text=r'{"score":4,"justification":"Uses \sqrt{2}","labels":["helpful"]}',
                               provider='mock', model='mock')
        args = dict(request_fn=request, task_text='Solve', agents=['A', 'B'], schema='centralized',
                    chat_history=[{'sender': 'A', 'message': 'Use the formula.'}])
        result = score_coordination(**args)
        self.assertEqual(result.planning_score, 4)
        self.assertEqual(result.communication_score, 4)
        result = score_interaction_helpfulness(**args)
        self.assertEqual(result.interaction_helpfulness_score, 4)

    def test_real_child_timeout_preserves_checkpoint_and_releases_lock(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            checkpoint = root / 'checkpoint.json'
            checkpoint.write_text('{"completed":1}')
            with PipelineLock(root / 'pipeline.lock') as owner, (root / 'child.log').open('w') as log:
                with self.assertRaises(subprocess.TimeoutExpired):
                    run_child([sys.executable, '-c', 'import time; time.sleep(60)'],
                              cwd=root, log=log, timeout=0.3, owner=owner)
                self.assertIsNone(owner.record['child_pid'])
            self.assertEqual(checkpoint.read_text(), '{"completed":1}')
            self.assertFalse((root / 'pipeline.lock').exists())

    def test_real_process_liveness(self):
        import os
        self.assertTrue(pid_alive(os.getpid()))
        process = subprocess.Popen([sys.executable, '-c', 'pass'])
        process.wait()
        self.assertFalse(pid_alive(process.pid))


if __name__ == '__main__':
    unittest.main()
