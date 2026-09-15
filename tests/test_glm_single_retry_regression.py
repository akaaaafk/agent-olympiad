"""Offline regressions for the GLM ARML single-agent failure shapes."""
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock
sys.path[:0] = [str(Path(__file__).resolve().parents[1] / 'src'), str(Path(__file__).parent)]
from test_live_failure_regressions import state
from contest_session import ContestSession
from contest_actions import _apply_action
from action_transport import request_single_action
from llm import LLMRequest, LLMResponse, LLMToolCall


def test_explicit_first_work_without_cursor_is_not_cross_task():
    m, s, memory, cfg = state('single_agent')
    s = ContestSession(s.tasks, s.budget)
    assert s.active_task is None
    target = s.tasks[-1].task_id
    _apply_action(action='work', arguments={'problem_id': target, 'content': 'Final answer: 43'},
                  agent='Agent_1', manifest=m, session=s, memory=memory, config=cfg,
                  strategic_policy=None, task_action_executor=Mock())
    assert s.task(target).versions[-1].content == 'Final answer: 43'


def test_length_with_partial_tool_retries_instead_of_executing_empty_arguments():
    partial = LLMResponse('', 'openai', 'glm-5.2', tool_calls=(LLMToolCall('work', {}),),
                          usage={'finish_reason': 'length', 'output_tokens': 8192})
    good = LLMResponse('', 'openai', 'glm-5.2', tool_calls=(LLMToolCall('work',
                       {'problem_id': 'q1', 'content': 'Final answer: 43'}),),
                       usage={'output_tokens': 20})
    fn = Mock(side_effect=[partial, good])
    result = request_single_action(fn, LLMRequest('One action', 'Solve'))
    assert fn.call_count == 2
    assert result.tool_calls == good.tool_calls
    assert result.usage['output_tokens'] == 8212


def test_repeated_partial_length_calls_never_execute():
    partial = LLMResponse('', 'openai', 'glm-5.2', tool_calls=(LLMToolCall('work', {}),),
                          usage={'finish_reason': 'length', 'output_tokens': 8192})
    result = request_single_action(Mock(return_value=partial), LLMRequest('One action', 'Solve'))
    assert not result.tool_calls
    assert result.usage['tool_error']


def load_tests(loader, tests, pattern):
    return unittest.TestSuite(unittest.FunctionTestCase(value)
                              for name, value in globals().items() if name.startswith('test_'))
