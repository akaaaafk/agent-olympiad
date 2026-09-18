"""Public providers use canonical tools, isolated credentials and full PDF bounds."""
import argparse
import base64
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
import llm
import env_config
import public_providers
from contest_run_identity import build_run_identity
from contest_manifest import ContestManifest, ManifestTask
from contest_config import ContestRunConfig
import run_competition_batch as batch

TOOLS = ({'type': 'function', 'name': 'rest', 'description': 'Wait',
          'parameters': {'type': 'object', 'properties': {}, 'additionalProperties': False}},)


def response(provider, *, finish=None, two=False):
    if provider == 'anthropic':
        return {'content': [{'type': 'text', 'text': 'Visible answer'},
                            *[{'type': 'tool_use', 'id': f'call_{i}', 'name': 'rest', 'input': {}}
                              for i in range(2 if two else 1)]],
                'stop_reason': finish or 'tool_use', 'usage': {'input_tokens': 12, 'output_tokens': 5}}
    return {'candidates': [{'finishReason': finish or 'STOP', 'content': {'parts': [
                {'text': 'Hidden thinking', 'thought': True}, {'text': 'Visible answer'},
                *[{'functionCall': {'name': 'rest', 'args': {}, 'id': f'call_{i}'}}
                  for i in range(2 if two else 1)]]}}],
            'usageMetadata': {'promptTokenCount': 12, 'candidatesTokenCount': 5, 'thoughtsTokenCount': 3}}


