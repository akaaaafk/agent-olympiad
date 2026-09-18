"""Real failed-output regression and bounded, atomic staged action generation."""
import json
from pathlib import Path
import unittest
import sys
from unittest.mock import patch
from dataclasses import replace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import llm
from action_transport import request_single_action

TOOLS = (
    {'name': 'submit_code', 'parameters': {'type': 'object', 'properties': {
        'code': {'type': 'string'}, 'problem_id': {'type': 'string', 'enum': ['q']}},
        'required': ['code'], 'additionalProperties': False}},
    {'name': 'work', 'parameters': {'type': 'object', 'properties': {
        'content': {'type': 'string'}}, 'required': ['content'], 'additionalProperties': False}},
    {'name': 'rest', 'parameters': {'type': 'object', 'properties': {}, 'additionalProperties': False}},
)


class Samples:
    supports_sampling_metadata = True
    supports_continuation = True

    def __init__(self, *rows):
        self.rows = iter(rows)
        self.requests = []

    def __call__(self, system, user, **kwargs):
        self.requests.append((system, user, kwargs))
        text, used, finish = next(self.rows)
        self.last_sample_tokens = [ord(c) for c in text]
        self.last_usage = {'input_tokens': 100, 'output_tokens': used, 'api_calls': 1,
                           'finish_reason': finish, 'max_output_tokens': kwargs['max_output_tokens_override']}
        return text

    def decode_completion_tokens(self, tokens):
        return ''.join(chr(t) for t in tokens)


def request(**metadata):
    return llm.LLMRequest('Contest rules.', 'Solve q.', tools=TOOLS, tool_choice='required',
        metadata={'agent': 'Agent_1', 'session_id': 's', 'task_id': 'q',
                  'max_transport_attempts': 4, 'max_transport_output_tokens': 20000, **metadata})


def run(sampler, req=None):
    with patch.object(llm, 'make_tinker_caller', return_value=sampler):
        fn = llm.make_tinker_request_fn('test-model', max_output_tokens=4096)
        return request_single_action(fn, req or request())


