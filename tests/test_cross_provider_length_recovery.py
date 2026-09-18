"""Provider-neutral overlimit recovery must precede any tool execution."""
import json
import sys
from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from action_transport import request_single_action
from llm import LLMRequest, LLMResponse, LLMToolCall


def request(limit=8000, **metadata):
    return LLMRequest('Original contest instructions.', 'Original solving observation.',
        tools=({'name': 'work', 'parameters': {'type': 'object', 'properties': {
            'problem_id': {'type': 'string', 'enum': ['q', 'source']},
            'content': {'type': 'string'}}, 'required': ['problem_id', 'content'],
            'additionalProperties': False}},), tool_choice='required',
        metadata={'task_id': 'q', 'action_argument_limits': {'work': {'content': limit}}, **metadata})


def response(text, provider='openai', **usage):
    return LLMResponse('', provider, 'fixture', tool_calls=(
        LLMToolCall('work', {'problem_id': 'q', 'content': text}, 'call'),),
        usage={'api_calls': 1, 'output_tokens': 10, 'finish_reason': 'stop', **usage})


@pytest.mark.parametrize('provider', ['openai', 'perplexity', 'openagents', 'vectorengine'])
def test_complete_native_overlimit_call_is_rewritten_before_it_can_execute(provider):
    fn = Mock(side_effect=[response('x' * 8001, provider), response('Final answer: 42', provider)])
    result = request_single_action(fn, request())
    assert len(fn.call_args_list) == 2
    assert result.tool_calls[0].arguments['content'] == 'Final answer: 42'
    assert result.usage['api_calls'] == 2 and result.usage['output_tokens'] == 20
    assert '8001' in fn.call_args.args[0].user_prompt
    assert '6000' in fn.call_args.args[0].user_prompt


def test_native_repeated_overlimit_is_not_returned_as_executable():
    fn = Mock(return_value=response('x' * 8001))
    result = request_single_action(fn, request())
    assert not result.tool_calls
    assert result.usage['tool_error']
    assert result.usage['api_calls'] == 2


def test_native_overlimit_at_api_cap_does_not_start_repair():
    fn = Mock(return_value=response('x' * 8001))
    result = request_single_action(fn, request(max_transport_attempts=1))
    assert not result.tool_calls and fn.call_count == 1


def test_mixed_source_packet_still_enforces_the_selected_draft_limit():
    req = request(action_argument_limits_by_task={
        'q': {'work': {'content': 8000}}, 'source': {}})
    req = replace(req, metadata={**req.metadata, 'action_argument_limits': {}})
    fn = Mock(side_effect=[response('x' * 8001), response('Final answer: 42')])
    result = request_single_action(fn, req)
    assert fn.call_count == 2 and result.tool_calls[0].arguments['content'] == 'Final answer: 42'


def test_pdf_overlong_evidence_retry_has_measured_feedback(tmp_path):
    import pymupdf
    from llm import LLMAttachment
    from evaluation.pdf_paging import paged_judge
    path = tmp_path / 'task.pdf'
    with pymupdf.open() as pdf:
        for _ in range(3):
            pdf.new_page()
        pdf.save(path)
    seen = []
    def judge(req):
        seen.append(req)
        if req.metadata['pdf_paging_stage'] == 'final':
            return LLMResponse('{"score":1}', 'fixture', 'fixture', usage={'output_tokens': 2})
        if req.metadata['attempt'] == 2:
            assert '3201' in req.user_prompt and '2400' in req.user_prompt
            text = 'Page evidence.'
        else:
            text = 'x' * 3201
        return LLMResponse(json.dumps(dict(evidence=text, unreadable_pages=[])), 'fixture', 'fixture',
                           usage={'output_tokens': 5, 'finish_reason': 'stop'})
    result = paged_judge(judge, tmp_path/'cache')(LLMRequest('Rubric.', 'Grade.',
        attachments=(LLMAttachment(path, 'application/pdf'),)))
    assert result.text == '{"score":1}'
    assert len(seen) == 5


@pytest.mark.parametrize('mutation', ['problem_id', 'name', 'extra_field', 'missing_field'])
def test_length_repair_cannot_change_fixed_action_or_metadata(mutation):
    good = response('Final answer: 42')
    call = good.tool_calls[0]
    if mutation == 'problem_id':
        call = replace(call, arguments={**call.arguments, 'problem_id': 'source'})
    elif mutation == 'name':
        call = replace(call, name='submit')
    elif mutation == 'extra_field':
        call = replace(call, arguments={**call.arguments, 'answer': '42'})
    else:
        call = replace(call, arguments={'content': 'Final answer: 42'})
    fn = Mock(side_effect=[response('x' * 8001), replace(good, tool_calls=(call,))])
    result = request_single_action(fn, request())
    assert not result.tool_calls and 'fixed arguments' in result.usage['tool_error']
    assert result.usage['api_calls'] == 2


