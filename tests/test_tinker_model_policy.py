"""Per-model templates and exact-token truncation regression matrix."""
import sys
import re
from pathlib import Path
from unittest.mock import Mock,patch
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import llm
from tinker_model_policy import model_policy,make_text_renderer,context_limit,stop_sequences
from test_tinker_action_mechanism import Samples

MODELS=['Qwen/Qwen3.6-35B-A3B','deepseek-ai/DeepSeek-V3.1',
        'moonshotai/Kimi-K2.6','meta-llama/Llama-3.1-8B-Instruct']

class TemplateTokenizer:
    """Deterministic special-token fixture, not a model tokenizer claim."""
    name_or_path='offline-template-fixture'
    def __init__(self):self.special={}
    def encode(self,text,**kwargs):
        result=[]
        for part in re.split(r'(<[^<>]+>)',text):
            if part.startswith('<') and part.endswith('>'):
                result.append(self.special.setdefault(part,1_000_000+len(self.special)))
            else:result.extend(map(ord,part))
        return result
    def decode(self,tokens,**kwargs):
        reverse={v:k for k,v in self.special.items()}
        return ''.join(reverse[t] if t in reverse else chr(t) for t in tokens)


@pytest.mark.parametrize('model,renderer',list(zip(MODELS,[None,'deepseekv3','kimi_k26_disable_thinking','llama3'])))
def test_exact_model_template_policy(model,renderer):
    policy=model_policy(model)
    assert policy.renderer==renderer
    assert policy.disable_thinking_kwarg==(renderer is None)
    assert policy.supports_prefix
    assert model_policy(model+':checkpoint').renderer==renderer


@pytest.mark.parametrize('model',MODELS[1:])
def test_official_renderers_preserve_roles_and_use_distinct_headers(model):
    tokenizer=TemplateTokenizer()
    renderer=make_text_renderer(model_policy(model),tokenizer)
    from tinker_vision import generation_input
    prompt=generation_input(renderer,tokenizer,'RULES','TASK',())
    text=tokenizer.decode(prompt.to_ints())
    assert 'RULES' in text and 'TASK' in text
    marker={'deepseek-ai/DeepSeek-V3.1':'<｜User｜>',
            'moonshotai/Kimi-K2.6':'<|im_user|>',
            'meta-llama/Llama-3.1-8B-Instruct':'<|start_header_id|>'}[model]
    assert marker in text
    stops=stop_sequences(tokenizer,renderer,['"'])
    assert stops[0]=='"' and len(stops)>1


@pytest.mark.parametrize('model',MODELS)
def test_generation_and_judge_truncation_resume_exact_tokens(model):
    sampler=Samples(('first ',6,'length'),('second',6,'stop'))
    with patch.object(llm,'make_tinker_caller',return_value=sampler):
        fn=llm.make_tinker_request_fn(model,max_output_tokens=10)
    response=fn(llm.LLMRequest('RULES','TASK',purpose='evaluation'))
    assert response.text=='first second'
    assert sampler.requests[0][:2]==sampler.requests[1][:2]
    assert sampler.requests[1][2]['continuation_tokens']==list(map(ord,'first '))
    assert response.usage['output_tokens']==12
    assert response.usage['api_calls']==2


@pytest.mark.parametrize('model',MODELS)
def test_truncated_answer_never_becomes_success_when_budget_exhausted(model):
    sampler=Samples(('partial',7,'length'))
    with patch.object(llm,'make_tinker_caller',return_value=sampler):
        fn=llm.make_tinker_request_fn(model)
    response=fn(llm.LLMRequest('','',metadata={'max_transport_attempts':1,'max_transport_output_tokens':7}))
    assert response.text=='' and response.usage['tool_error']
    assert response.usage['incomplete_text']=='partial'
    assert len(sampler.requests)==1


def test_unknown_model_does_not_inherit_qwen_options_or_context():
    policy=model_policy('other/model')
    assert not policy.disable_thinking_kwarg and not policy.supports_prefix
    assert policy.context_window is None
    tokenizer=Mock(model_max_length=10**30)
    assert context_limit(policy,tokenizer) is None
    tokenizer.model_max_length=32768
    assert context_limit(policy,tokenizer)==32768