class StagedActionTests(unittest.TestCase):
    def test_typed_metadata_continues_across_turns_without_executing_partial_array(self):
        tools = ({'name': 'check_cases', 'parameters': {'type': 'object', 'properties': {
            'inputs': {'type': 'array', 'items': {'type': 'string'}}},
            'required': ['inputs'], 'additionalProperties': False}},)
        req = replace(request(max_transport_attempts=2), tools=tools)
        first = Samples(('check_cases"', 2, 'stop'), ('["first\\n', 10, 'length'))
        first.supports_prefix = True
        response = run(first, req)
        self.assertFalse(response.tool_calls)
        draft = json.loads(json.dumps(response.usage['unexecuted_action_draft']))
        second = Samples(('check_cases"', 2, 'stop'), ('line", "second"]}', 10, 'stop'))
        second.supports_prefix = True
        final = run(second, replace(req, metadata={**req.metadata, 'unexecuted_action_draft': draft}))
        self.assertEqual(final.tool_calls[0].arguments, {'inputs': ['first\nline', 'second']})
        self.assertEqual(second.requests[1][2]['continuation_tokens'], [ord(c) for c in '["first\\n'])
        self.assertEqual(first.requests[1][:2], second.requests[1][:2])

    def test_optional_metadata_omission_and_scoped_value_validation(self):
        sampler = Samples(('submit_code"', 2, 'stop'), ('forbidden"', 2, 'stop'),
                          ('__OMIT__"', 2, 'stop'), ('int main(){}', 10, 'stop'))
        sampler.supports_prefix = True
        response = run(sampler)
        self.assertEqual(response.tool_calls[0].arguments, {'code': 'int main(){}'})
        self.assertIn('must be one of', response.usage['sampling_trace'][1]['error'])

    def test_answer_is_raw_and_never_forced_into_short_metadata_json(self):
        tools = ({'name': 'submit', 'parameters': {'type': 'object', 'properties': {
            'answer': {'type': 'string'}}, 'required': ['answer'], 'additionalProperties': False}},)
        sampler = Samples(('submit","', 2, 'stop'), ('Source with "quotes"\nand literal newlines.', 10, 'stop'))
        sampler.supports_prefix = True
        result = run(sampler, replace(request(), tools=tools))
        self.assertEqual(result.tool_calls[0].arguments['answer'], 'Source with "quotes"\nand literal newlines.')
        self.assertEqual([x['stage'] for x in result.usage['sampling_trace']], ['select', 'body'])

    def test_multiple_long_fields_preserve_completed_fields_across_turns(self):
        tools = ({'name': 'prepare_report', 'parameters': {'type': 'object', 'properties': {
            'problem_id': {'type': 'string', 'enum': ['q']},
            'theory': {'type': 'string'}, 'evidence': {'type': 'string'}},
            'required': ['problem_id', 'theory', 'evidence'], 'additionalProperties': False}},)
        req = replace(request(max_transport_attempts=3), tools=tools)
        first = Samples(('prepare_report"', 2, 'stop'), ('q","', 8, 'stop'),
                        ('Completed theory "literal quotes".', 10, 'stop'))
        first.supports_prefix = True
        response = run(first, req)
        self.assertFalse(response.tool_calls)
        draft = json.loads(json.dumps(response.usage['unexecuted_action_draft']))
        second = Samples(('prepare_report"', 2, 'stop'), ('q","', 8, 'stop'),
                         ('Evidence line 1\nEvidence line 2', 10, 'stop'))
        second.supports_prefix = True
        final = run(second, replace(req, metadata={**req.metadata, 'unexecuted_action_draft': draft}))
        self.assertEqual(final.tool_calls[0].arguments, {'problem_id': 'q',
            'theory': 'Completed theory "literal quotes".', 'evidence': 'Evidence line 1\nEvidence line 2'})
        self.assertIn("'evidence'", second.requests[-1][0])
        self.assertEqual(final.usage['output_tokens'], 20)

    def test_prefilled_name_stop_may_include_comma_in_same_token(self):
        sampler = Samples(('submit_code","', 3, 'stop'),
                          ('q","', 7, 'stop'), ('int main(){}\n', 8, 'stop'))
        sampler.supports_prefix = True
        result = run(sampler)
        self.assertEqual(result.tool_calls[0].name, 'submit_code')
        self.assertEqual(result.tool_calls[0].arguments, {'problem_id': 'q', 'code': 'int main(){}\n'})
        self.assertEqual(sampler.requests[0][2]['assistant_prefix'], '{"name":"')
        self.assertEqual(sampler.requests[0][2]['stop'], ['"'])
        self.assertEqual(sampler.requests[1][2]['assistant_prefix'], '{"problem_id":"')
        self.assertEqual(sampler.requests[1][2]['stop'], ['"'])
        self.assertEqual(result.usage['output_tokens'], 18)

    def test_raw_code_needs_no_json_escaping(self):
        code = '#include <iostream>\nint main(){std::cout << "a\\nb";}\n'
        sampler = Samples(('{"name":"submit_code","arguments":{},"body_argument":"code"}', 25, 'stop'),
                          (code, 30, 'stop'))
        result = run(sampler)
        self.assertEqual(result.tool_calls[0].arguments, {'code': code})
        self.assertEqual(result.usage['api_calls'], 2)
        self.assertEqual(result.usage['output_tokens'], 55)

    def test_length_continues_exact_tokens_then_executes_one_complete_call(self):
        sampler = Samples(('{"name":"submit_code","arguments":{},"body_argument":"code"}', 25, 'stop'),
                          ('int main(){\n', 4096, 'length'), ('return 0;\n}\n', 15, 'stop'))
        result = run(sampler)
        self.assertEqual(result.tool_calls[0].arguments['code'], 'int main(){\nreturn 0;\n}\n')
        self.assertEqual(sampler.requests[2][2]['continuation_tokens'], [ord(c) for c in 'int main(){\n'])
        self.assertEqual(sampler.requests[1][:2], sampler.requests[2][:2])
        self.assertEqual(result.usage['output_tokens'], 4136)
        self.assertEqual(len(result.usage['sampling_trace']), 3)

    def test_budget_exhaustion_saves_unexecuted_draft_without_outer_restart(self):
        sampler = Samples(('{"name":"submit_code","arguments":{},"body_argument":"code"}', 25, 'stop'),
                          ('int main(){', 10, 'length'))
        result = run(sampler, request(max_transport_output_tokens=35))
        self.assertFalse(result.tool_calls)
        self.assertEqual(len(sampler.requests), 2)
        self.assertEqual(result.usage['output_tokens'], 35)
        self.assertIn('int main(){', result.usage['unexecuted_action_draft']['text'])
        self.assertFalse(result.usage['unexecuted_action_draft']['executed'])

    def test_next_turn_resumes_body_after_reselecting_same_authorized_action(self):
        header = '{"name":"submit_code","arguments":{},"body_argument":"code"}'
        first = run(Samples((header, 25, 'stop'), ('int main(){\n', 10, 'length')),
                    request(max_transport_attempts=2))
        draft = json.loads(json.dumps(first.usage['unexecuted_action_draft']))
        second = Samples((header, 25, 'stop'), ('return 0;\n}\n', 12, 'stop'))
        req = replace(request(unexecuted_action_draft=draft), user_prompt='Updated state; solve q.')
        final = run(second, req)
        self.assertEqual(final.tool_calls[0].arguments['code'], 'int main(){\nreturn 0;\n}\n')
        self.assertEqual(second.requests[1][2]['continuation_tokens'], [ord(c) for c in 'int main(){\n'])
        self.assertIn('Updated state', second.requests[0][1])

    def test_reselected_different_action_does_not_reuse_body_tokens(self):
        header = '{"name":"submit_code","arguments":{},"body_argument":"code"}'
        first = run(Samples((header, 25, 'stop'), ('int main(){\n', 10, 'length')),
                    request(max_transport_attempts=2))
        second = Samples(('{"name":"work","arguments":{},"body_argument":"content"}', 20, 'stop'),
                         ('Unfinished code; need to verify the recurrence.', 12, 'stop'))
        final = run(second, request(unexecuted_action_draft=first.usage['unexecuted_action_draft']))
        self.assertEqual(final.tool_calls[0].name, 'work')
        self.assertEqual(second.requests[1][2]['continuation_tokens'], [])

    def test_budget_after_selection_reports_incomplete_action(self):
        sampler = Samples(('{"name":"work","arguments":{},"body_argument":"content"}', 20, 'stop'))
        result = run(sampler, request(max_transport_attempts=1))
        self.assertFalse(result.tool_calls)
        self.assertIn('budget', result.usage['tool_error'].lower())

    def test_changed_current_schema_discards_continuation_tokens(self):
        header = '{"name":"submit_code","arguments":{},"body_argument":"code"}'
        first = run(Samples((header, 25, 'stop'), ('OLD_PREFIX', 10, 'length')),
                    request(max_transport_attempts=2))
        tools = json.loads(json.dumps(TOOLS))
        tools[0]['parameters']['properties']['problem_id']['enum'] = ['new_q']
        req = replace(request(unexecuted_action_draft=first.usage['unexecuted_action_draft']), tools=tuple(tools))
        second = Samples((header, 25, 'stop'), ('int main(){}', 12, 'stop'))
        final = run(second, req)
        self.assertEqual(final.tool_calls[0].arguments['code'], 'int main(){}')
        self.assertEqual(second.requests[1][2]['continuation_tokens'], [])

    def test_completed_rejected_body_does_not_keep_stale_pending_tokens(self):
        header = '{"name":"work","arguments":{},"body_argument":"content"}'
        first = run(Samples((header, 20, 'stop'), ('prefix', 10, 'length')),
                    request(max_transport_attempts=2))
        draft = first.usage['unexecuted_action_draft']
        second = Samples((header, 20, 'stop'), ('too long', 10, 'stop'))
        final = run(second, request(max_transport_attempts=2, unexecuted_action_draft=draft,
                                   action_argument_limits={'work': {'content': 2}}))
        self.assertFalse(final.tool_calls)
        self.assertNotIn('pending_body', final.usage['unexecuted_action_draft'])

    def test_real_failed_output_is_retained_for_selection_and_never_executed(self):
        fixture = json.loads((Path(__file__).parent / 'fixtures/tinker_failed_samples_20260917.json').read_text(encoding='utf8'))
        text = fixture['samples'][0]['text']
        draft = {'scope': {'agent': 'Agent_1', 'session_id': 's', 'task_id': 'q'}, 'text': text, 'executed': False}
        sampler = Samples(('{"name":"work","arguments":{},"body_argument":"content"}', 20, 'stop'),
                          ('Interval DP; still verifying the length-one base case.', 12, 'stop'))
        result = run(sampler, request(unexecuted_action_draft=draft))
        self.assertIn(text, sampler.requests[0][1])
        self.assertIn('unexecuted', sampler.requests[0][1].lower())
        self.assertEqual(len(result.tool_calls), 1)
        self.assertNotIn(text, result.tool_calls[0].arguments['content'])

    def test_foreign_agent_or_task_draft_is_not_visible(self):
        for changed in ({'agent': 'Agent_2'}, {'task_id': 'other'}, {'session_id': 'other'}):
            draft = {'scope': {'agent': 'Agent_1', 'session_id': 's', 'task_id': 'q', **changed},
                     'text': 'SECRET_DRAFT', 'executed': False}
            sampler = Samples(('{"name":"rest","arguments":{}}', 10, 'stop'))
            result = run(sampler, request(unexecuted_action_draft=draft))
            self.assertEqual(len(result.tool_calls), 1)
            self.assertNotIn('SECRET_DRAFT', str(sampler.requests))

    def test_unavailable_body_field_and_tool_never_reach_body_generation(self):
        for raw in ('{"name":"submit_code","arguments":{},"body_argument":"content"}',
                    '{"name":"forbidden","arguments":{},"body_argument":"code"}'):
            sampler = Samples((raw, 20, 'stop'))
            result = run(sampler, request(max_transport_attempts=1))
            self.assertFalse(result.tool_calls)
            self.assertEqual(len(sampler.requests), 1)

    def test_character_limit_is_checked_without_clipping_candidate(self):
        sampler = Samples(('{"name":"work","arguments":{},"body_argument":"content"}', 20, 'stop'),
                          ('Final answer: 12345', 15, 'stop'))
        result = run(sampler, request(max_transport_attempts=2, action_argument_limits={'work': {'content': 10}}))
        self.assertFalse(result.tool_calls)
        self.assertIn('10', result.usage['tool_error'])
        self.assertIn('Final answer: 12345', result.usage['unexecuted_action_draft']['text'])


class AtomicParsingTests(unittest.TestCase):
    def test_malformed_outer_json_does_not_execute_an_inner_call(self):
        for text in ('{"name":"work","arguments":{"content":"broken '+
                     '{"name":"rest","arguments":{}}',
                     '{"name":"rest"}\n{"name":"rest"}'):
            with self.assertRaises(ValueError):
                llm._coerce_emulated_tool_call(text)

    def test_real_malformed_json_reports_outer_error_instead_of_math_array(self):
        fixture = json.loads((Path(__file__).parent / 'fixtures/tinker_failed_samples_20260917.json').read_text(encoding='utf8'))
        with self.assertRaisesRegex(ValueError, 'JSON.*(?:char|column|line)'):
            llm._coerce_emulated_tool_call(fixture['samples'][1]['text'])

    def test_duplicate_names_are_not_last_wins(self):
        with self.assertRaises(ValueError):
            llm._coerce_emulated_tool_call('{"name":"work","name":"rest","arguments":{}}')
