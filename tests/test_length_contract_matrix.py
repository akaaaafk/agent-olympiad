"""Exercise every main/mini delivery contract through shared action transport."""
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from audit_length_contracts import cases
from argument_limits import violations
from action_transport import request_single_action
from llm import LLMRequest, LLMResponse, LLMToolCall
from work_content import action_argument_limits, action_argument_limits_by_task, validate_work_content

CASES=cases()


@pytest.mark.parametrize('row,manifest',CASES,ids=[r['dataset']+'/'+r['competition'] for r,_ in CASES])
@pytest.mark.parametrize('backend',['native','tinker'])
def test_actual_catalog_contracts_reject_or_repair_without_clipping(row,manifest,backend):
    cap=row['work_character_limit']
    text='x'*(cap+1 if cap else 9001)
    tool={'name':'work','parameters':{'type':'object','properties':{'content':{'type':'string'}},
          'required':['content'],'additionalProperties':False}}
    req=LLMRequest('Rules.','Task.',tools=(tool,),tool_choice='required',metadata={
        'task_id':'q','action_argument_limits':action_argument_limits(manifest),
        'action_argument_limits_by_task':action_argument_limits_by_task(manifest)})
    assert bool(violations('work',{'content':text},req.metadata)) == (cap is not None)
    if cap is not None:
        validate_work_content(manifest,'q',text[:-1])
        with pytest.raises(ValueError,match='character'):
            validate_work_content(manifest,'q',text)
    else:
        validate_work_content(manifest,'q',text)
    if backend=='native':
        replies=[LLMResponse('','fixture','fixture',tool_calls=(LLMToolCall('work',{'content':value}),),
                             usage={'output_tokens':10}) for value in (text,'Complete replacement.')]
        fn=Mock(side_effect=replies)
        result=request_single_action(fn,req)
    else:
        from test_tinker_action_mechanism import Samples,run
        sampler=Samples(('work"',2,'stop'),(text,10,'stop'),('Complete replacement.',5,'stop'))
        sampler.supports_prefix=True
        result=run(sampler,req)
    expected='Complete replacement.' if cap is not None else text
    assert result.tool_calls[0].arguments['content']==expected
    validate_work_content(manifest,'q',expected)
