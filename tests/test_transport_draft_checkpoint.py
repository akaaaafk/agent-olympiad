"""Unexecuted adapter buffers survive checkpoints without crossing actors/tasks."""
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from contest_engine import _ContestEngine, _AgentTurn
from contest_config import ContestRunConfig
from contest_manifest import ContestManifest, ManifestTask
from llm import LLMResponse, LLMToolCall
from tinker_action import VERSION, draft_scope


class DraftCheckpointTests(unittest.TestCase):
    def test_private_buffer_round_trip_and_clear_after_valid_action(self):
        manifest = ContestManifest('s', 'arml_local', (
            ManifestTask('q', 'q', None, '6*7?', 'math', 1, False, {}),))
        cfg = ContestRunConfig('single_agent', 1, 4, max_api_calls=12, max_tokens=10000)
        seen = []
        pending_body = {'model': 'test', 'name': 'work', 'arguments': {},
                        'body_argument': 'content', 'tokens': [11, 12, 13],
                        'system_prompt': 'sys', 'user_prompt': 'user', 'tool': {'name': 'work'}}
        def failed(request):
            seen.append(request)
            return LLMResponse('', 'tinker', 'test', usage={
                'api_calls': 1, 'output_tokens': 3, 'tool_error': 'incomplete',
                'transport_recovery_managed': True,
                'unexecuted_action_draft': {'scope': draft_scope(request),
                    'text': 'PRIVATE_UNEXECUTED', 'executed': False, 'version': VERSION,
                    'pending_body': pending_body},
                'sampling_trace': [{'stage': 'body', 'text': 'PRIVATE_UNEXECUTED', 'executed': False}]})
        engine = _ContestEngine(manifest, lambda *_: '', cfg,
                                action_request_fn=failed, action_transport='emulated')
        turn = _AgentTurn('Agent_1')
        self.assertFalse(engine._request_action(turn))
        self.assertEqual(engine.transport_drafts['Agent_1']['text'], 'PRIVATE_UNEXECUTED')
        self.assertNotIn('PRIVATE_UNEXECUTED', engine.memory.to_checkpoint_json())
        self.assertFalse(engine.session.tasks[0].versions)
        saved = json.loads(json.dumps(engine._checkpoint()))
        def good(request):
            seen.append(request)
            return LLMResponse('', 'tinker', 'test', usage={'api_calls': 1, 'output_tokens': 1},
                               tool_calls=(LLMToolCall('rest', {}),))
        resumed = _ContestEngine(manifest, lambda *_: '', cfg, action_request_fn=good,
            action_transport='emulated', session_checkpoint=saved,
            memory_checkpoint=engine.memory.to_checkpoint_json())
        # A different actor must not even receive the private metadata buffer.
        resumed._request_action(_AgentTurn('Agent_2'))
        self.assertIsNone(seen[-1].metadata['unexecuted_action_draft'])
        resumed._request_action(_AgentTurn('Agent_1'))
        self.assertEqual(seen[-1].metadata['unexecuted_action_draft']['text'], 'PRIVATE_UNEXECUTED')
        self.assertEqual(seen[-1].metadata['unexecuted_action_draft']['pending_body'], pending_body)
        self.assertNotIn('Agent_1', resumed.transport_drafts)
        self.assertEqual(resumed.action_sampling_log[0]['text'], 'PRIVATE_UNEXECUTED')


if __name__ == '__main__':
    unittest.main()