@pytest.mark.parametrize('remaining', [10, 11, 20])
def test_length_recovery_respects_output_budget(remaining):
    fn = Mock(side_effect=[response('x' * 8001), response('42', output_tokens=remaining-10)])
    result = request_single_action(fn, request(max_transport_output_tokens=remaining))
    if remaining == 10:
        assert fn.call_count == 1 and not result.tool_calls
    else:
        assert fn.call_args.args[0].metadata['max_output_tokens_override'] == remaining-10
        assert result.tool_calls
    assert result.usage['output_tokens'] == remaining


def test_length_recovery_provider_exception_preserves_both_calls():
    error = RuntimeError('Provider failed')
    error.usage = {'api_calls': 1, 'output_tokens': 3}
    fn = Mock(side_effect=[response('x' * 8001), error])
    with pytest.raises(RuntimeError) as caught:
        request_single_action(fn, request())
    assert caught.value.usage['api_calls'] == 2
    assert caught.value.usage['output_tokens'] == 13


def test_source_in_mixed_packet_does_not_inherit_draft_limit():
    req = request(action_argument_limits_by_task={'q': {'work': {'content': 8000}}, 'source': {}})
    call = LLMToolCall('work', {'problem_id': 'source', 'content': 'source' * 2000})
    fn = Mock(return_value=replace(response('unused'), tool_calls=(call,)))
    result = request_single_action(fn, req)
    assert result.tool_calls == (call,) and fn.call_count == 1


@pytest.mark.parametrize('cap,name,field', [(8000,'work','content'), (60000,'work','content'),
    (60000,'render_pdf','content'), (8000,'submit','answer')])
@pytest.mark.parametrize('offset', [0, 1])
def test_answer_and_artifact_boundaries_across_shared_actions(cap, name, field, offset):
    tool = {'name': name, 'parameters': {'type':'object', 'properties': {field:{'type':'string'}},
             'required':[field], 'additionalProperties':False}}
    req = LLMRequest('Contest.', 'Task.', tools=(tool,), tool_choice='required',
                     metadata={'action_argument_limits':{name:{field:cap}}})
    call = LLMToolCall(name, {field:'x'*(cap+offset)})
    fn = Mock(return_value=LLMResponse('', 'mock','mock', tool_calls=(call,), usage={'output_tokens': 10}))
    result = request_single_action(fn, req)
    assert bool(result.tool_calls) == (offset == 0)
    assert fn.call_count == 1 + offset


def test_tinker_reads_target_specific_limit_and_does_not_restart_managed_recovery():
    from test_tinker_action_mechanism import Samples, run
    sampler = Samples(('work"', 2, 'stop'), ('q"', 2, 'stop'), ('x'*8001, 10,'stop'),
                      ('Final answer: 42', 5,'stop'))
    sampler.supports_prefix = True
    req = request(action_argument_limits_by_task={'q':{'work':{'content':8000}}, 'source':{}})
    req = replace(req, metadata={**req.metadata, 'action_argument_limits':{}})
    result = run(sampler, req)
    assert result.tool_calls[0].arguments['content'] == 'Final answer: 42'
    assert result.usage['api_calls'] == len(sampler.requests) == 4


@pytest.mark.parametrize('provider', ['openai','perplexity','openagents','vectorengine',
                                     'anthropic','gemini','deepseek','openai_compatible'])
