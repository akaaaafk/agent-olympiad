"""Provider failures retain usage and stay inside the action budget."""
import copy
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'tests')]
import public_providers
from action_transport import request_single_action
from contest_config import ContestRunConfig
from contest_runner import run_contest
from env_config import RUN_API_KEY_ENV
from llm import LLMRequest
from test_otc_rulecard import arml_manifest

TOOLS = ({'type': 'function', 'name': 'rest', 'parameters': {
    'type': 'object', 'properties': {}, 'additionalProperties': False}},)


def wire(provider, *, truncated=False, tokens=4):
    if provider == 'anthropic':
        return {'stop_reason': 'max_tokens' if truncated else 'tool_use',
                'content': [] if truncated else [{'type': 'tool_use', 'name': 'rest', 'input': {}}],
                'usage': {'input_tokens': 10, 'output_tokens': tokens}}
    if provider == 'gemini':
        return {'candidates': [{'finishReason': 'MAX_TOKENS' if truncated else 'STOP',
                'content': {'parts': [] if truncated else [{'functionCall': {'name': 'rest', 'args': {}}}]}}],
                'usageMetadata': {'promptTokenCount': 10, 'candidatesTokenCount': tokens}}
    return {'choices': [{'finish_reason': 'length' if truncated else 'tool_calls',
                         'message': {} if truncated else {'tool_calls': [{'id': 'x',
                             'function': {'name': 'rest', 'arguments': '{}'}}]}}],
            'usage': {'prompt_tokens': 10, 'completion_tokens': tokens}}


class ProviderRecoveryTests(unittest.TestCase):
    def caller(self, provider):
        self.enterContext(patch.dict(os.environ, {RUN_API_KEY_ENV[provider]: 'offline-test'}, clear=True))
        return public_providers.make_public_caller(provider, 'fixture-model', max_output_tokens=500)

    def request(self, calls=3, tokens=2000):
        return LLMRequest('', 'Call rest.', tools=TOOLS, tool_choice='required', purpose='contest_action',
                          metadata={'max_transport_attempts': calls, 'max_transport_output_tokens': tokens})

    def test_gemini_thought_only_usage_reaches_contest_budget(self):
        reply = wire('gemini', truncated=True)
        reply['usageMetadata'] = {'promptTokenCount': 10, 'thoughtsTokenCount': 500,
                                  'totalTokenCount': 510}
        caller = self.caller('gemini')
        with patch.object(public_providers, '_post', return_value=reply):
            result = run_contest(arml_manifest(), lambda *_: '',
                ContestRunConfig('single_agent', 1, 1, max_api_calls=1, max_tokens=1000),
                action_request_fn=caller)
        self.assertEqual(result['budget']['tokens_used'], 500)
        self.assertEqual(result['budget']['api_calls_used'], 1)

    def test_reported_zero_usage_is_not_replaced_by_estimate(self):
        reply = wire('gemini', truncated=True, tokens=0)
        caller = self.caller('gemini')
        with patch.object(public_providers, '_post', return_value=reply):
            result = run_contest(arml_manifest(), lambda *_: '',
                ContestRunConfig('single_agent', 1, 1, max_api_calls=1, max_tokens=1000),
                action_request_fn=caller)
        self.assertEqual(result['budget']['tokens_used'], 0)

    def test_malformed_native_batch_is_atomic_and_charged_by_engine(self):
        for provider in ('deepseek', 'openai_compatible', 'anthropic', 'gemini'):
            with self.subTest(provider=provider):
                reply = wire(provider, tokens=500)
                if provider == 'anthropic':
                    reply['content'].append({'type': 'tool_use', 'name': 'rest', 'input': []})
                elif provider == 'gemini':
                    reply['candidates'][0]['content']['parts'].append(
                        {'functionCall': {'name': 'rest', 'args': []}})
                else:
                    reply['choices'][0]['message']['tool_calls'].append(
                        {'function': {'name': 'rest', 'arguments': '{broken'}})
                caller = self.caller(provider)
                with patch.object(public_providers, '_post', return_value=reply):
                    response = request_single_action(caller, self.request(calls=1))
                    self.assertFalse(response.tool_calls)
                    self.assertIn('tool_error', response.usage)
                    result = run_contest(arml_manifest(), lambda *_: '',
                        ContestRunConfig('single_agent', 1, 1, max_api_calls=1, max_tokens=1000),
                        action_request_fn=caller)
                self.assertEqual(result['budget']['tokens_used'], 500)
                self.assertEqual(result['budget']['api_calls_used'], 1)
                self.assertEqual(result['diagnostics']['transport_failures'], 1)
                self.assertFalse(result['action_transport_log'])

    def test_missing_unique_choice_retains_returned_usage(self):
        caller = self.caller('deepseek')
        with patch.object(public_providers, '_post', return_value={
                'choices': [], 'usage': {'completion_tokens': 27}}):
            result = caller(self.request())
        self.assertFalse(result.tool_calls)
        self.assertEqual(result.usage['output_tokens'], 27)
        self.assertIn('tool_error', result.usage)

    def test_all_public_providers_recover_truncation_with_shared_budget(self):
        for provider in ('anthropic', 'gemini', 'deepseek', 'openai_compatible'):
            with self.subTest(provider=provider):
                caller = self.caller(provider)
                replies = [wire(provider, truncated=True, tokens=500), wire(provider)]
                with patch.object(public_providers, '_post', side_effect=replies) as post:
                    result = request_single_action(caller, self.request(tokens=550))
                self.assertEqual(post.call_count, 2)
                self.assertEqual([c.name for c in result.tool_calls], ['rest'])
                self.assertEqual(result.usage['output_tokens'], 504)
                self.assertEqual(result.usage['api_calls'], 2)
                self.assertEqual(result.usage['tool_retries'], 1)
                limits = [(c.args[3]['generationConfig']['maxOutputTokens'] if provider == 'gemini'
                           else c.args[3]['max_tokens']) for c in post.call_args_list]
                self.assertEqual(limits, [500, 50])

    def test_truncation_stops_at_api_or_output_budget(self):
        for provider in ('anthropic', 'gemini'):
            caller = self.caller(provider)
            for calls, tokens in [(1, 2000), (3, 500)]:
                with self.subTest(provider=provider, calls=calls, tokens=tokens), patch.object(
                        public_providers, '_post', return_value=wire(provider, truncated=True, tokens=500)) as post:
                    result = request_single_action(caller, self.request(calls, tokens))
                self.assertEqual(post.call_count, 1)
                self.assertFalse(result.tool_calls)
                self.assertEqual(result.usage['output_tokens'], 500)
                self.assertEqual(result.usage['finish_reason'], 'length')
                self.assertEqual(result.usage['provider_finish_reason'],
                                 'max_tokens' if provider == 'anthropic' else 'MAX_TOKENS')

    def test_refusals_are_not_length_retries(self):
        for provider, reason in [('anthropic', 'refusal'), ('gemini', 'SAFETY')]:
            caller = self.caller(provider)
            reply = wire(provider)
            if provider == 'anthropic':
                reply['stop_reason'] = reason
            else:
                reply['candidates'][0]['finishReason'] = reason
            with patch.object(public_providers, '_post', return_value=reply) as post:
                result = request_single_action(caller, self.request())
            self.assertEqual(post.call_count, 1)
            self.assertFalse(result.tool_calls)
            self.assertEqual(result.usage['finish_reason'], reason)


if __name__ == '__main__':
    unittest.main()
