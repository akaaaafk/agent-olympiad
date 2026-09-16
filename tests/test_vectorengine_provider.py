import os
import unittest
from unittest.mock import patch
import llm
import run_competition_batch as cli


class VectorEngineTests(unittest.TestCase):
    def test_key_isolation(self):
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'other', 'OPENAGENTS_API_KEY': 'gateway'}, clear=True):
            with self.assertRaisesRegex(ValueError, 'VECTORENGINE_API_KEY'):
                llm.resolve_request_fn('vectorengine')

    def test_native_call_and_output_ceiling(self):
        with patch.dict(os.environ, {'VECTORENGINE_API_KEY': 'test'}, clear=True), patch('openai.OpenAI') as sdk:
            sdk.return_value.chat.completions.create.return_value.model_dump.return_value = {
                'choices': [{'finish_reason': 'tool_calls', 'message': {'tool_calls': [
                    {'id': 'a', 'function': {'name': 'work', 'arguments': '{}'}}]}}],
                'usage': {'completion_tokens': 5}}
            result = llm.resolve_request_fn('vectorengine')(llm.LLMRequest('s', 'u',
                tools=({'type': 'function', 'name': 'work', 'parameters': {'type': 'object'}},),
                metadata={'max_output_tokens_override': 16384}))
            self.assertEqual(sdk.call_args.kwargs['base_url'], 'https://api.vectorengine.ai/v1')
            sent = sdk.return_value.chat.completions.create.call_args.kwargs
            self.assertEqual(sent['model'], 'claude-sonnet-5')
            self.assertEqual(sent['max_tokens'], 8192)
            self.assertEqual(result.tool_calls[0].name, 'work')
            self.assertEqual(result.provider, 'vectorengine')

    def test_cli(self):
        args = cli._build_parser().parse_args(['--provider', 'vectorengine', '--judge-provider', 'vectorengine'])
        self.assertEqual(args.provider, 'vectorengine')
        self.assertEqual(cli._judge_api_key_name('vectorengine'), 'VECTORENGINE_API_KEY')