def test_real_provider_payload_adapters_share_length_recovery_without_network(provider):
    import os
    import llm
    from env_config import RUN_API_KEY_ENV
    def payload(text):
        args = {'problem_id':'q','content':text}
        arguments = json.dumps(args)
        if provider == 'anthropic':
            return {'stop_reason':'tool_use', 'content':[{'type':'tool_use','name':'work','input':args}],
                    'usage':{'output_tokens':10,'input_tokens':20}}
        if provider == 'gemini':
            return {'candidates':[{'finishReason':'STOP','content':{'parts':[
                {'functionCall':{'name':'work','args':args}}]}}],
                'usageMetadata':{'candidatesTokenCount':10,'promptTokenCount':20}}
        if provider in {'openagents','vectorengine','deepseek','openai_compatible'}:
            return {'choices':[{'finish_reason':'tool_calls','message':{'content':None,
                'tool_calls':[{'id':'c1','type':'function','function':{'name':'work','arguments':arguments}}]}}],
                'usage':{'completion_tokens':10,'prompt_tokens':20}}
        return {'output':[{'type':'function_call','name':'work','arguments':arguments}],
                'usage':{'output_tokens':10,'input_tokens':20}}
    rows = [payload('x'*8001),payload('Final answer: 42')]
    responses = []
    for row in rows:
        reply = Mock(ok=True, usage=None, output_text='')
        reply.json.return_value = reply.model_dump.return_value = row
        responses.append(reply)
    with patch.dict(os.environ, {RUN_API_KEY_ENV[provider]:'offline'}, clear=True), \
            patch('openai.OpenAI') as sdk, patch('requests.post') as post:
        create = (sdk.return_value.chat.completions.create if provider in {'openagents','vectorengine'}
                  else sdk.return_value.responses.create)
        create.side_effect = responses
        post.side_effect = responses
        fn = llm.resolve_request_fn(provider, model='fixture', max_output_tokens=4096)
        result = request_single_action(fn, request(max_transport_output_tokens=65536))
        http = provider in {'perplexity','anthropic','gemini','deepseek','openai_compatible'}
        sent = post.call_args_list if http else create.call_args_list
        assert len(sent) == 2
        for sent_call in sent:
            body = sent_call.kwargs['json'] if http else sent_call.kwargs
            cap = (body['generationConfig']['maxOutputTokens'] if provider == 'gemini'
                   else body.get('max_tokens',body.get('max_output_tokens')))
            assert cap == 4096
    assert result.tool_calls[0].arguments['content'] == 'Final answer: 42'
    assert result.usage['api_calls'] == 2 and result.usage['output_tokens'] == 20


def test_tinker_oversized_structured_payload_retries_value_without_index_error():
    from test_tinker_action_mechanism import Samples, run
    tool = {'name':'prepare', 'parameters':{'type':'object', 'properties':{
        'notes':{'type':'array','items':{'type':'string'}}}, 'required':['notes'],
        'additionalProperties':False}}
    req = LLMRequest('Contest.', 'Task.', tools=(tool,), tool_choice='required',
        metadata={'action_payload_limits':{'prepare':60}, 'max_transport_attempts':3})
    sampler = Samples(('prepare"',2,'stop'), (json.dumps(['x'*100])+'}',10,'stop'),
                      (json.dumps(['Concise evidence.'])+'}',5,'stop'))
    sampler.supports_prefix = True
    result = run(sampler, req)
    assert result.tool_calls[0].arguments == {'notes':['Concise evidence.']}
    assert result.usage['api_calls'] == 3


def test_native_structured_payload_repair_preserves_rows_ids_and_numbers():
    tool = {'name':'prepare','parameters':{'type':'object','properties':{
        'problem_ids':{'type':'array','items':{'type':'string'}},
        'notes':{'type':'array','items':{'type':'string'}}, 'number':{'type':'integer'}},
        'required':['problem_ids','notes','number'], 'additionalProperties':False}}
    req = LLMRequest('Contest.','Task.',tools=(tool,),tool_choice='required',
        metadata={'action_payload_limits':{'prepare':100}})
    original={'problem_ids':['q'], 'notes':['x'*110], 'number':42}
    good={**original, 'notes':['Evidence.']}
    for replacement, expected in [(good,True), ({**good,'problem_ids':['other']},False),
                                  ({**good,'notes':[]},False), ({**good,'number':41},False)]:
        responses=[LLMResponse('','mock','mock',tool_calls=(LLMToolCall('prepare',args),),
                              usage={'output_tokens':10}) for args in (original,replacement)]
        result=request_single_action(Mock(side_effect=responses),req)
        assert bool(result.tool_calls) is expected


@pytest.mark.parametrize('budget_key,budget,expected_calls',[
    ('max_transport_attempts',2,2), ('max_transport_output_tokens',5,1)])
