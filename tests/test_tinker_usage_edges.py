import sys
from pathlib import Path
import pytest
sys.path[:0] = [str(Path(__file__).resolve().parents[1] / p) for p in ('src', 'tests')]
from test_tinker_action_mechanism import Samples, run

@pytest.mark.parametrize('prior', [False, True])
@pytest.mark.parametrize('failed', [
    {'api_calls': 0, 'output_tokens': 0, 'unknown_usage_attempts': 0},
    {'api_calls': 1, 'output_tokens': 0, 'unknown_usage_attempts': 1},
    {'api_calls': 2, 'output_tokens': 7, 'unknown_usage_attempts': 1}])
def test_staged_action_failures_preserve_zero_known_and_unknown_usage(prior, failed):
    class Failure(Samples):
        def __call__(self, *args, **kwargs):
            if prior and not self.requests:
                return super().__call__(*args, **kwargs)
            self.last_usage = dict(failed)
            raise RuntimeError('Fixture failure')
    result = run(Failure(('{"name":"rest', 13, 'length')))
    assert not result.tool_calls
    assert result.usage['api_calls'] == int(prior) + failed['api_calls']
    assert result.usage['output_tokens'] == 13 * int(prior) + failed['output_tokens']
    assert result.usage['unknown_usage_attempts'] == failed['unknown_usage_attempts']


def test_failed_staged_request_checkpoints_draft_and_resumes_remaining_allowance():
    import copy
    from unittest.mock import patch
    import llm
    from test_action_usage_resume import engine
    saved = []
    prefix = '{"name":"rest","arguments":{"reason":"'
    class Failure(Samples):
        def __call__(self, *args, **kwargs):
            if not self.requests:
                return super().__call__(*args, **kwargs)
            self.last_usage = {'api_calls': 1, 'output_tokens': 0, 'unknown_usage_attempts': 1}
            raise RuntimeError('Fixture sampling outage')
    first = Failure((prefix, 13, 'length'))
    with patch.object(llm, 'make_tinker_caller', return_value=first):
        request_fn = llm.make_tinker_request_fn('test-model', max_output_tokens=512)
    with pytest.raises(RuntimeError, match='Fixture sampling outage'):
        engine(request_fn, calls=3, turns=1,
            callback=lambda state, memory: saved.append((copy.deepcopy(state), memory))).run()
    checkpoint = saved[-1]
    assert checkpoint[0]['budget']['api_calls_used'] == 2
    assert checkpoint[0]['budget']['tokens_used'] == 13
    draft = checkpoint[0]['engine_state']['state']['transport_drafts']['Agent_1']
    assert draft['executed'] is False
    second = Samples(('{"name":"rest","arguments":{"reason":"Wait"}}', 3, 'stop'))
    with patch.object(llm, 'make_tinker_caller', return_value=second):
        request_fn = llm.make_tinker_request_fn('test-model', max_output_tokens=512)
    result = engine(request_fn, calls=3, turns=1, saved=checkpoint).run()
    assert len(second.requests) == 1
    # The observation's spent budget changed. Revalidate selection against the
    # new observation while retaining the prior text as an unexecuted draft.
    assert not second.requests[0][2].get('continuation_tokens')
    assert prefix in second.requests[0][1]
    assert second.requests[0][2]['max_output_tokens_override'] == 87
    assert result['budget']['api_calls_used'] == 3
    assert result['budget']['tokens_used'] == 16
    assert sum(row['executed'] for row in result['action_transport_log']) == 1
