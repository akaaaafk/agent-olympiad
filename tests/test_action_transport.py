"""Atomic rejection and lossless correction of single-action responses."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from action_transport import request_single_action
from llm import (LLMRequest, LLMResponse, LLMToolCall,
                 make_openai_responses_caller, make_perplexity_responses_caller)


class SingleActionTransportTests(unittest.TestCase):
    def setUp(self):
        # Minimized from Agent_6, turn 1 of memory_activation_20260913_035256.
        self.calls = (
            LLMToolCall("remember", {"problem_id": "arml_local_2009:3",
                "content": "Unfinished expected winnings recurrence; check S2."}, "note-call"),
            LLMToolCall("inspect_problem", {"problem_id": "arml_local_2009:3",
                "focus": "Check the statement."}, "inspect-call"),
        )
        self.request = LLMRequest("Exactly one function per response.", "Current state.",
            purpose="contest_action", tools=(
                {"type": "function", "name": "remember", "parameters": {"type": "object"}},
                {"type": "function", "name": "inspect_problem", "parameters": {"type": "object"}},
            ), tool_choice="required")

    def response(self, calls):
        return LLMResponse("", "mock", "transport", tool_calls=calls,
                           usage={"api_calls": 1, "output_tokens": 7})

    def test_repeated_mixed_batch_is_fully_rejected(self):
        fn = Mock(return_value=self.response(self.calls))
        result = request_single_action(fn, self.request)
        self.assertEqual(result.tool_calls, ())
        self.assertEqual(fn.call_count, 2)
        self.assertEqual(result.usage["api_calls"], 2)
        self.assertEqual(result.usage["output_tokens"], 14)
        self.assertEqual(len(result.usage["rejected_tool_calls"]), 4)
        self.assertTrue(all(not c["executed"] for c in result.usage["rejected_tool_calls"]))

    def test_retry_keeps_rejected_intent_available_without_selecting_for_model(self):
        fn = Mock(side_effect=[self.response(self.calls), self.response(self.calls[:1])])
        result = request_single_action(fn, self.request)
        correction = fn.call_args.args[0]
        # The stateless retry must show what was rejected, not silently discard
        # the note's contents and ask the model to reconstruct its previous plan.
        self.assertIn(json.dumps([{"name": c.name, "arguments": c.arguments}
                                  for c in self.calls], ensure_ascii=False), correction.user_prompt)
        self.assertIn("No action from that response executed", correction.user_prompt)
        self.assertEqual(correction.tools, self.request.tools)
        self.assertEqual(correction.tool_choice, "required")
        self.assertEqual(result.tool_calls, self.calls[:1])
        self.assertEqual(result.usage["api_calls"], 2)
        self.assertEqual(result.usage["output_tokens"], 14)
        self.assertEqual(result.usage["tool_retries"], 1)

    def test_api_budget_one_does_not_retry_or_execute_batch(self):
        from dataclasses import replace
        fn = Mock(return_value=self.response(self.calls))
        result = request_single_action(fn, replace(self.request,
            metadata={"max_transport_attempts": 1}))
        self.assertEqual(fn.call_count, 1)
        self.assertEqual(result.tool_calls, ())
        self.assertEqual(result.usage["api_calls"], 1)

    def test_length_exhaustion_before_tool_call_retries_with_more_output_budget(self):
        exhausted = LLMResponse(
            "", "openai", "glm-5.2", tool_calls=(),
            usage={"api_calls": 1, "output_tokens": 8192,
                   "finish_reason": "length", "max_output_tokens": 8192,
                   "reasoning_chars": 12000},
        )
        success = self.response(self.calls[:1])
        fn = Mock(side_effect=[exhausted, success])

        result = request_single_action(fn, self.request)

        self.assertEqual(result.tool_calls, self.calls[:1])
        self.assertEqual(fn.call_count, 2)
        retry = fn.call_args.args[0]
        self.assertEqual(retry.metadata["max_output_tokens_override"], 16384)
        self.assertIn("reasoning output hit its token limit", retry.user_prompt)
        self.assertEqual(result.usage["api_calls"], 2)
        self.assertEqual(result.usage["output_tokens"], 8199)
        self.assertEqual(result.usage["tool_retries"], 1)

    def test_perplexity_action_instructions_use_system_channel(self):
        response = Mock(ok=True)
        response.json.return_value = {"output": [{"type": "function_call",
            "name": "remember", "arguments": json.dumps(self.calls[0].arguments)}],
            "usage": {"output_tokens": 7}}
        with patch.dict("os.environ", {"PERPLEXITY_API_KEY": "test-key"}), \
                patch("requests.post", return_value=response) as post:
            request_single_action(make_perplexity_responses_caller("test-model"), self.request)
        payload = post.call_args.kwargs["json"]
        self.assertEqual(payload.get("instructions"), self.request.system_prompt)
        self.assertEqual(payload["input"][0]["content"][0]["text"], self.request.user_prompt)

    def test_perplexity_honors_transport_output_override(self):
        from dataclasses import replace
        response = Mock(ok=True)
        response.json.return_value = {'output': [], 'usage': {'output_tokens': 2}}
        with patch.dict('os.environ', {'PERPLEXITY_API_KEY': 'test-key'}), \
                patch('requests.post', return_value=response) as post:
            result = make_perplexity_responses_caller('test-model')(replace(
                self.request, metadata={'max_output_tokens_override': 3}))
        self.assertEqual(post.call_args.kwargs['json']['max_output_tokens'], 3)
        self.assertEqual(result.usage['max_output_tokens'], 3)

    def test_glm_compatible_caller_reports_length_and_honors_action_override(self):
        from dataclasses import replace
        message = Mock(content=None, tool_calls=[])
        message.model_dump.return_value = {"reasoning_content": "hidden reasoning"}
        usage = Mock()
        usage.model_dump.return_value = {"completion_tokens": 16384}
        response = Mock(usage=usage)
        response.choices = [Mock(message=message, finish_reason="length")]
        response.model_dump.return_value = {"choices": [{"finish_reason": "length",
            "message": {"content": None, "tool_calls": [], "reasoning_content": "hidden reasoning"}}],
            "usage": {"completion_tokens": 16384}}
        with patch.dict("os.environ", {
            "OPENAI_API_KEY": "test-key",
            "OPENAI_BASE_URL": "https://gateway.test/v1",
        }, clear=True), patch("openai.OpenAI") as client:
            client.return_value.chat.completions.create.return_value = response
            caller = make_openai_responses_caller(
                "glm-5.2", max_output_tokens=8192, temperature=0.2,
            )
            result = caller(replace(self.request, metadata={
                "disable_reasoning": True,
                "max_output_tokens_override": 16384,
            }))
        sent = client.return_value.chat.completions.create.call_args.kwargs
        self.assertEqual(sent["max_tokens"], 16384)
        self.assertEqual(sent["temperature"], 0.2)
        self.assertEqual(sent["reasoning_effort"], "medium")
        self.assertEqual(sent["extra_body"], {"thinking": {"type": "disabled"}})
        self.assertEqual(result.usage["finish_reason"], "length")
        self.assertEqual(result.usage["reasoning_chars"], len("hidden reasoning"))
        self.assertEqual(result.usage["max_output_tokens"], 16384)

    def test_live_deliberation_disables_glm_hidden_reasoning(self):
        from run_competition_batch import _make_live_query

        captured = []

        def request(req):
            captured.append(req)
            return LLMResponse("brief private thought", "openai", "glm-5.2")

        with patch("run_competition_batch.resolve_request_fn", return_value=request):
            query = _make_live_query("openai", "glm-5.2")
            self.assertEqual(query("system", "user"), "brief private thought")

        self.assertEqual(len(captured), 1)
        self.assertEqual(captured[0].purpose, "contest_deliberation")
        self.assertIs(captured[0].metadata["disable_reasoning"], True)
        self.assertEqual(captured[0].metadata["max_output_tokens_override"], 2048)

    def test_native_single_action_constraint_reaches_provider_on_retry(self):
        response = Mock(ok=True)
        response.json.return_value = {"output": [{"type": "function_call",
            "name": c.name, "arguments": json.dumps(c.arguments)} for c in self.calls],
            "usage": {"output_tokens": 7}}
        response.model_dump.return_value = response.json.return_value
        response.output_text = ""
        response.usage = None
        for provider in ("perplexity", "openai"):
            with self.subTest(provider=provider), patch.dict("os.environ", {
                "PERPLEXITY_API_KEY": "test-key", "OPENAI_API_KEY": "test-key",
            }), patch("requests.post", return_value=response) as post, \
                    patch("openai.OpenAI") as client:
                create = client.return_value.responses.create
                create.return_value = response
                factory = (make_perplexity_responses_caller if provider == "perplexity"
                           else make_openai_responses_caller)
                result = request_single_action(factory("test-model"), self.request)
                sent = post.call_args_list if provider == "perplexity" else create.call_args_list
                self.assertEqual(len(sent), 2)
                for call in sent:
                    payload = call.kwargs["json"] if provider == "perplexity" else call.kwargs
                    self.assertIs(payload.get("parallel_tool_calls"), False)
                    self.assertEqual(payload["tool_choice"], "required")
                    self.assertEqual(payload["tools"], list(self.request.tools))
                self.assertEqual(result.tool_calls, ())


if __name__ == "__main__":
    unittest.main()