def test_pdf_recovery_shares_one_budget_across_page_batches(tmp_path,budget_key,budget,expected_calls):
    import pymupdf
    from llm import LLMAttachment
    from evaluation.pdf_paging import paged_judge,PagedJudgeError
    path=tmp_path/'task.pdf'
    with pymupdf.open() as pdf:
        for _ in range(3):pdf.new_page()
        pdf.save(path)
    seen=[]
    def judge(req):
        seen.append(req)
        assert req.metadata['pdf_paging_stage']=='evidence'
        value='x'*3201 if len(seen)==1 else 'Page facts.'
        return LLMResponse(json.dumps(dict(evidence=value,unreadable_pages=[])),
                           'fixture','fixture',usage={'api_calls':1,'output_tokens':5})
    req=LLMRequest('Rubric.','Grade.',attachments=(LLMAttachment(path,'application/pdf'),),
                   metadata={budget_key:budget})
    with pytest.raises(PagedJudgeError,match='budget exhausted') as caught:
        paged_judge(judge,tmp_path/'cache')(req)
    assert len(seen)==caught.value.usage['api_calls']==expected_calls
    assert caught.value.usage['output_tokens']==5*expected_calls


def test_native_provider_budget_overrun_is_charged_but_not_executed():
    fn=Mock(return_value=response('42',api_calls=3,output_tokens=50))
    result=request_single_action(fn,request(max_transport_attempts=2,max_transport_output_tokens=40))
    assert not result.tool_calls and 'exceeded' in result.usage['tool_error']
    assert result.usage['api_calls']==3 and result.usage['output_tokens']==50


def test_tinker_structured_repair_cannot_drop_rows():
    from test_tinker_action_mechanism import Samples,run
    tool={'name':'prepare','parameters':{'type':'object','properties':{
        'notes':{'type':'array','items':{'type':'string'}}},'required':['notes'],'additionalProperties':False}}
    req=LLMRequest('Rules.','Task.',tools=(tool,),tool_choice='required',
                   metadata={'action_payload_limits':{'prepare':60},'max_transport_attempts':3})
    sampler=Samples(('prepare"',2,'stop'),(json.dumps(['x'*100,'Second row.'])+'}',10,'stop'),('["Only one row."]}',2,'stop'))
    sampler.supports_prefix=True
    result=run(sampler,req)
    assert not result.tool_calls
    assert 'changed structured data' in result.usage['tool_error']


@pytest.mark.parametrize('variant', ['single_agent','decentralized','centralized','vallina_otc','otc'])
def test_full_engine_recovers_then_saves_once_in_each_baseline(variant):
    from test_work_content_limits import setup
    from contest_engine import _AgentTurn, _ContestEngine
    manifest, config, _, _ = setup(variant)
    texts = ['x'*8001, 'Essential reasoning.\nFinal answer: 42']
    seen = []
    def provider(req):
        seen.append(req)
        return LLMResponse('', 'fixture', 'fixture', tool_calls=(
            LLMToolCall('work', {'content':texts[len(seen)-1]}),),
            usage={'api_calls':1,'output_tokens':10,'finish_reason':'stop'})
    engine = _ContestEngine(manifest, lambda *_:'Use the supplied task.', config,
                             action_request_fn=provider, action_transport='native')
    engine.session.select_task('q1')
    turn = _AgentTurn('Agent_1')
    assert engine._prepare_agent(turn)
    turn.think_completed = True
    engine._build_agent_prompts(turn)
    assert engine._request_action(turn)
    assert engine.session.active_task.versions == []
    engine._apply_agent_action(turn)
    versions = engine.session.active_task.versions
    assert len(seen) == 2 and len(versions) == 1
    assert versions[0].content == texts[1]
    assert engine.transport_api_calls == 2
    assert engine.session.budget.tokens_used == 20


def test_tinker_structured_length_repair_survives_checkpoint_without_restarting():
    from test_tinker_action_mechanism import Samples, run
    tool = {'name':'prepare','parameters':{'type':'object','properties':{
        'notes':{'type':'array','items':{'type':'string'}}},'required':['notes'],'additionalProperties':False}}
    req = LLMRequest('Rules.','Task.',tools=(tool,),tool_choice='required',metadata={
        'session_id':'session','agent':'Agent_1','task_id':'q',
        'action_payload_limits':{'prepare':60},'max_transport_attempts':2})
    first = Samples(('prepare"',2,'stop'), (json.dumps(['x'*100])+'}',10,'stop'))
    first.supports_prefix = True
    pending = run(first, req)
    assert not pending.tool_calls
    draft = json.loads(json.dumps(pending.usage['unexecuted_action_draft']))
    second = Samples(('prepare"',2,'stop'), ('["Evidence."]}',5,'stop'))
    second.supports_prefix = True
    result = run(second, replace(req,metadata={**req.metadata,'unexecuted_action_draft':draft}))
    assert result.tool_calls[0].arguments == {'notes':['Evidence.']}
    assert 'ACTION METADATA LENGTH REPAIR' in second.requests[1][0]
    assert '100' in second.requests[1][1] or '115' in second.requests[1][1]
