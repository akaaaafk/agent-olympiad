"""Repair an invalid raw argument without spending its allowance reselecting it."""
import sys
from pathlib import Path

import pytest

sys.path[:0] = [str(Path(__file__).resolve().parents[1] / p) for p in ('src', 'tests')]
from test_tinker_action_mechanism import Samples, run, request


def test_overlong_body_rewrites_the_same_field_within_existing_attempt_budget():
    # The live OTC pattern uses selection + metadata + body, leaving two calls.
    # Re-selecting and serializing metadata again leaves no call for correction.
    sample = Samples(('work","', 2, 'stop'),
                     ('A derivation much too long. Final answer: 42', 20, 'stop'),
                     ('Final answer: 42', 5, 'stop'))
    sample.supports_prefix = True
    response = run(sample, request(max_transport_attempts=3,
                                  action_argument_limits={'work': {'content': 20}}))
    assert len(response.tool_calls) == 1
    assert response.tool_calls[0].arguments['content'] == 'Final answer: 42'
    assert [r['stage'] for r in response.usage['sampling_trace']] == ['select', 'body', 'body']
    assert response.usage['api_calls'] == 3
    assert response.usage['output_tokens'] == 27
    assert not sample.requests[-1][2].get('continuation_tokens')
    assert '20' in sample.requests[-1][0] + sample.requests[-1][1]


def test_repeated_invalid_body_still_exhausts_budget_without_clipping_or_execution():
    body = 'Repeated excessive derivation. Final answer: 42'
    sample = Samples(('work","', 2, 'stop'), (body, 20, 'stop'), (body, 20, 'stop'))
    sample.supports_prefix = True
    response = run(sample, request(max_transport_attempts=3,
                                  action_argument_limits={'work': {'content': 20}}))
    assert not response.tool_calls
    assert len(sample.requests) == response.usage['api_calls'] == 3
    assert body in response.usage['unexecuted_action_draft']['text']
    assert response.usage['output_tokens'] == 42
