"""Partial calls never execute; retries obey available API and output budgets."""
import unittest
from unittest.mock import Mock
from llm import LLMRequest, LLMResponse, LLMToolCall
from action_transport import request_single_action


class TransportBudgetTests(unittest.TestCase):
    def test_multi_call_repair_cannot_run_after_output_budget_exhaustion(self):
        batch = LLMResponse('', 'openai', 'glm-5.2',
            tool_calls=(LLMToolCall('rest', {}), LLMToolCall('check_budget', {})),
            usage={'output_tokens': 8, 'max_output_tokens': 8192})
        fn = Mock(return_value=batch)
        result = request_single_action(fn, LLMRequest('s', 'u',
            metadata={'max_transport_output_tokens': 8}))
        self.assertEqual(fn.call_count, 1)
        self.assertFalse(result.tool_calls)
        self.assertEqual(result.usage['tool_retries'], 0)
        self.assertEqual(result.usage['output_tokens'], 8)

    def test_multi_call_repair_caps_remaining_output(self):
        batch = LLMResponse('', 'openai', 'glm-5.2',
            tool_calls=(LLMToolCall('rest', {}), LLMToolCall('check_budget', {})),
            usage={'output_tokens': 8, 'max_output_tokens': 8192})
        good = LLMResponse('', 'openai', 'glm-5.2',
                           tool_calls=(LLMToolCall('rest', {}),), usage={'output_tokens': 2})
        fn = Mock(side_effect=[batch, good])
        result = request_single_action(fn, LLMRequest('s', 'u',
            metadata={'max_transport_output_tokens': 10}))
        self.assertEqual(fn.call_args.args[0].metadata['max_output_tokens_override'], 2)
        self.assertEqual(result.usage['output_tokens'], 10)

    def partial(self):
        return LLMResponse('', 'openai', 'glm-5.2', tool_calls=(LLMToolCall('work', {}),),
                           usage={'finish_reason': 'length', 'output_tokens': 8192,
                                  'input_tokens': 12, 'max_output_tokens': 8192})

    def test_partial_call_at_api_limit_is_rejected_and_charged(self):
        fn = Mock(return_value=self.partial())
        result = request_single_action(fn, LLMRequest('s', 'u', metadata={'max_transport_attempts': 1}))
        self.assertEqual(fn.call_count, 1)
        self.assertFalse(result.tool_calls)
        self.assertEqual(result.usage['output_tokens'], 8192)
        self.assertEqual(result.usage['input_tokens'], 12)

    def test_no_output_budget_left_prevents_retry(self):
        fn = Mock(return_value=self.partial())
        result = request_single_action(fn, LLMRequest('s', 'u', metadata={'max_transport_output_tokens': 8192}))
        self.assertEqual(fn.call_count, 1)
        self.assertFalse(result.tool_calls)
        self.assertEqual(result.usage['tool_retries'], 0)

    def test_retry_is_capped_and_both_generations_are_charged(self):
        good = LLMResponse('', 'openai', 'glm-5.2', tool_calls=(LLMToolCall('rest', {}),),
                           usage={'output_tokens': 3, 'input_tokens': 15})
        fn = Mock(side_effect=[self.partial(), good])
        result = request_single_action(fn, LLMRequest('s', 'u', metadata={'max_transport_output_tokens': 8200}))
        self.assertEqual(fn.call_args.args[0].metadata['max_output_tokens_override'], 8)
        self.assertEqual(result.usage['output_tokens'], 8195)
        self.assertEqual(result.usage['input_tokens'], 27)
        self.assertEqual(result.usage['api_calls'], 2)
        self.assertEqual(result.tool_calls, good.tool_calls)
        self.assertFalse(result.usage['rejected_tool_calls'][0]['executed'])