class PublicProviderTests(unittest.TestCase):
    def factory(self, provider):
        return llm.resolve_request_fn(provider, 'fixture-model', max_output_tokens=500)

    def test_native_tools_and_usage(self):
        for provider in ('anthropic', 'gemini'):
            with self.subTest(provider=provider), patch.dict(os.environ,
                {env_config.RUN_API_KEY_ENV[provider]: 'dedicated-key'}, clear=True), patch.object(
                    public_providers.requests, 'post', return_value=Mock(ok=True, json=lambda: response(provider))) as post:
                result = self.factory(provider)(llm.LLMRequest('system', 'question', tools=TOOLS,
                    tool_choice='required', parallel_tool_calls=False,
                    metadata={'max_output_tokens_override': 250}))
            self.assertEqual(result.text, 'Visible answer')
            self.assertEqual(result.tool_calls[0].name, 'rest')
            self.assertEqual(result.tool_calls[0].arguments, {})
            self.assertEqual(result.usage['input_tokens'], 12)
            self.assertEqual(result.usage['output_tokens'], 8 if provider == 'gemini' else 5)
            self.assertEqual(result.usage['max_output_tokens'], 250)
            payload = post.call_args.kwargs['json']
            self.assertNotIn('dedicated-key', post.call_args.args[0])
            if provider == 'anthropic':
                self.assertEqual(payload['tools'][0]['input_schema'], TOOLS[0]['parameters'])
                self.assertEqual(payload['tool_choice'], {'type': 'any', 'disable_parallel_tool_use': True})
            else:
                self.assertEqual(payload['toolConfig']['functionCallingConfig']['mode'], 'ANY')
                self.assertEqual(payload['tools'][0]['functionDeclarations'][0]['parametersJsonSchema'],
                                 TOOLS[0]['parameters'])

    def test_multi_calls_are_preserved_for_atomic_dispatch_rejection(self):
        for provider in ('anthropic', 'gemini'):
            with patch.dict(os.environ, {env_config.RUN_API_KEY_ENV[provider]: 'key'}, clear=True), patch.object(
                public_providers.requests, 'post', return_value=Mock(ok=True, json=lambda: response(provider, two=True))):
                result = self.factory(provider)(llm.LLMRequest('', '', tools=TOOLS, tool_choice='required'))
            self.assertEqual(len(result.tool_calls), 2)

    def test_incomplete_and_refused_output_cannot_execute_tools(self):
        for provider, reason in [('anthropic', 'max_tokens'), ('anthropic', 'refusal'),
                                  ('gemini', 'MAX_TOKENS'), ('gemini', 'SAFETY')]:
            with patch.dict(os.environ, {env_config.RUN_API_KEY_ENV[provider]: 'key'}, clear=True), patch.object(
                public_providers.requests, 'post', return_value=Mock(ok=True, json=lambda: response(provider, finish=reason))):
                result = self.factory(provider)(llm.LLMRequest('', '', tools=TOOLS))
            self.assertFalse(result.text)
            self.assertFalse(result.tool_calls)
            self.assertIn('tool_error', result.usage)

    def test_each_provider_requires_own_key(self):
        for provider in env_config.PUBLIC_PROFILE_PROVIDERS:
            with patch.dict(os.environ, {'OPENAI_API_KEY': 'other-service-key'}, clear=True):
                with self.assertRaisesRegex(ValueError, env_config.RUN_API_KEY_ENV[provider]):
                    self.factory(provider)

    def test_http_errors_do_not_echo_key_or_response_body(self):
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'secret-value'}, clear=True), patch.object(
            public_providers.requests, 'post', return_value=Mock(ok=False, status_code=401, text='secret-value')):
            with self.assertRaisesRegex(RuntimeError, 'HTTP 401') as caught:
                self.factory('anthropic')(llm.LLMRequest('', ''))
        self.assertNotIn('secret-value', str(caught.exception))

    def test_pdf_page_range_in_native_payload_and_text_adapter(self):
        import pymupdf
        from pypdf import PdfReader
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'packet.pdf'
            with pymupdf.open() as doc:
                for text in ['VISIBLE TASK', 'SECRET ANSWER']:
                    doc.new_page().insert_text((60, 60), text)
                doc.save(path)
            req = llm.LLMRequest('sys', 'question', attachments=(
                llm.LLMAttachment(path, 'application/pdf', 'agent_visible', 1, 1),))
            for provider in ('anthropic', 'gemini'):
                with patch.dict(os.environ, {env_config.RUN_API_KEY_ENV[provider]: 'key'}, clear=True), patch.object(
                    public_providers.requests, 'post', return_value=Mock(ok=True, json=lambda: response(provider))) as post:
                    self.factory(provider)(req)
                payload = post.call_args.kwargs['json']
                encoded = (payload['messages'][0]['content'][1]['source']['data'] if provider == 'anthropic'
                           else payload['contents'][0]['parts'][1]['inlineData']['data'])
                pages = PdfReader(io.BytesIO(base64.b64decode(encoded))).pages
                self.assertEqual(len(pages), 1)
                self.assertIn('VISIBLE TASK', pages[0].extract_text())
                self.assertNotIn('SECRET ANSWER', pages[0].extract_text())
            for provider in ('deepseek', 'openai_compatible'):
                sink = Mock(return_value={'choices': [{'finish_reason': 'stop', 'message': {'content': 'ok'}}]})
                with patch.dict(os.environ, {env_config.RUN_API_KEY_ENV[provider]: 'key'}, clear=True), patch.object(
                    public_providers, '_post', sink):
                    self.factory(provider)(req)
                converted = sink.call_args.args[3]['messages'][1]['content']
                self.assertIsInstance(converted, str)
                self.assertIn('VISIBLE TASK', converted)
                self.assertNotIn('SECRET ANSWER', converted)
            with self.assertRaisesRegex(ValueError, 'Judge-only'):
                llm.LLMRequest('', '', purpose='contest_action', attachments=(
                    llm.LLMAttachment(path, 'application/pdf', 'judge_only'),))

    def test_compatible_chat_uses_plain_text_and_canonical_tool_schema(self):
        reply = {
            'choices': [{'finish_reason': 'tool_calls', 'message': {'content': None, 'tool_calls': [
                {'id': 'c', 'function': {'name': 'rest', 'arguments': '{}'}}]}}],
            'usage': {'prompt_tokens': 20, 'completion_tokens': 4}}
        for provider in ('deepseek', 'openai_compatible'):
            with patch.dict(os.environ, {env_config.RUN_API_KEY_ENV[provider]: 'key'}, clear=True), patch.object(
                public_providers, '_post', return_value=reply) as post:
                result = self.factory(provider)(llm.LLMRequest('sys', 'user', tools=TOOLS,
                    metadata={'max_output_tokens_override': 2000}))
            payload = post.call_args.args[3]
            self.assertEqual(payload['messages'][1]['content'], 'user')
            self.assertEqual(payload['max_tokens'], 500)
            self.assertEqual(result.tool_calls[0].name, 'rest')

    def test_common_cli_key_and_endpoint_are_consumed_and_provider_bound(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--provider', default='gemini')
        env_config.add_run_credentials(parser)
        args = parser.parse_args(['--api-key-env', 'MY_KEY', '--base-url', 'https://fixture.test/v1beta'])
        with patch.dict(os.environ, {'MY_KEY': 'fixture-secret'}, clear=True):
            env_config.consume_run_credentials(args)
            self.assertEqual(os.environ['GEMINI_API_KEY'], 'fixture-secret')
            self.assertEqual(env_config.provider_config('gemini')['base_url'], 'https://fixture.test/v1beta')
            self.assertNotIn('api_key_env', vars(args))
            self.assertNotIn('base_url', vars(args))
            self.assertNotIn('OPENAI_API_KEY', os.environ)

    def test_identity_includes_endpoint_but_never_key(self):
        task = ManifestTask('q', 'q', None, 'Question', 'quiz', 1, False, {})
        manifest = ContestManifest('fixture', 'quiz', (task,))
        config = ContestRunConfig('single_agent', 1, 2)
        with tempfile.TemporaryDirectory() as empty_sources, patch.dict(os.environ,
            {'OPENAI_COMPATIBLE_API_KEY': 'secret-not-in-identity',
             'OPENAI_COMPATIBLE_BASE_URL': 'https://one.test/v1'}, clear=True):
            def identity():
                return build_run_identity(manifest, config, execution={'provider': 'openai_compatible',
                    'model': 'fixture'}, evaluation={'provider': 'openai_compatible'}, source_root=Path(empty_sources))
            before = identity()
            os.environ['OPENAI_COMPATIBLE_BASE_URL'] = 'https://two.test/v1'
            after = identity()
            self.assertNotEqual(before['fingerprint'], after['fingerprint'])
            self.assertNotIn('secret-not-in-identity', json.dumps(before))

    def test_new_providers_reach_normal_solver_factory(self):
        for provider in env_config.PUBLIC_PROFILE_PROVIDERS:
            self.assertIn(provider, batch.PROVIDERS)
            self.assertEqual(batch._judge_api_key_name(provider), env_config.RUN_API_KEY_ENV[provider])
            with patch.object(batch, 'resolve_request_fn', return_value=lambda request:
                              llm.LLMResponse('answer', provider, 'fixture')) as factory:
                self.assertEqual(batch._make_live_query(provider, 'fixture')('sys', 'user'), 'answer')
                self.assertEqual(factory.call_args.kwargs['provider'], provider)

    def test_new_providers_prepare_existing_artifact_path_without_model_calls(self):
        import pymupdf
        from otc_artifact_pipeline import prepare_artifact_run
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {}, clear=True):
            path = Path(folder) / 'task.pdf'
            with pymupdf.open() as doc:
                doc.new_page().insert_text((60, 60), 'Prepare a reasoned legal argument.')
                doc.save(path)
            for provider in env_config.PUBLIC_PROFILE_PROVIDERS:
                prepared = prepare_artifact_run(competition='vis_moot', task_pdf=path,
                    output=Path(folder) / provider, model='fixture-model', provider=provider,
                    system_variant='single_agent', max_turns=2)
                settings = prepared['identity']['settings']
                self.assertEqual(settings['execution']['provider'], provider)
                self.assertEqual(settings['evaluation']['provider'], provider)
                self.assertEqual(settings['execution']['action_transport'], 'native')
                self.assertIn('base_url', settings['execution'])

    def test_check_provider_calls_only_text_and_one_tool_probe(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location('provider_check', ROOT / 'scripts/check_provider.py')
        probe = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(probe)
        sink = Mock(side_effect=[llm.LLMResponse('OK', 'gemini', 'fixture'),
             llm.LLMResponse('', 'gemini', 'fixture', tool_calls=(
                 llm.LLMToolCall('provider_probe', {'value': 7}),))])
        with patch.object(llm, 'resolve_request_fn', return_value=sink), patch.object(
                env_config, 'load_repo_dotenv'), patch('sys.stdout', new_callable=io.StringIO) as stdout:
            probe.main(['--provider', 'gemini', '--model', 'fixture'])
        self.assertEqual(sink.call_count, 2)
        self.assertEqual(json.loads(stdout.getvalue())['passed'], ['authenticated_text', 'native_tools'])

    def test_exhausted_transport_budget_fails_before_http(self):
        for provider in env_config.PUBLIC_PROFILE_PROVIDERS:
            with patch.dict(os.environ, {env_config.RUN_API_KEY_ENV[provider]: 'key'}, clear=True), patch.object(
                    public_providers.requests, 'post') as post:
                with self.assertRaisesRegex(ValueError, 'budget exhausted'):
                    self.factory(provider)(llm.LLMRequest('', '', metadata={'max_transport_attempts': 0}))
                post.assert_not_called()


if __name__ == '__main__':
    unittest.main()
