"""Gateway routing, credentials, payloads, accounting, and resume isolation."""
import base64
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tests")]
import llm
import run_competition_batch as cli
from env_config import load_repo_dotenv
from contest_config import ContestRunConfig
from contest_run_identity import build_run_identity
from test_contest_settings import example


class OpenAgentsTests(unittest.TestCase):
    def test_gateway_credential_is_redacted_from_saved_errors(self):
        self.assertNotIn('gateway-test-key', cli._sanitize_exception(ValueError('failed gateway-test-key')))

    def setUp(self):
        env = patch.dict(os.environ, {"OPENAGENTS_API_KEY": "gateway-test-key"}, clear=True)
        env.start()
        self.addCleanup(env.stop)
        sdk = patch("openai.OpenAI")
        self.sdk = sdk.start()
        self.addCleanup(sdk.stop)
        self.create = self.sdk.return_value.chat.completions.create
        self.reply = {"choices": [{"finish_reason": "tool_calls", "message": {
            "content": None, "tool_calls": [{"id": "c1", "type": "function", "function": {
                "name": "rest", "arguments": "{}"}}]}}],
            "usage": {"prompt_tokens": 13, "completion_tokens": 7, "total_tokens": 20}}
        self.create.return_value.model_dump.return_value = self.reply

    def test_native_tools_usage_and_sampling_reach_gateway(self):
        request = llm.LLMRequest("system", "user", tools=({"type": "function",
            "name": "rest", "parameters": {"type": "object", "properties": {}}},),
            tool_choice="required", parallel_tool_calls=False)
        response = llm.resolve_request_fn("openagents", max_output_tokens=123, temperature=0.13)(request)
        self.assertEqual(self.sdk.call_args.kwargs["base_url"], "https://api-gateway.openagents.org/v1")
        self.assertEqual(self.sdk.call_args.kwargs["api_key"], "gateway-test-key")
        payload = self.create.call_args.kwargs
        self.assertEqual(payload["model"], "glm-5.2")
        self.assertEqual(payload["temperature"], 0.13)
        self.assertEqual(payload["max_tokens"], 123)
        self.assertEqual(payload["tools"][0]["function"]["name"], "rest")
        self.assertFalse(payload["parallel_tool_calls"])
        self.assertEqual(payload["tool_choice"], "required")
        self.assertEqual(response.tool_calls, (llm.LLMToolCall("rest", {}, "c1"),))
        self.assertEqual(response.usage["input_tokens"], 13)
        self.assertEqual(response.usage["output_tokens"], 7)

    def test_plain_text_think_does_not_use_perplexity(self):
        self.reply["choices"][0]["message"] = {"content": "Think carefully."}
        with patch.object(cli, "make_perplexity_caller", side_effect=AssertionError("wrong provider")):
            call = cli._make_live_query("openagents", "other-model", max_output_tokens=77, temperature=0.1)
            self.assertEqual(call("s", "u"), "Think carefully.")
        self.assertEqual(self.create.call_args.kwargs["model"], "other-model")

    def test_deepseek_deliberation_disables_thinking_and_uses_short_budget(self):
        self.reply["choices"][0]["message"] = {"content": "NEXT ACTION: work"}
        call = cli._make_live_query(
            "openagents", "deepseek-v4-pro", max_output_tokens=8192, temperature=0.2,
        )
        self.assertEqual(call("system", "user"), "NEXT ACTION: work")
        payload = self.create.call_args.kwargs
        self.assertEqual(payload["max_tokens"], 2048)
        self.assertEqual(payload["extra_body"], {"thinking": {"type": "disabled"}})

    def test_deepseek_contest_action_disables_duplicate_thinking(self):
        request = llm.LLMRequest(
            "system", "user", purpose="contest_action",
            tools=({"type": "function", "name": "rest",
                    "parameters": {"type": "object", "properties": {}}},),
            tool_choice="required",
        )
        llm.resolve_request_fn(
            "openagents", model="deepseek-v4-pro", max_output_tokens=8192,
        )(request)
        self.assertEqual(
            self.create.call_args.kwargs["extra_body"],
            {"thinking": {"type": "disabled"}},
        )

    def test_truncated_deliberation_is_bounded_scratch_not_a_fatal_action(self):
        self.reply["choices"][0] = {
            "finish_reason": "length",
            "message": {"content": "partial private scratch", "tool_calls": []},
        }
        response = llm.resolve_request_fn(
            "openagents", model="deepseek-v4-pro", max_output_tokens=8192,
        )(llm.LLMRequest(
            "system", "user", purpose="contest_deliberation",
            metadata={"disable_reasoning": True, "max_output_tokens_override": 2048},
        ))
        self.assertEqual(response.text, "partial private scratch")
        self.assertTrue(response.usage["deliberation_truncated"])
        self.assertNotIn("tool_error", response.usage)

    def test_missing_gateway_key_never_uses_other_provider_key(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "unrelated"}, clear=True):
            with self.assertRaisesRegex(ValueError, "OPENAGENTS_API_KEY"):
                llm.resolve_request_fn("openagents")
        self.sdk.assert_not_called()

    def test_unknown_solver_provider_cannot_fall_back_to_perplexity(self):
        with patch.object(cli, "make_perplexity_caller") as wrong:
            with self.assertRaisesRegex(ValueError, "Unsupported solver provider"):
                cli._make_live_query("unknown", "model")
            wrong.assert_not_called()

    def test_legacy_local_gateway_key_is_not_used_for_openagents(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            path.write_text("OPENAI_API_KEY=local-gateway\nOPENAI_BASE_URL=https://api-gateway.openagents.org/v1\n")
            with patch.dict(os.environ, {"OPENAI_API_KEY": "inherited-other"}, clear=True):
                load_repo_dotenv(path)
                self.assertEqual(os.environ["OPENAI_API_KEY"], "inherited-other")
                self.assertNotIn("OPENAGENTS_API_KEY", os.environ)
                self.assertNotIn("OPENAGENTS_BASE_URL", os.environ)
                with self.assertRaisesRegex(ValueError, "OPENAGENTS_API_KEY"):
                    llm.resolve_request_fn("openagents")
            with patch.dict(os.environ, {"OPENAGENTS_API_KEY": "explicit"}, clear=True):
                load_repo_dotenv(path)
                self.assertEqual(os.environ["OPENAGENTS_API_KEY"], "explicit")
                self.assertNotIn("OPENAGENTS_BASE_URL", os.environ)

    def test_invalid_or_partial_tool_calls_are_not_executed(self):
        caller = llm.resolve_request_fn("openagents")
        self.reply["choices"][0]["message"]["tool_calls"][0]["function"]["arguments"] = "[]"
        response = caller(llm.LLMRequest("s", "u"))
        self.assertEqual(response.tool_calls, ())
        self.assertIn('no action executed', response.usage['tool_error'])
        self.assertEqual(response.usage['output_tokens'], 7)
        self.assertEqual(response.usage['api_calls'], 1)
        self.reply["choices"][0]["finish_reason"] = "length"
        response = caller(llm.LLMRequest("s", "u"))
        self.assertEqual(response.tool_calls, ())
        self.assertEqual(response.usage["finish_reason"], "length")
        self.assertEqual(response.usage["output_tokens"], 7)

    def test_pdf_page_selection_is_rendered_as_images(self):
        from pypdf import PdfWriter
        from PIL import Image
        with tempfile.TemporaryDirectory() as directory:
            pdf = Path(directory) / "two.pdf"
            writer = PdfWriter()
            writer.add_blank_page(width=100, height=100)
            writer.add_blank_page(width=200, height=100)
            writer.write(pdf)
            llm.resolve_request_fn("openagents")(llm.LLMRequest("s", "u", attachments=(
                llm.LLMAttachment(pdf, "application/pdf", page_start=2, page_end=2),)))
            content = self.create.call_args.kwargs["messages"][1]["content"]
            self.assertEqual(len(content), 2)
            image = Image.open(io.BytesIO(base64.b64decode(content[1]["image_url"]["url"].split(",")[1])))
            self.assertGreater(image.width, image.height)

    def test_endpoint_changes_invalidate_identity_but_keys_do_not(self):
        config = ContestRunConfig("single_agent", 1, 2)
        def identity():
            return build_run_identity(example(), config, execution={"provider": "openagents"},
                                      evaluation={"provider": "openagents"})
        first = identity()
        with patch.dict(os.environ, {"OPENAGENTS_API_KEY": "rotated"}):
            self.assertEqual(first, identity())
        with patch.dict(os.environ, {"OPENAGENTS_BASE_URL": "https://different.example/v1"}):
            self.assertNotEqual(first, identity())
        self.assertNotIn("gateway-test-key", json.dumps(first))


if __name__ == "__main__":
    unittest.main()
